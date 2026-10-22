
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest

from django.contrib.auth import get_user_model
from django.db import (
    close_old_connections,
    connections,
    transaction,
)
from django.utils import timezone

from apps.hostel.models import (
    HostelBooking,
    HostelReservation,
    HostelRoom,
)
from apps.hostel.services import (
    create_hostel_reservation,
    expire_hostel_reservations,
)


@pytest.mark.django_db(transaction=True)
def test_expiration_skips_locked_hostel_reservation():
    User = get_user_model()

    user = User.objects.create(
        **{User.USERNAME_FIELD: "hostel010"}
    )

    HostelRoom.objects.create(
        number="1001",
        name="1001 - 2 kishilik",
        capacity=2,
        daily_price="150000.00",
    )

    check_in = timezone.localdate() + timedelta(days=2)

    reservation = create_hostel_reservation(
        user=user,
        check_in=check_in,
        check_out=check_in + timedelta(days=2),
        capacity=2,
        room_count=1,
    )

    HostelReservation.objects.filter(
        pk=reservation.pk
    ).update(
        payment_expires_at=(
            timezone.now() - timedelta(seconds=1)
        )
    )

    lock_acquired = threading.Event()
    release_lock = threading.Event()

    def hold_reservation_lock():
        close_old_connections()

        try:
            with transaction.atomic():
                locked = (
                    HostelReservation.objects
                    .select_for_update()
                    .get(pk=reservation.pk)
                )

                assert locked.pk == reservation.pk

                lock_acquired.set()

                if not release_lock.wait(timeout=15):
                    raise TimeoutError(
                        "Reservation lock release timeout"
                    )

        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(hold_reservation_lock)

        try:
            assert lock_acquired.wait(timeout=10)

            # Boshqa connection lockni ushlab turibdi.
            # skip_locked=True kutmasdan o'tkazishi kerak.
            skipped_count = expire_hostel_reservations(
                batch_size=10
            )

            assert skipped_count == 0

            reservation.refresh_from_db()

            assert reservation.status == (
                HostelReservation.Status.PENDING_PAYMENT
            )

        finally:
            release_lock.set()
            future.result(timeout=20)

    # Endi lock bo'shadi.
    expired_count = expire_hostel_reservations(
        batch_size=10
    )

    assert expired_count == 1

    reservation.refresh_from_db()

    assert reservation.status == (
        HostelReservation.Status.EXPIRED
    )

    assert HostelBooking.objects.filter(
        reservation=reservation,
        status=HostelBooking.Status.EXPIRED,
    ).count() == 1
