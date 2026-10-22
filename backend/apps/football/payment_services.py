
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone

from apps.finance.models import RevenueEntry
from apps.finance.recording import record_successful_payment

from apps.payments.exceptions import (
    PaymentOrderUnavailable,
    PaymentTransactionConflict,
)

from .models import (
    HourlyBooking,
    FootballPayment,
)


@transaction.atomic
def confirm_football_payment(
    *,
    booking_id,
    provider,
    provider_transaction_id,
    verified_amount,
):
    """
    Football booking uchun tasdiqlangan
    provider to'lovini yakunlaydi.

    Bu funksiya faqat payment provider
    callbacki tekshirilgandan keyin
    chaqirilishi kerak.

    Xususiyatlar:
    - PostgreSQL row-level locking
    - ACID transaction
    - Idempotency
    - Provider transaction ID validation
    - Booking confirmation
    - RevenueEntry yozish
    """

    # Provider tekshiruvi.
    if provider not in FootballPayment.Provider.values:
        raise PaymentTransactionConflict()

    if not provider_transaction_id:
        raise PaymentTransactionConflict()

    provider_transaction_id = str(
        provider_transaction_id
    )

    # Verified amount normalizatsiyasi.
    # Float qabul qilinmaydi.
    if isinstance(verified_amount, (float, bool)):
        raise PaymentTransactionConflict()

    try:
        amount = Decimal(str(verified_amount))
    except (
        InvalidOperation,
        TypeError,
        ValueError,
    ):
        raise PaymentTransactionConflict()

    if not amount.is_finite() or amount <= 0:
        raise PaymentTransactionConflict()

    # Booking lock.
    booking = (
        HourlyBooking.objects
        .select_for_update(of=("self",))
        .select_related("user")
        .get(pk=booking_id)
    )

    if amount != booking.price_snapshot:
        raise PaymentTransactionConflict()

    # Oldin muvaffaqiyatli to'langanmi?
    existing = (
        FootballPayment.objects
        .select_for_update()
        .filter(
            booking=booking,
            status=FootballPayment.Status.SUCCEEDED,
        )
        .first()
    )

    if existing:
        if (
            existing.provider != provider
            or existing.provider_transaction_id
            != provider_transaction_id
        ):
            raise PaymentTransactionConflict()

        # Bir xil tranzaksiya qayta keldi.
        # Settlement va RevenueEntry
        # qayta yaratilmaydi.
        return booking

    # Booking to'lovga yaroqliligini tekshirish.
    if booking.status != HourlyBooking.Status.PENDING_PAYMENT:
        raise PaymentOrderUnavailable()

    now = timezone.now()

    if booking.hold_expires_at <= now:
        raise PaymentOrderUnavailable()

    # To'lovni saqlash.
    FootballPayment.objects.create(
        booking=booking,
        provider=provider,
        provider_transaction_id=provider_transaction_id,
        amount=booking.price_snapshot,
        status=FootballPayment.Status.SUCCEEDED,
        is_demo=False,
        paid_at=now,
    )

    # Bookingni tasdiqlash.
    booking.status = HourlyBooking.Status.CONFIRMED
    booking.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    # Moliyaviy yozuv.
    record_successful_payment(
        category=RevenueEntry.Category.FOOTBALL,
        source="football_booking",
        source_payment_id=str(booking.pk),
        amount=booking.price_snapshot,
        provider=provider,
        user=booking.user,
        paid_at=now,
    )

    return booking
