
from decimal import Decimal
from unittest.mock import patch

import pytest

from django.core.cache import cache
from django.test import override_settings

from apps.payments.click_verification import (
    ClickVerificationResult,
)


@pytest.fixture(autouse=True)
def isolated_throttle_cache():
    with override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "fcbukhara-tests",
            }
        }
    ):
        cache.clear()
        yield
        cache.clear()


@pytest.fixture
def verified_click_provider():
    """
    Faqat test muhitida provider verificationni
    muvaffaqiyatli deb simulyatsiya qiladi.
    """

    def fake_verify(
        *,
        click_trans_id,
        merchant_trans_id,
        amount,
    ):
        return ClickVerificationResult(
            verified=True,
            click_trans_id=click_trans_id,
            merchant_trans_id=merchant_trans_id,
            amount=Decimal(str(amount)),
        )

    with patch(
        "apps.payments.click_services."
        "verify_click_payment_with_provider",
        side_effect=fake_verify,
    ):
        yield

import pytest

from django.utils import timezone
from apps.competitions.models import TicketOrder


@pytest.fixture
def paid_click_order(click_order):
    click_order.status = TicketOrder.Status.PAID
    click_order.paid_at = timezone.now()
    click_order.provider_transaction_id = (
        f"test-click-{click_order.pk}"
    )

    click_order.save(
        update_fields=[
            "status",
            "paid_at",
            "provider_transaction_id",
        ]
    )

    return click_order

@pytest.fixture(autouse=True)
def disable_ssl_redirect_for_tests(settings):
    """
    Test so'rovlarining HTTP -> HTTPS redirect
    bo'lishini oldini oladi.

    Production HTTPS sozlamalariga ta'sir qilmaydi.
    """
    settings.SECURE_SSL_REDIRECT = False
