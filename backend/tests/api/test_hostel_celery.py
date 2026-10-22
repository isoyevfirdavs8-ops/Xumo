
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
from apps.hostel.tasks import expire_hostel_reservations_task


@pytest.mark.django_db
def test_hostel_expiration_celery_task():
    User = get_user_model()

    user = User(
        **{User.USERNAME_FIELD: "hostel003"}
    )
    user.set_unusable_password()
    user.save()

    HostelRoom.objects.create(
        number="401",
        name="4 kishilik xona",
        capacity=4,
        daily_price="300000.00",
    )

    check_in = timezone.localdate() + timedelta(days=2)
    check_out = check_in + timedelta(days=2)

    reservation = create_hostel_reservation(
        user=user,
        check_in=check_in,
        check_out=check_out,
        capacity=4,
        room_count=1,
    )

    reservation.payment_expires_at = (
        timezone.now() - timedelta(minutes=1)
    )
    reservation.save(update_fields=["payment_expires_at"])

    # Taskni sinxron ishga tushirib, biznes logikani tekshiramiz.
    count = expire_hostel_reservations_task()

    reservation.refresh_from_db()

    assert count == 1
    assert reservation.status == HostelReservation.Status.EXPIRED

    assert HostelBooking.objects.filter(
        reservation=reservation,
        status=HostelBooking.Status.EXPIRED,
    ).count() == 1
