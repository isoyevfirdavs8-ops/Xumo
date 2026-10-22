
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

    return settings


def make_click_payload(
    *,
    action="0",
    error="0",
    prepare_id="100",
):
    data = {
        "click_trans_id": "987654",
        "service_id": "12345",
        "merchant_trans_id": "competition:test-order",
        "amount": "50000.00",
        "action": action,
        "sign_time": "2026-10-14 10:00:00",
    }

    if action == "1":
        data["merchant_prepare_id"] = prepare_id

        if error is not None:
            data["error"] = error

    parts = [
        data["click_trans_id"],
        data["service_id"],
        "test-secret-key",
        data["merchant_trans_id"],
    ]

    if action == "1":
        parts.append(str(data["merchant_prepare_id"]))

    parts.extend([
        data["amount"],
        action,
        data["sign_time"],
    ])

    data["sign_string"] = hashlib.md5(
        "".join(parts).encode("utf-8")
    ).hexdigest()

    return data


def test_valid_prepare_signature(click_credentials):
    data = make_click_payload(action="0")

    assert verify_click_signature(data) is True


def test_valid_complete_signature(click_credentials):
    data = make_click_payload(action="1")

    assert verify_click_signature(data) is True


def test_invalid_signature_rejected(click_credentials):
    data = make_click_payload(action="0")
    data["sign_string"] = "invalid-signature"

    with pytest.raises(PaymentVerificationError):
        verify_click_signature(data)


def test_wrong_service_id_rejected(click_credentials):
    data = make_click_payload(action="0")
    data["service_id"] = "99999"

    with pytest.raises(PaymentVerificationError):
        verify_click_signature(data)


def test_missing_prepare_id_rejected(click_credentials):
    data = make_click_payload(action="1")
    del data["merchant_prepare_id"]

    with pytest.raises(PaymentVerificationError):
        verify_click_signature(data)


def test_missing_complete_error_rejected(click_credentials):
    data = make_click_payload(
        action="1",
        error=None,
    )

    with pytest.raises(PaymentVerificationError):
        verify_click_signature(data)


def test_invalid_action_rejected(click_credentials):
    data = make_click_payload(action="0")
    data["action"] = "9"

    with pytest.raises(PaymentVerificationError):
        verify_click_signature(data)


def test_tampered_amount_rejected(click_credentials):
    data = make_click_payload(action="0")
    data["amount"] = "1000.00"

    with pytest.raises(PaymentVerificationError):
        verify_click_signature(data)
