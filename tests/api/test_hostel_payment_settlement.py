
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.hostel.models import (
    HostelBooking,
    HostelReservation,
    HostelRoom,
)
from apps.hostel.services import create_hostel_reservation
from apps.hostel.payment_services import confirm_hostel_payment
from apps.payments.exceptions import PaymentOrderUnavailable


@pytest.fixture
def pending_hostel_reservation(db):
    User = get_user_model()

    user = User.objects.create(
        **{User.USERNAME_FIELD: "hostel007"}
    )

    HostelRoom.objects.create(
        number="701",
        name="701 - 2 kishilik",
        capacity=2,
        daily_price="150000.00",
    )

    check_in = timezone.localdate() + timedelta(days=2)

    return create_hostel_reservation(
        user=user,
        check_in=check_in,
        check_out=check_in + timedelta(days=2),
        capacity=2,
        room_count=1,
    )


@pytest.mark.django_db
def test_hostel_payment_marks_booking_paid(
    pending_hostel_reservation,
):
    reservation = pending_hostel_reservation

    result = confirm_hostel_payment(
        reservation_id=reservation.pk,
        provider="click",
        provider_transaction_id="click-test-701",
        verified_amount=reservation.total_price,
    )

    reservation.refresh_from_db()

    assert result.pk == reservation.pk
    assert reservation.status == HostelReservation.Status.PAID
    assert reservation.paid_at is not None

    assert HostelBooking.objects.filter(
        reservation=reservation,
        status=HostelBooking.Status.PAID,
    ).count() == 1


@pytest.mark.django_db
def test_expired_hostel_cannot_be_paid(
    pending_hostel_reservation,
):
    reservation = pending_hostel_reservation

    HostelReservation.objects.filter(
        pk=reservation.pk
    ).update(
        payment_expires_at=(
            timezone.now() - timedelta(seconds=1)
        )
    )

    with pytest.raises(PaymentOrderUnavailable):
        confirm_hostel_payment(
            reservation_id=reservation.pk,
            provider="click",
            provider_transaction_id="click-test-702",
            verified_amount=reservation.total_price,
        )

    reservation.refresh_from_db()

    assert reservation.status == (
        HostelReservation.Status.PENDING_PAYMENT
    )

    assert HostelBooking.objects.filter(
        reservation=reservation,
        status=HostelBooking.Status.PENDING_PAYMENT,
    ).count() == 1
