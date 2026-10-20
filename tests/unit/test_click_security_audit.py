
import hashlib

import pytest

from apps.payments.click_security import (
    verify_click_signature,
)
from apps.payments.security import PaymentVerificationError


@pytest.fixture
def click_credentials(settings):
    settings.PAYMENT_MODE = "live"
    settings.CLICK_MERCHANT_ID = "test-merchant"
    settings.CLICK_SERVICE_ID = "12345"
    settings.CLICK_SECRET_KEY = "test-secret-key"


def make_signed_payload(
    *,
    action="1",
    error="0",
    amount="50000.00",
):
    data = {
        "click_trans_id": "123456789",
        "service_id": "12345",
        "merchant_trans_id": "competition:100",
        "merchant_prepare_id": "25",
        "amount": amount,
        "action": action,
        "error": error,
        "sign_time": "2026-10-14 10:00:00",
    }

    parts = [
        data["click_trans_id"],
        data["service_id"],
        "test-secret-key",
        data["merchant_trans_id"],
    ]

    if action == "1":
        parts.append(data["merchant_prepare_id"])

    parts.extend([
        data["amount"],
        data["action"],
        data["sign_time"],
    ])

    data["sign_string"] = hashlib.md5(
        "".join(parts).encode("utf-8")
    ).hexdigest()

    return data


def test_valid_click_signature(click_credentials):
    payload = make_signed_payload()

    assert verify_click_signature(payload) is True


def test_changed_amount_rejected(click_credentials):
    payload = make_signed_payload()
    payload["amount"] = "90000.00"

    with pytest.raises(PaymentVerificationError):
        verify_click_signature(payload)


def test_changed_merchant_rejected(click_credentials):
    payload = make_signed_payload()
    payload["merchant_trans_id"] = "competition:999"

    with pytest.raises(PaymentVerificationError):
        verify_click_signature(payload)


def test_invalid_action_rejected(click_credentials):
    payload = make_signed_payload()
    payload["action"] = "2"

    with pytest.raises(PaymentVerificationError):
        verify_click_signature(payload)


def test_missing_complete_error_rejected(click_credentials):
    payload = make_signed_payload()
    del payload["error"]

    with pytest.raises(PaymentVerificationError):
        verify_click_signature(payload)


def test_invalid_sign_time_rejected(click_credentials):
    payload = make_signed_payload()
    payload["sign_time"] = "invalid-date"

    with pytest.raises(PaymentVerificationError):
        verify_click_signature(payload)


def test_error_field_is_not_covered_by_signature(
    click_credentials,
):
    """
    Hozirgi imzo formulasi xususiyatini qayd etadi.

    Bu xavfsizlik kafolati emas: error maydoni
    o'zgarganda imzo hamon valid bo'lib qoladi.
    """
    payload = make_signed_payload(error="-1")

    assert verify_click_signature(payload) is True

    payload["error"] = "0"

    assert verify_click_signature(payload) is True
