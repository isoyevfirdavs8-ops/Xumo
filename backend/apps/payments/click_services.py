
from decimal import Decimal, InvalidOperation

from apps.football.models import FootballSubscription
from django.utils import timezone
from .click_verification import (
    ClickVerificationUnavailable,
    verify_click_payment_with_provider,
)
from apps.competitions.models import TicketOrder
from apps.football.models import HourlyBooking
from apps.restaurant_orders.models import RestaurantOrder
from apps.finance.payment_settlement import (
    settle_restaurant_payment,
    settle_competition_payment,
)
from apps.hostel.models import HostelReservation
from apps.hostel.payment_services import confirm_hostel_payment

from apps.football.academy_payment_services import (
    confirm_football_academy_payment,
)
from apps.football.payment_services import (
    confirm_football_payment,
)
from .click_orders import get_click_order
from .models import ClickTransaction
from .security import PaymentVerificationError
from django.db import IntegrityError, transaction

from .click_verification import (
    ClickVerificationError,
    ClickVerificationUnavailable,
    verify_click_payment_with_provider,
    validate_click_verification_result,
)

class ClickError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(message)

def is_click_unique_conflict(exc):
    """
    PostgreSQL unique violation (23505) va
    faqat ruxsat etilgan Click constraintlarini
    aniqlaydi.
    """
    cause = exc.__cause__

    if cause is None:
        return False

    sqlstate = getattr(cause, "sqlstate", None)

    if sqlstate is None:
        sqlstate = getattr(cause, "pgcode", None)

    constraint_name = getattr(
        getattr(cause, "diag", None),
        "constraint_name",
        None,
    )

    allowed_constraints = {
        "unique_prepared_click_order",
        "unique_completed_click_order",
        "payments_clicktransaction_click_trans_id_key",
    }

    return (
        sqlstate == "23505"
        and constraint_name in allowed_constraints
    )


def validate_click_paydoc_id(tx, data):
    """
    Agar callbackda click_paydoc_id mavjud bo'lsa,
    avval saqlangan qiymat bilan solishtiradi.

    Missing qiymatni majburiy deb hisoblamaydi.
    """
    incoming = data.get("click_paydoc_id")

    if incoming is None or str(incoming) == "":
        return

    incoming = str(incoming)
    stored = str(tx.click_paydoc_id or "")

    if stored and stored != incoming:
        raise ClickError(
            -4,
            "Click paydoc transaction mismatch",
        )



def get_order_info(merchant_trans_id):
    try:
        return get_click_order(merchant_trans_id)
    except (
        PaymentVerificationError,
        ValueError,
        TypeError,
    ) as exc:
        raise ClickError(-5, str(exc))


def validate_click_amount(info, raw_amount):
    try:
        amount = Decimal(str(raw_amount))
    except (InvalidOperation, TypeError, ValueError):
        raise ClickError(-2, "Invalid amount")

    if (
        not amount.is_finite()
        or amount <= 0
        or amount != info.amount
    ):
        raise ClickError(-2, "Incorrect amount")

    return amount


def validate_order_state(info):
    now = timezone.now()

    if info.category == "restaurant":
        order = RestaurantOrder.objects.get(
            pk=info.order_id
        )

        if order.provider != "click":
            raise ClickError(-5, "Wrong provider")

        if order.status != RestaurantOrder.Status.PENDING:
            raise ClickError(-9, "Order unavailable")

        if order.expires_at <= now:
            raise ClickError(-9, "Order expired")

    elif info.category == "competition":
        order = TicketOrder.objects.get(
            pk=info.order_id
        )

        if order.provider != "click":
            raise ClickError(-5, "Wrong provider")

        if order.status != TicketOrder.Status.PENDING:
            raise ClickError(-9, "Order unavailable")

        if (
            order.payment_expires_at is not None
            and order.payment_expires_at <= now
        ):
            raise ClickError(-9, "Order expired")

    elif info.category == "football":
        booking = HourlyBooking.objects.get(
            pk=info.order_id
        )

        if booking.status != HourlyBooking.Status.PENDING_PAYMENT:
            raise ClickError(-9, "Booking unavailable")

        if booking.hold_expires_at <= now:
            raise ClickError(-9, "Booking expired")

    elif info.category == "football_academy":
        subscription = FootballSubscription.objects.get(
            pk=info.order_id
        )

        if subscription.status != FootballSubscription.Status.PENDING_PAYMENT:
            raise ClickError(-9, "Subscription unavailable")

        if (
            subscription.payment_expires_at is None
            or subscription.payment_expires_at <= now
        ):
            raise ClickError(-9, "Subscription expired")
    elif info.category == "hostel":
        reservation = HostelReservation.objects.get(
            pk=info.order_id
        )

        if reservation.status != (
            HostelReservation.Status.PENDING_PAYMENT
        ):
            raise ClickError(
                -9,
                "Hostel reservation unavailable",
            )

        if (
            reservation.payment_expires_at is None
            or reservation.payment_expires_at <= now
        ):
            raise ClickError(
                -9,
                "Hostel reservation expired",
            )



@transaction.atomic
def prepare_click_payment(data):
    merchant_trans_id = data["merchant_trans_id"]
    click_trans_id = str(data["click_trans_id"])

    info = get_order_info(merchant_trans_id)

    amount = validate_click_amount(
        info,
        data["amount"],
    )

    # 1. Birinchi navbatda Order lock.
    # Restaurant, Competition va Football uchun
    # mos modelni yordamchi funksiya tanlaydi.
    lock_click_order(info)

    # 2. Keyin ClickTransaction lock.
    existing = (
        ClickTransaction.objects
        .select_for_update()
        .filter(click_trans_id=click_trans_id)
        .first()
    )

    if existing:
        if (
            existing.category != info.category
            or existing.order_id != info.order_id
            or existing.amount != amount
        ):
            raise ClickError(-4, "Transaction mismatch")

        validate_click_paydoc_id(existing, data)

        if existing.status != ClickTransaction.Status.PREPARED:
            raise ClickError(-9, "Transaction not active")

        return existing

    # 3. Order holatini tekshirish.
    validate_order_state(info)

    # 4. Bitta buyurtmaga faqat bitta
    # faol Click tranzaksiya.
    another = ClickTransaction.objects.filter(
        category=info.category,
        order_id=info.order_id,
        status=ClickTransaction.Status.PREPARED,
    ).exists()

    if another:
        raise ClickError(
            -4,
            "Another transaction is active",
        )

    # 5. Yangi Click tranzaksiya.
    try:
        with transaction.atomic():
            return ClickTransaction.objects.create(
                click_trans_id=click_trans_id,
                click_paydoc_id=str(
                    data.get("click_paydoc_id", "")
                ),
                category=info.category,
                order_id=info.order_id,
                amount=amount,
                status=ClickTransaction.Status.PREPARED,
            )

    except IntegrityError as exc:
        if not is_click_unique_conflict(exc):
            raise

        raise ClickError(
            -4,
            "Payment transaction conflict",
        ) from exc


def complete_click_payment(data):
    click_trans_id = str(data["click_trans_id"])
    click_error = str(data.get("error", ""))

    # Bu dastlabki o'qish lock emas.
    # Yakuniy tekshiruv ichki atomic funksiyada.
    tx = ClickTransaction.objects.filter(
        click_trans_id=click_trans_id,
    ).first()

    if tx is not None:
        validate_click_paydoc_id(tx, data)

    # Mavjud idempotency va cancellation
    # xatti-harakatlarini saqlaymiz.
    if (
        click_error != "0"
        or (
            tx is not None
            and tx.status != ClickTransaction.Status.PREPARED
        )
    ):
        return _complete_click_payment_atomic(data)

    # Tranzaksiya topilmasa, avvalgi -6
    # xatolik ichki funksiyada qaytariladi.
    if tx is None:
        return _complete_click_payment_atomic(data)

    # Providerga murojaat qilishdan oldin
    # callback summasini dastlabki tekshirish.
    info = get_order_info(data["merchant_trans_id"])
    amount = validate_click_amount(info, data["amount"])

    if (
        tx.category != info.category
        or tx.order_id != info.order_id
        or tx.amount != amount
        or str(tx.merchant_prepare_id)
        != str(data["merchant_prepare_id"])
    ):
        return _complete_click_payment_atomic(data)

    # Muhim: bu joyda atomic transaction ochiq emas.
    try:
        verification = verify_click_payment_with_provider(
            click_trans_id=click_trans_id,
            merchant_trans_id=data["merchant_trans_id"],
            amount=amount,
        )

        validate_click_verification_result(
            result=verification,
            click_trans_id=click_trans_id,
            merchant_trans_id=data["merchant_trans_id"],
            amount=amount,
        )

    except ClickVerificationError as exc:
        raise ClickError(
            -9,
            "Click provider verification failed",
        ) from exc

    # Verificationdan keyin barcha DB holatlari
    # qayta tekshiriladi va settlement atomic bajariladi.
    return _complete_click_payment_atomic(
        data,
        verification=verification,
    )


@transaction.atomic
def _complete_click_payment_atomic(data, verification=None):
    click_trans_id = str(data["click_trans_id"])
    prepare_id = str(data["merchant_prepare_id"])

    # 1. Avval order ma'lumotini aniqlaymiz.
    info = get_order_info(data["merchant_trans_id"])

    amount = validate_click_amount(
        info,
        data["amount"],
    )

    # 2. Order lock — barcha Click oqimlarida birinchi.
    lock_click_order(info)

    # 3. Keyin ClickTransaction lock.
    tx = (
        ClickTransaction.objects
        .select_for_update()
        .filter(click_trans_id=click_trans_id)
        .first()
    )

    if tx is None:
        raise ClickError(-6, "Transaction not found")

    if (
        str(tx.merchant_prepare_id) != prepare_id
        or tx.category != info.category
        or tx.order_id != info.order_id
        or tx.amount != amount
    ):
        raise ClickError(-4, "Transaction mismatch")

    validate_click_paydoc_id(tx, data)

    if tx.status == ClickTransaction.Status.COMPLETED:
        if str(data.get("error", "")) != "0":
            raise ClickError(
                -9,
                "Completed transaction cannot be cancelled",
            )

        return tx

    if tx.status == ClickTransaction.Status.CANCELLED:
        if str(data.get("error", "")) != "0":
            return tx

        raise ClickError(
            -9,
            "Cancelled transaction cannot be completed",
        )

    click_error = str(data.get("error", ""))

    if click_error != "0":
        tx.status = ClickTransaction.Status.CANCELLED
        tx.save(
            update_fields=["status", "updated_at"]
        )
        return tx

    # Click provider orqali to'lovni tekshirish.

    # Verification tashqi transactionda bajarilgan.
    # Bu yerda uning natijasini lock ostidagi
    # haqiqiy transaction bilan qayta solishtiramiz.
    if verification is None:
        raise ClickError(
            -9,
            "Click provider verification required",
        )

    try:
        validate_click_verification_result(
            result=verification,
            click_trans_id=tx.click_trans_id,
            merchant_trans_id=data["merchant_trans_id"],
            amount=tx.amount,
        )
    except ClickVerificationError as exc:
        raise ClickError(
            -9,
            "Click provider verification failed",
        ) from exc

    validate_order_state(info)


    # 5. Settlement ham shu order lockdan foydalanadi.
    if tx.category == "restaurant":
        settle_restaurant_payment(
            order_id=tx.order_id,
            provider="click",
            provider_transaction_id=tx.click_trans_id,
        )

    elif tx.category == "competition":
        settle_competition_payment(
            order_id=tx.order_id,
            provider="click",
            provider_transaction_id=tx.click_trans_id,
        )

    elif tx.category == "football":
        confirm_football_payment(
            booking_id=tx.order_id,
            provider="click",
            provider_transaction_id=tx.click_trans_id,
            verified_amount=tx.amount,
        )
    elif tx.category == "football_academy":
        confirm_football_academy_payment(
            subscription_id=tx.order_id,
            provider="click",
            provider_transaction_id=tx.click_trans_id,
            verified_amount=tx.amount,
        )
    elif tx.category == "hostel":
        confirm_hostel_payment(
            reservation_id=tx.order_id,
            provider="click",
            provider_transaction_id=tx.click_trans_id,
            verified_amount=tx.amount,
        )

    else:
        raise ClickError(-5, "Unknown category")

    tx.status = ClickTransaction.Status.COMPLETED
    tx.save(
        update_fields=["status", "updated_at"]
    )

    return tx




def lock_click_order(info):
    if info.category == "restaurant":
        return (
            RestaurantOrder.objects
            .select_for_update(of=("self",))
            .get(pk=info.order_id)
        )

    if info.category == "competition":
        return (
            TicketOrder.objects
            .select_for_update()
            .get(pk=info.order_id)
        )

    if info.category == "football":
        return (
            HourlyBooking.objects
            .select_for_update()
            .get(pk=info.order_id)
        )
    if info.category == "football_academy":
        return (
            FootballSubscription.objects
            .select_for_update()
            .get(pk=info.order_id)
        )
    if info.category == "hostel":
        return (
            HostelReservation.objects
            .select_for_update()
            .get(pk=info.order_id)
        )
    raise ClickError(-5, "Unknown order category")


