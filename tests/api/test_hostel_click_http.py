
import hashlib
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.hostel.models import (
    HostelBooking,
    HostelReservation,
    HostelRoom,
)
from apps.hostel.services import create_hostel_reservation
from apps.payments.click_verification import ClickVerificationResult
from apps.payments.models import ClickTransaction


TEST_CREDENTIALS = {
    "service_id": "12345",
    "secret_key": "test-click-secret",
}


def sign_click_data(data):
    parts = [
        str(data["click_trans_id"]),
        str(data["service_id"]),
        TEST_CREDENTIALS["secret_key"],
        str(data["merchant_trans_id"]),
    ]

    if str(data["action"]) == "1":
        parts.append(str(data["merchant_prepare_id"]))

    parts.extend([
        str(data["amount"]),
        str(data["action"]),
        str(data["sign_time"]),
    ])

    result = dict(data)
    result["sign_string"] = hashlib.md5(
        "".join(parts).encode("utf-8")
    ).hexdigest()
    return result


@pytest.fixture
def click_http_environment(db):
    User = get_user_model()
    user = User.objects.create(
        **{User.USERNAME_FIELD: "hostel011"}
    )

    HostelRoom.objects.create(
        number="1101",
        name="1101 - 2 kishilik",
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

    return APIClient(), reservation


@pytest.fixture(autouse=True)
def mock_click_credentials():
    with patch(
        "apps.payments.click_security.get_provider_credentials",
        return_value=TEST_CREDENTIALS,
    ):
        yield


def prepare_payload(reservation):
    return sign_click_data({
        "click_trans_id": "http-hostel-1101",
        "service_id": TEST_CREDENTIALS["service_id"],
        "merchant_trans_id": f"hostel:{reservation.pk}",
        "amount": str(reservation.total_price),
        "action": "0",
        "sign_time": timezone.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
    })


def complete_payload(prepare_data, merchant_prepare_id):
    data = {
        **prepare_data,
        "action": "1",
        "merchant_prepare_id": str(merchant_prepare_id),
        "error": "0",
    }
    return sign_click_data(data)


def post_prepare(client, payload):
    return client.post(
        reverse("click-prepare"),
        data=payload,
        format="json",
    )


def post_complete(client, payload):
    return client.post(
        reverse("click-complete"),
        data=payload,
        format="json",
    )


@pytest.mark.django_db
def test_http_prepare_valid_signature(click_http_environment):
    client, reservation = click_http_environment

    response = post_prepare(
        client, prepare_payload(reservation)
    )

    assert response.status_code == 200
    assert response.data["error"] == 0
    assert response.data["merchant_prepare_id"] > 0

    assert ClickTransaction.objects.filter(
        category="hostel",
        order_id=str(reservation.pk),
        status=ClickTransaction.Status.PREPARED,
    ).count() == 1


@pytest.mark.django_db
def test_http_prepare_invalid_signature(click_http_environment):
    client, reservation = click_http_environment
    payload = prepare_payload(reservation)
    payload["sign_string"] = "0" * 32

    response = post_prepare(client, payload)

    assert response.status_code == 200
    assert response.data["error"] == -1
    assert ClickTransaction.objects.count() == 0


@pytest.mark.django_db
def test_http_prepare_wrong_amount(click_http_environment):
    client, reservation = click_http_environment
    payload = prepare_payload(reservation)
    payload["amount"] = str(
        reservation.total_price + Decimal("1000.00")
    )
    payload = sign_click_data(payload)

    response = post_prepare(client, payload)

    assert response.status_code == 200
    assert response.data["error"] == -2
    assert ClickTransaction.objects.count() == 0


@pytest.mark.django_db
def test_http_prepare_retry(click_http_environment):
    client, reservation = click_http_environment
    payload = prepare_payload(reservation)

    first = post_prepare(client, payload)
    second = post_prepare(client, payload)

    assert first.data["error"] == 0
    assert second.data["error"] == 0
    assert (
        first.data["merchant_prepare_id"]
        == second.data["merchant_prepare_id"]
    )
    assert ClickTransaction.objects.count() == 1


@pytest.mark.django_db
def test_http_complete_success_and_retry(click_http_environment):
    client, reservation = click_http_environment

    prepared = prepare_payload(reservation)
    prepare_response = post_prepare(client, prepared)

    assert prepare_response.data["error"] == 0

    payload = complete_payload(
        prepared,
        prepare_response.data["merchant_prepare_id"],
    )

    verification = ClickVerificationResult(
        verified=True,
        click_trans_id=payload["click_trans_id"],
        merchant_trans_id=payload["merchant_trans_id"],
        amount=reservation.total_price,
    )

    with patch(
        "apps.payments.click_services."
        "verify_click_payment_with_provider",
        return_value=verification,
    ) as verifier:
        first = post_complete(client, payload)
        second = post_complete(client, payload)

    assert first.status_code == 200
    assert first.data["error"] == 0
    assert second.data["error"] == 0
    assert (
        first.data["merchant_confirm_id"]
        == second.data["merchant_confirm_id"]
    )

    # Takroriy callback provayderga qayta murojaat
    # qilmasligi kerak.
    assert verifier.call_count == 1

    reservation.refresh_from_db()

    assert reservation.status == HostelReservation.Status.PAID

    assert HostelBooking.objects.filter(
        reservation=reservation,
        status=HostelBooking.Status.PAID,
    ).count() == 1

    assert ClickTransaction.objects.filter(
        category="hostel",
        status=ClickTransaction.Status.COMPLETED,
    ).count() == 1


@pytest.mark.django_db
def test_http_complete_without_provider_verification(
    click_http_environment,
):
    client, reservation = click_http_environment

    prepared = prepare_payload(reservation)
    prepare_response = post_prepare(client, prepared)
    assert prepare_response.data["error"] == 0

    payload = complete_payload(
        prepared,
        prepare_response.data["merchant_prepare_id"],
    )

    # Haqiqiy, hozircha sozlanmagan verifier ishlaydi.
    response = post_complete(client, payload)

    assert response.status_code == 200
    assert response.data["error"] == -9

    reservation.refresh_from_db()
    assert reservation.status == (
        HostelReservation.Status.PENDING_PAYMENT
    )

    assert ClickTransaction.objects.filter(
        status=ClickTransaction.Status.COMPLETED,
    ).count() == 0


@pytest.mark.django_db
def test_http_complete_expired_reservation(
    click_http_environment,
):
    client, reservation = click_http_environment

    prepared = prepare_payload(reservation)
    prepare_response = post_prepare(client, prepared)
    assert prepare_response.data["error"] == 0

    payload = complete_payload(
        prepared,
        prepare_response.data["merchant_prepare_id"],
    )

    HostelReservation.objects.filter(
        pk=reservation.pk
    ).update(
        payment_expires_at=timezone.now() - timedelta(seconds=1)
    )

    verification = ClickVerificationResult(
        verified=True,
        click_trans_id=payload["click_trans_id"],
        merchant_trans_id=payload["merchant_trans_id"],
        amount=reservation.total_price,
    )

    with patch(
        "apps.payments.click_services."
        "verify_click_payment_with_provider",
        return_value=verification,
    ):
        response = post_complete(client, payload)

    assert response.status_code == 200
    assert response.data["error"] == -9

    reservation.refresh_from_db()

    assert reservation.status == (
        HostelReservation.Status.PENDING_PAYMENT
    )
    assert ClickTransaction.objects.filter(
        status=ClickTransaction.Status.COMPLETED,
    ).count() == 0
