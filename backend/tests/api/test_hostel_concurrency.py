
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.db import close_old_connections, connections
from django.utils import timezone
from rest_framework.test import APIClient

from apps.hostel.models import (
    HostelBooking,
    HostelReservation,
    HostelRoom,
)


@pytest.mark.django_db(transaction=True)
def test_two_users_cannot_book_same_room_concurrently():
    User = get_user_model()

    user1 = User.objects.create(
        **{User.USERNAME_FIELD: "hostel005"}
    )
    user2 = User.objects.create(
        **{User.USERNAME_FIELD: "hostel006"}
    )

    room = HostelRoom.objects.create(
        number="601",
        name="601 - 2 kishilik",
        capacity=2,
        daily_price="150000.00",
    )

    check_in = timezone.localdate() + timedelta(days=2)
    check_out = check_in + timedelta(days=3)

    payload = {
        "check_in": check_in.isoformat(),
        "check_out": check_out.isoformat(),
        "capacity": 2,
        "room_count": 1,
    }

    barrier = threading.Barrier(2)

    def book_room(user):
        close_old_connections()

        try:
            client = APIClient()
            client.force_authenticate(user=user)

            barrier.wait(timeout=10)

            response = client.post(
                "/api/v1/hostel/bookings/",
                payload,
                format="json",
                HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
            )

            return response.status_code, response.data

        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        future1 = executor.submit(book_room, user1)
        future2 = executor.submit(book_room, user2)

        result1 = future1.result(timeout=20)
        result2 = future2.result(timeout=20)

    status_codes = sorted([result1[0], result2[0]])

    assert status_codes == [201, 400], (
        f"Unexpected responses: {result1}, {result2}"
    )

    assert HostelReservation.objects.count() == 1
    assert HostelBooking.objects.count() == 1

    booking = HostelBooking.objects.get()

    assert booking.room_id == room.pk
    assert (
        booking.status
        == HostelBooking.Status.PENDING_PAYMENT
    )
