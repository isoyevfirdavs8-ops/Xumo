
from django.db import transaction
from django.utils import timezone

from apps.competitions.models import TicketOrder
from apps.competitions.services import issue_tickets_for_paid_order

from apps.restaurant_orders.models import (
    RestaurantOrder,
    RestaurantPayment,
)

from apps.finance.models import RevenueEntry
from apps.finance.recording import record_successful_payment

from apps.payments.exceptions import (
    PaymentOrderUnavailable,
    PaymentTransactionConflict,
)


@transaction.atomic
def settle_restaurant_payment(
    *,
    order_id,
    provider,
    provider_transaction_id,
):
    """
    Restaurant buyurtmasi uchun tasdiqlangan
    provider to'lovini yakunlaydi.

    Xususiyatlar:
    - PostgreSQL row-level locking
    - ACID transaction
    - Idempotent settlement
    - Transaction ID conflict protection
    - RevenueEntry yozish
    """

    if not provider_transaction_id:
        raise PaymentTransactionConflict()

    provider_transaction_id = str(
        provider_transaction_id
    )

    order = (
        RestaurantOrder.objects
        .select_for_update(of=("self",))
        .select_related("user")
        .get(pk=order_id)
    )

    if order.provider != provider:
        raise PaymentTransactionConflict()

    payment = (
        RestaurantPayment.objects
        .select_for_update()
        .get(order_id=order.pk)
    )

    # Boshqa provider tranzaksiyasi bilan
    # to'lov bajarilishining oldini olish.
    if (
        payment.provider_transaction_id
        and payment.provider_transaction_id
        != provider_transaction_id
    ):
        raise PaymentTransactionConflict()

    # Idempotency:
    # bir xil transaction bilan qayta chaqirilsa,
    # daromad ikkinchi marta yozilmaydi.
    if order.status == RestaurantOrder.Status.PAID:
        if (
            payment.provider_transaction_id
            != provider_transaction_id
        ):
            raise PaymentTransactionConflict()

        return order

    if order.status != RestaurantOrder.Status.PENDING:
        raise PaymentOrderUnavailable()

    now = timezone.now()

    if order.expires_at <= now:
        raise PaymentOrderUnavailable()

    # Order holatini yangilash.
    order.status = RestaurantOrder.Status.PAID
    order.paid_at = now
    order.save(
        update_fields=[
            "status",
            "paid_at",
        ]
    )

    # Payment ma'lumotlarini saqlash.
    payment.provider_transaction_id = (
        provider_transaction_id
    )
    payment.provider_state = "succeeded"

    payment.save(
        update_fields=[
            "provider_transaction_id",
            "provider_state",
            "updated_at",
        ]
    )

    # Moliyaviy yozuvni yaratish.
    record_successful_payment(
        category=RevenueEntry.Category.RESTAURANT,
        source="restaurant_order",
        source_payment_id=str(order.pk),
        amount=order.total_amount,
        provider=provider,
        user=order.user,
        paid_at=now,
    )

    return order


@transaction.atomic
def settle_competition_payment(
    *,
    order_id,
    provider,
    provider_transaction_id,
):
    """
    Musobaqa chiptasi uchun to'lovni yakunlaydi.

    Xususiyatlar:
    - ACID transaction
    - Row-level locking
    - Provider validation
    - Idempotent settlement
    - Ticket issuance
    - RevenueEntry yozish
    """

    if not provider_transaction_id:
        raise PaymentTransactionConflict()

    provider_transaction_id = str(
        provider_transaction_id
    )

    order = (
        TicketOrder.objects
        .select_for_update(of=("self",))
        .select_related("user", "competition")
        .get(pk=order_id)
    )

    if order.provider != provider:
        raise PaymentTransactionConflict()

    # Idempotency:
    # PAID order qayta kelsa, faqat bir xil
    # provider transaction ID qabul qilinadi.
    if order.status == TicketOrder.Status.PAID:
        if (
            order.provider_transaction_id
            != provider_transaction_id
        ):
            raise PaymentTransactionConflict()

        issue_tickets_for_paid_order(order)
        return order

    if order.status != TicketOrder.Status.PENDING:
        raise PaymentOrderUnavailable()

    now = timezone.now()

    if (
        order.payment_expires_at is not None
        and order.payment_expires_at <= now
    ):
        raise PaymentOrderUnavailable()

    # To'lov tasdiqlandi.
    order.status = TicketOrder.Status.PAID
    order.paid_at = now
    order.provider_transaction_id = (
        provider_transaction_id
    )

    order.save(
        update_fields=[
            "status",
            "paid_at",
            "provider_transaction_id",
        ]
    )

    # Chiptalarni yaratish.
    # Funksiya o'zi ham idempotent
    # bo'lishi kerak.
    issue_tickets_for_paid_order(order)

    # Daromad yozuvi.
    record_successful_payment(
        category=RevenueEntry.Category.TOURNAMENT,
        source="competition_ticket_order",
        source_payment_id=str(order.pk),
        amount=order.total_amount,
        provider=provider,
        user=order.user,
        paid_at=now,
    )

    return order
