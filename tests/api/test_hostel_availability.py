
from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.hostel.models import HostelRoom


@pytest.mark.django_db
def test_hostel_availability_filters_capacity():
    HostelRoom.objects.create(
        number="101",
        name="2 kishilik xona",
        capacity=2,
        daily_price="150000.00",
    )

    for number in ["102", "103", "104", "105"]:
        HostelRoom.objects.create(
            number=number,
            name=f"{number} - 3 kishilik",
            capacity=3,
            daily_price="200000.00",
        )

    for number in ["106", "107"]:
        HostelRoom.objects.create(
            number=number,
            name=f"{number} - 4 kishilik",
            capacity=4,
            daily_price="250000.00",
        )

    check_in = timezone.localdate() + timedelta(days=2)
    check_out = check_in + timedelta(days=3)

    client = APIClient()

    response = client.get(
        "/api/v1/hostel/availability/",
        {
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "capacity": 3,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["nights"] == 3
    assert len(data["rooms"]) == 4
    assert data["summary"][0]["capacity"] == 3
    assert data["summary"][0]["total_rooms"] == 4
    assert data["summary"][0]["available_rooms"] == 4

    assert all(
        room["capacity"] == 3
        for room in data["rooms"]
    )


@pytest.mark.django_db
def test_hostel_availability_rejects_invalid_dates():
    client = APIClient()
    today = timezone.localdate()

    response = client.get(
        "/api/v1/hostel/availability/",
        {
            "check_in": today.isoformat(),
            "check_out": today.isoformat(),
        },
    )

    assert response.status_code == 400
