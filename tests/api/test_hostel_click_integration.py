
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.hostel.models import (
    HostelBooking,
    HostelReservation,
    HostelRoom,
)
from apps.hostel.services import create_hostel_reservation
from apps.payments.click_services import (
    ClickError,
    complete_click_payment,
    prepare_click_payment,
)
from apps.payments.models import ClickTransaction


@pytest.fixture
def hostel_click_reservation(db):
    User = get_user_model()
    user = User.objects.create(
        **{User.USERNAME_FIELD: "hostel008"}
    )

    HostelRoom.objects.create(
        number="801",
        name="801 - 2 kishilik",
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


def click_prepare_data(reservation, trans_id="click-hostel-801"):
    return {
        "click_trans_id": trans_id,
        "merchant_trans_id": f"hostel:{reservation.pk}",
        "amount": str(reservation.total_price),
        "click_paydoc_id": "paydoc-801",
    }


def click_complete_data(prepare_data, tx):
    return {
        **prepare_data,
        "merchant_prepare_id": str(tx.merchant_prepare_id),
        "error": "0",
    }


@pytest.mark.django_db
def test_click_prepare_creates_transaction(
    hostel_click_reservation,
):
    reservation = hostel_click_reservation
    data = click_prepare_data(reservation)

    tx = prepare_click_payment(data)

    assert tx.category == "hostel"
    assert tx.order_id == str(reservation.pk)
    assert tx.amount == reservation.total_price
    assert tx.status == ClickTransaction.Status.PREPARED

    reservation.refresh_from_db()

    assert reservation.status == (
        HostelReservation.Status.PENDING_PAYMENT
    )


@pytest.mark.django_db
def test_click_prepare_retry_is_idempotent(
    hostel_click_reservation,
):
    data = click_prepare_data(hostel_click_reservation)

    first = prepare_click_payment(data)
    second = prepare_click_payment(data)

    assert first.pk == second.pk
    assert ClickTransaction.objects.count() == 1


@pytest.mark.django_db
def test_click_complete_marks_reservation_paid(
    hostel_click_reservation,
):
    reservation = hostel_click_reservation
    prepare_data = click_prepare_data(reservation)
    tx = prepare_click_payment(prepare_data)
    complete_data = click_complete_data(prepare_data, tx)

    # Provider tasdiqlash natijasini simulyatsiya qilamiz.
    # Database settlement haqiqiy ishlaydi.
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
        result = complete_click_payment(complete_data)

    reservation.refresh_from_db()
    tx.refresh_from_db()

    assert result.pk == tx.pk
    assert tx.status == ClickTransaction.Status.COMPLETED
    assert reservation.status == HostelReservation.Status.PAID
    assert reservation.paid_at is not None

    assert HostelBooking.objects.filter(
        reservation=reservation,
        status=HostelBooking.Status.PAID,
    ).count() == 1


@pytest.mark.django_db
def test_click_complete_retry_is_idempotent(
    hostel_click_reservation,
):
    reservation = hostel_click_reservation
    prepare_data = click_prepare_data(reservation)
    tx = prepare_click_payment(prepare_data)
    complete_data = click_complete_data(prepare_data, tx)

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
        first = complete_click_payment(complete_data)
        second = complete_click_payment(complete_data)

    assert first.pk == second.pk

    assert ClickTransaction.objects.filter(
        status=ClickTransaction.Status.COMPLETED,
    ).count() == 1

    assert HostelReservation.objects.filter(
        status=HostelReservation.Status.PAID,
    ).count() == 1

    assert HostelBooking.objects.count() == 1


@pytest.mark.django_db
def test_click_complete_rejects_expired_reservation(
    hostel_click_reservation,
):
    reservation = hostel_click_reservation
    prepare_data = click_prepare_data(reservation)
    tx = prepare_click_payment(prepare_data)
    complete_data = click_complete_data(prepare_data, tx)

    HostelReservation.objects.filter(
        pk=reservation.pk,
    ).update(
        payment_expires_at=timezone.now() - timedelta(seconds=1)
    )

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
        pytest.raises(ClickError),
    ):
        complete_click_payment(complete_data)

    reservation.refresh_from_db()
    tx.refresh_from_db()

    assert reservation.status == (
        HostelReservation.Status.PENDING_PAYMENT
    )
    assert tx.status == ClickTransaction.Status.PREPARED
