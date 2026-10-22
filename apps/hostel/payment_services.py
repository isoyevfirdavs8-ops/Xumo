
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone

from apps.payments.exceptions import (
    PaymentOrderUnavailable,
    PaymentTransactionConflict,
)

from .models import HostelBooking, HostelReservation


@transaction.atomic
def confirm_hostel_payment(
    *,
    reservation_id,
    provider,
    provider_transaction_id,
    verified_amount,
):
    if provider != "click" or not str(
        provider_transaction_id
    ).strip():
        raise PaymentTransactionConflict()

    try:
        amount = Decimal(str(verified_amount))
    except (InvalidOperation, TypeError, ValueError):
        raise PaymentTransactionConflict()

    if not amount.is_finite() or amount <= 0:
        raise PaymentTransactionConflict()

    reservation = (
        HostelReservation.objects
        .select_for_update()
        .filter(pk=reservation_id)
        .first()
    )

    if reservation is None:
        raise PaymentOrderUnavailable()

    if reservation.total_price != amount:
        raise PaymentTransactionConflict()

    if reservation.status != (
        HostelReservation.Status.PENDING_PAYMENT
    ):
        raise PaymentOrderUnavailable()

    now = timezone.now()

    if (
        reservation.payment_expires_at is None
        or reservation.payment_expires_at <= now
    ):
        raise PaymentOrderUnavailable()

    bookings = list(
        HostelBooking.objects
        .select_for_update()
        .filter(reservation=reservation)
        .order_by("pk")
    )

    if not bookings:
        raise PaymentOrderUnavailable()

    if any(
        booking.status != HostelBooking.Status.PENDING_PAYMENT
        for booking in bookings
    ):
        raise PaymentOrderUnavailable()

    HostelBooking.objects.filter(
        pk__in=[booking.pk for booking in bookings]
    ).update(
        status=HostelBooking.Status.PAID
    )

    reservation.status = HostelReservation.Status.PAID
    reservation.paid_at = now
    reservation.save(
        update_fields=[
            "status",
            "paid_at",
            "updated_at",
        ]
    )

    return reservation
