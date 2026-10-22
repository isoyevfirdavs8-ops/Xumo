
from datetime import timedelta
import uuid
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
def hostel_client(db):
    User = get_user_model()

    user = User(
        **{User.USERNAME_FIELD: "hostel001"}
    )
    user.set_password("TestPassword123!")
    user.save()

    client = APIClient()
    client.force_authenticate(user=user)

    return client


@pytest.fixture
def three_person_rooms(db):
    return [
        HostelRoom.objects.create(
            number=str(number),
            name=f"{number} - 3 kishilik",
            capacity=3,
            daily_price="200000.00",
        )
        for number in range(201, 205)
    ]


@pytest.mark.django_db
def test_book_three_rooms_atomically(
    hostel_client,
    three_person_rooms,
):
    check_in = timezone.localdate() + timedelta(days=2)
    check_out = check_in + timedelta(days=3)

    response = hostel_client.post(
        "/api/v1/hostel/bookings/",
        {
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "capacity": 3,
            "room_count": 3,
        },
        format="json",
        HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
    )

    assert response.status_code == 201, response.data
    assert HostelReservation.objects.count() == 1
    assert HostelBooking.objects.count() == 3

    data = response.json()

    assert data["nights"] == 3
    assert len(data["bookings"]) == 3
    assert float(data["total_price"]) == 1800000.0


@pytest.mark.django_db
def test_cannot_book_more_than_available(
    hostel_client,
    three_person_rooms,
):
    check_in = timezone.localdate() + timedelta(days=2)
    check_out = check_in + timedelta(days=3)

    payload = {
        "check_in": check_in.isoformat(),
        "check_out": check_out.isoformat(),
        "capacity": 3,
        "room_count": 3,
    }

    first = hostel_client.post(
        "/api/v1/hostel/bookings/",
        payload,
        format="json",
        HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
    )

    assert first.status_code == 201, first.data

    second = hostel_client.post(
        "/api/v1/hostel/bookings/",
        payload,
        format="json",
        HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
    )

    assert second.status_code == 400, second.data

    assert HostelReservation.objects.count() == 1
    assert HostelBooking.objects.count() == 3

    availability = hostel_client.get(
        "/api/v1/hostel/availability/",
        {
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "capacity": 3,
        },
    )

    assert availability.status_code == 200
    assert availability.json()["summary"][0]["available_rooms"] == 1
