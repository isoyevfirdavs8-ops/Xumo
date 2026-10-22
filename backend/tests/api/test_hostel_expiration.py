
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone

from apps.hostel.models import (
    HostelBooking,
    HostelReservation,
    HostelRoom,
)
from apps.hostel.services import create_hostel_reservation


@pytest.fixture
def hostel_user(db):
    User = get_user_model()

    user = User(
        **{User.USERNAME_FIELD: "hostel002"}
    )
    user.set_unusable_password()
    user.save()

    return user


@pytest.fixture
def pending_hostel_reservation(hostel_user):
    HostelRoom.objects.create(
        number="301",
        name="3 kishilik xona",
        capacity=3,
        daily_price="200000.00",
    )

    check_in = timezone.localdate() + timedelta(days=2)
    check_out = check_in + timedelta(days=3)

    return create_hostel_reservation(
        user=hostel_user,
        check_in=check_in,
        check_out=check_out,
        capacity=3,
        room_count=1,
    )


@pytest.mark.django_db
def test_expired_reservation_releases_room(
    pending_hostel_reservation,
):
    reservation = pending_hostel_reservation

    reservation.payment_expires_at = (
        timezone.now() - timedelta(minutes=1)
    )
    reservation.save(update_fields=["payment_expires_at"])

    call_command("expire_hostel_bookings")

    reservation.refresh_from_db()

    booking = HostelBooking.objects.get(
        reservation=reservation
    )

    assert reservation.status == HostelReservation.Status.EXPIRED
    assert booking.status == HostelBooking.Status.EXPIRED


@pytest.mark.django_db
def test_unexpired_reservation_stays_pending(
    pending_hostel_reservation,
):
    reservation = pending_hostel_reservation

    call_command("expire_hostel_bookings")

    reservation.refresh_from_db()

    assert (
        reservation.status
        == HostelReservation.Status.PENDING_PAYMENT
    )

    assert HostelBooking.objects.filter(
        reservation=reservation,
        status=HostelBooking.Status.PENDING_PAYMENT,
    ).count() == 1


@pytest.mark.django_db
def test_paid_reservation_does_not_expire(
    pending_hostel_reservation,
):
    reservation = pending_hostel_reservation

    reservation.status = HostelReservation.Status.PAID
    reservation.payment_expires_at = (
        timezone.now() - timedelta(minutes=1)
    )
    reservation.save(
        update_fields=["status", "payment_expires_at"]
    )

    HostelBooking.objects.filter(
        reservation=reservation
    ).update(
        status=HostelBooking.Status.PAID
    )

    call_command("expire_hostel_bookings")

    reservation.refresh_from_db()

    assert reservation.status == HostelReservation.Status.PAID

    assert HostelBooking.objects.filter(
        reservation=reservation,
        status=HostelBooking.Status.PAID,
    ).count() == 1
