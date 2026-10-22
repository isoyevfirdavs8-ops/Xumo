
import uuid
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.hostel.models import (
    HostelBooking,
    HostelReservation,
    HostelRoom,
)


@pytest.fixture
def booking_client(db):
    User = get_user_model()

    user = User(
        **{User.USERNAME_FIELD: "hostel004"}
    )
    user.set_unusable_password()
    user.save()

    client = APIClient()
    client.force_authenticate(user=user)

    return client


@pytest.fixture
def available_rooms(db):
    for number in range(501, 505):
        HostelRoom.objects.create(
            number=str(number),
            name=f"{number} - 3 kishilik",
            capacity=3,
            daily_price="200000.00",
        )


@pytest.mark.django_db
def test_same_idempotency_key_returns_same_reservation(
    booking_client,
    available_rooms,
):
    check_in = timezone.localdate() + timedelta(days=2)
    check_out = check_in + timedelta(days=3)

    payload = {
        "check_in": check_in.isoformat(),
        "check_out": check_out.isoformat(),
        "capacity": 3,
        "room_count": 2,
    }

    key = str(uuid.uuid4())

    first = booking_client.post(
        "/api/v1/hostel/bookings/",
        payload,
        format="json",
        HTTP_IDEMPOTENCY_KEY=key,
    )

    second = booking_client.post(
        "/api/v1/hostel/bookings/",
        payload,
        format="json",
        HTTP_IDEMPOTENCY_KEY=key,
    )

    assert first.status_code == 201, first.data
    assert second.status_code == 201, second.data

    assert first.data["id"] == second.data["id"]

    assert HostelReservation.objects.count() == 1
    assert HostelBooking.objects.count() == 2


@pytest.mark.django_db
def test_same_key_with_different_payload_rejected(
    booking_client,
    available_rooms,
):
    check_in = timezone.localdate() + timedelta(days=2)
    check_out = check_in + timedelta(days=3)

    key = str(uuid.uuid4())

    payload = {
        "check_in": check_in.isoformat(),
        "check_out": check_out.isoformat(),
        "capacity": 3,
        "room_count": 1,
    }

    first = booking_client.post(
        "/api/v1/hostel/bookings/",
        payload,
        format="json",
        HTTP_IDEMPOTENCY_KEY=key,
    )

    assert first.status_code == 201, first.data

    payload["room_count"] = 2

    second = booking_client.post(
        "/api/v1/hostel/bookings/",
        payload,
        format="json",
        HTTP_IDEMPOTENCY_KEY=key,
    )

    assert second.status_code == 400, second.data

    assert HostelReservation.objects.count() == 1
    assert HostelBooking.objects.count() == 1
