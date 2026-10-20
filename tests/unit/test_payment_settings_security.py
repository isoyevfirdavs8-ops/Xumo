
import pytest

from django.conf import settings


def test_payment_mode_is_valid():
    assert settings.PAYMENT_MODE in {
        "disabled",
        "demo",
        "sandbox",
        "live",
    }


def test_restaurant_payment_mode_is_valid():
    assert settings.RESTAURANT_PAYMENT_MODE in {
        "disabled",
        "sandbox",
        "live",
    }


def test_demo_mode_requires_debug():
    if settings.PAYMENT_MODE == "demo":
        assert settings.DEBUG is True


def test_click_credentials_are_strings():
    assert isinstance(settings.CLICK_MERCHANT_ID, str)
    assert isinstance(settings.CLICK_SERVICE_ID, str)
    assert isinstance(settings.CLICK_SECRET_KEY, str)


def test_payme_merchant_id_is_string():
    assert isinstance(settings.PAYME_MERCHANT_ID, str)
