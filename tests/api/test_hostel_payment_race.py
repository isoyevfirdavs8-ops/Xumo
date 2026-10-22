
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.db import close_old_connections, connections
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
from apps.payments.click_services import (
    ClickError,
    complete_click_payment,
    prepare_click_payment,
)
from apps.payments.models import ClickTransaction


@pytest.mark.django_db(transaction=True)
def test_click_complete_and_expiration_race():
    User = get_user_model()

    user = User.objects.create(
        **{User.USERNAME_FIELD: "hostel009"}
    )

    HostelRoom.objects.create(
        number="901",
        name="901 - 2 kishilik",
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

    prepare_data = {
        "click_trans_id": "click-race-901",
        "merchant_trans_id": f"hostel:{reservation.pk}",
        "amount": str(reservation.total_price),
        "click_paydoc_id": "paydoc-race-901",
    }

    tx = prepare_click_payment(prepare_data)

    complete_data = {
        **prepare_data,
        "merchant_prepare_id": str(tx.merchant_prepare_id),
        "error": "0",
    }

    # Ikkala worker ish boshlashidan oldin
    # to'lov muddati tugagan bo'ladi.
    HostelReservation.objects.filter(
        pk=reservation.pk,
    ).update(
        payment_expires_at=timezone.now() - timedelta(seconds=1)
    )

    barrier = threading.Barrier(2)

    def run_complete():
        close_old_connections()

        try:
            barrier.wait(timeout=10)

            try:
                with (
                    patch(
                        "apps.payments.click_services."
                        "verify_click_payment_with_provider",
                        return_value=object(),
                    ),
                    patch(
                        "apps.payments.click_services."
                        "validate_click_verification_result",
                    ),
                ):
                    complete_click_payment(complete_data)

                return "completed"

            except ClickError:
                return "rejected"

        finally:
            connections.close_all()

    def run_expiration():
        close_old_connections()

        try:
            barrier.wait(timeout=10)
            return expire_hostel_reservations(batch_size=10)

        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        complete_future = executor.submit(run_complete)
        expire_future = executor.submit(run_expiration)

        complete_result = complete_future.result(timeout=30)
        expired_count = expire_future.result(timeout=30)

    reservation.refresh_from_db()
    tx.refresh_from_db()

    assert complete_result == "rejected"
    assert expired_count in (0, 1)

    if expired_count == 0:
        retry_count = expire_hostel_reservations(
            batch_size=10
        )
        assert retry_count == 1

    # Database'dan oxirgi holatni qayta o'qiymiz.
    reservation.refresh_from_db()
    tx.refresh_from_db()

    assert reservation.status == HostelReservation.Status.EXPIRED
    assert tx.status == ClickTransaction.Status.PREPARED

    assert HostelBooking.objects.filter(
        reservation=reservation,
        status=HostelBooking.Status.EXPIRED,
    ).count() == 1

    assert HostelBooking.objects.filter(
        reservation=reservation,
        status=HostelBooking.Status.PAID,
    ).count() == 0
    assert tx.status == ClickTransaction.Status.PREPARED

    assert HostelBooking.objects.filter(
        reservation=reservation,
        status=HostelBooking.Status.EXPIRED,
    ).count() == 1

    assert HostelBooking.objects.filter(
        reservation=reservation,
        status=HostelBooking.Status.PAID,
    ).count() == 0
