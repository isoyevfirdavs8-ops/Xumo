
import uuid
from datetime import timedelta
import hashlib
from django.db import connection
from django.db import IntegrityError, transaction
from django.db.models import Q, Sum
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from apps.payments.models import ClickTransaction
from .models import Competition, TicketOrder, Ticket


PAYMENT_TIMEOUT_MINUTES = 15


def lock_ticket_checkout_key(key):
    """
    PostgreSQL transaction-scoped advisory lock.

    Bir xil idempotency_key bilan kelgan parallel
    checkoutlarni ketma-ket bajaradi.
    """
    digest = hashlib.sha256(
        f"competition-ticket:{key}".encode("utf-8")
    ).digest()

    lock_id = int.from_bytes(
        digest[:8],
        byteorder="big",
        signed=True,
    )

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT pg_advisory_xact_lock(%s)",
            [lock_id],
        )

def create_ticket_order(
    *,
    user,
    competition_id,
    full_name,
    phone_number,
    quantity,
    provider,
    idempotency_key,
):
    """
    Musobaqaga chipta buyurtmasini yaratadi.

    - Faqat faol va boshlanmagan musobaqalar.
    - 1 tadan 10 tagacha chipta.
    - Capacity nazorati.
    - PostgreSQL select_for_update.
    - Idempotency key orqali takroriy checkout nazorati.
    - 15 daqiqalik to'lov muddati.
    """

    if provider not in TicketOrder.Provider.values:
        raise ValidationError({
            "provider": "Click yoki Payme tanlang."
        })

    if not isinstance(quantity, int) or not 1 <= quantity <= 10:
        raise ValidationError({
            "quantity": "1 tadan 10 tagacha chipta tanlang."
        })

    try:
        key = uuid.UUID(str(idempotency_key))
    except (ValueError, TypeError, AttributeError):
        raise ValidationError({
            "idempotency_key": "UUID formatida bo'lishi kerak."
        })

    full_name = full_name.strip()
    phone_number = phone_number.strip()

    if not full_name:
        raise ValidationError({
            "full_name": "Ism va familiyani kiriting."
        })

    if not phone_number:
        raise ValidationError({
            "phone_number": "Telefon raqamini kiriting."
        })

    with transaction.atomic():
        lock_ticket_checkout_key(key)

        existing = (
            TicketOrder.objects
            .select_for_update()
            .filter(idempotency_key=key)
            .first()
        )

        if existing is not None:
            if (
                existing.user_id != user.pk
                or existing.competition_id != competition_id
                or existing.full_name != full_name
                or existing.phone_number != phone_number
                or existing.quantity != quantity
                or existing.provider != provider
            ):
                raise ValidationError({
                    "idempotency_key": (
                        "Bu kalit boshqa buyurtma uchun ishlatilgan."
                    )
                })

            return existing

        # Bir musobaqaga parallel checkoutlarni
        # ketma-ket bajarish uchun lock.
        competition = (
            Competition.objects
            .select_for_update()
            .filter(pk=competition_id)
            .first()
        )

        if competition is None:
            raise ValidationError({
                "competition_id": "Musobaqa topilmadi."
            })

        if not competition.is_active:
            raise ValidationError({
                "competition_id": "Musobaqa faol emas."
            })

        now = timezone.now()

        if competition.start_time <= now:
            raise ValidationError({
                "competition_id": (
                    "Musobaqa allaqachon boshlangan."
                )
            })

        # Paid va muddati tugamagan pending
        # buyurtmalar joy band qiladi.
        reserved = (
            TicketOrder.objects
            .filter(competition=competition)
            .filter(
                Q(status=TicketOrder.Status.PAID)
                | Q(
                    status=TicketOrder.Status.PENDING,
                    payment_expires_at__gt=now,
                )
                | Q(
                    status=TicketOrder.Status.PENDING,
                    payment_expires_at__isnull=True,
                )
            )
            .aggregate(total=Sum("quantity"))["total"] or 0
        )

        if reserved + quantity > competition.capacity:
            raise ValidationError({
                "quantity": (
                    "Yetarli bo'sh joy mavjud emas. "
                    f"Qolgan joylar: {max(competition.capacity - reserved, 0)}."
                )
            })

        unit_price = competition.price
        total_amount = unit_price * quantity

        try:
            order = TicketOrder.objects.create(
                user=user,
                competition=competition,
                full_name=full_name,
                phone_number=phone_number,
                quantity=quantity,
                unit_price=unit_price,
                total_amount=total_amount,
                provider=provider,
                status=TicketOrder.Status.PENDING,
                idempotency_key=key,
                payment_expires_at=(
                    now + timedelta(
                        minutes=PAYMENT_TIMEOUT_MINUTES
                    )
                ),
            )
        except IntegrityError:
            raise ValidationError({
                "idempotency_key": (
                    "Buyurtma boshqa so'rovda "
                    "yaratilmoqda. Qayta urinib ko'ring."
                )
            })

        return order


@transaction.atomic
def issue_tickets_for_paid_order(order):
    """
    PAID buyurtma uchun chiptalarni idempotent yaratadi.

    Himoyalar:
    - Atomic transaction
    - Order row-level lock
    - Takroriy chaqiruvda yangi chipta yaratilmaydi
    - Qisman yaratilgan chiptalar rad etiladi
    """
    locked_order = (
        TicketOrder.objects
        .select_for_update()
        .get(pk=order.pk)
    )

    if locked_order.status != TicketOrder.Status.PAID:
        raise ValidationError(
            "Faqat to'langan buyurtmaga chipta beriladi."
        )

    existing_tickets = list(
        Ticket.objects.filter(order=locked_order)
    )

    if len(existing_tickets) == locked_order.quantity:
        return existing_tickets

    if existing_tickets:
        raise ValidationError(
            "Buyurtmadagi chiptalar soni mos kelmayapti."
        )

    tickets = [
        Ticket(order=locked_order)
        for _ in range(locked_order.quantity)
    ]

    Ticket.objects.bulk_create(tickets)

    return list(
        Ticket.objects.filter(order=locked_order)
    )



def expire_ticket_order(order_id):
    """
    Muddati tugagan PENDING ticket orderni
    xavfsiz bekor qiladi.

    Click uchun:
    - faol PREPARED transaction mavjud bo'lsa,
      avtomatik cancellation bajarilmaydi;
    - transaction tarixi mavjud bo'lsa, provider
      reconciliation talab qilinadi;
    - hech qanday Click transaction bo'lmasa,
      expired order CANCELLED qilinishi mumkin.

    PAYME uchun:
    - provider holatini tekshirish integratsiyasi
      mavjud bo'lmagani sababli fail-closed.
    """
    with transaction.atomic():
        order = (
            TicketOrder.objects
            .select_for_update()
            .filter(pk=order_id)
            .first()
        )

        if order is None:
            return False

        if order.status != TicketOrder.Status.PENDING:
            return False

        if (
            order.payment_expires_at is None
            or order.payment_expires_at > timezone.now()
        ):
            return False

        if order.provider_transaction_id:
            return False

        if order.provider == TicketOrder.Provider.CLICK:
            has_click_transaction = (
                ClickTransaction.objects.filter(
                    category="competition",
                    order_id=str(order.pk),
                ).exists()
            )

            if has_click_transaction:
                return False

        elif order.provider == TicketOrder.Provider.PAYME:
            # PAYME transaction/reconciliation holati
            # hali tekshirilmagan.
            return False

        else:
            # Noma'lum provider.
            return False

        order.status = TicketOrder.Status.CANCELLED
        order.save(update_fields=["status"])

        return True
