
import pytest

from apps.payments.click_security import (
    verify_click_signature,
)
from apps.payments.security import (
    PaymentVerificationError,
)


@pytest.fixture
def click_settings(settings):
    settings.PAYMENT_MODE = "live"
    settings.CLICK_MERCHANT_ID = "12345"
    settings.CLICK_SERVICE_ID = "67890"
    settings.CLICK_SECRET_KEY = "test-secret"

    return settings


def test_click_missing_fields(click_settings):
    with pytest.raises(PaymentVerificationError):
        verify_click_signature({})


def test_click_invalid_service_id(click_settings):
    data = {
        "click_trans_id": "123",
        "service_id": "wrong",
        "merchant_trans_id": "football:1",
        "amount": "100000",
        "action": "0",
        "sign_time": "2026-10-14 10:00:00",
        "sign_string": "invalid",
    }

    with pytest.raises(PaymentVerificationError):
        verify_click_signature(data)


def test_click_invalid_signature(click_settings):
    data = {
        "click_trans_id": "123",
        "service_id": "67890",
        "merchant_trans_id": "football:1",
        "amount": "100000",
        "action": "0",
        "sign_time": "2026-10-14 10:00:00",
        "sign_string": "invalid",
    }

    with pytest.raises(PaymentVerificationError):
        verify_click_signature(data)
