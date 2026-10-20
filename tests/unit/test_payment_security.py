
from decimal import Decimal

import pytest

from apps.payments.security import (
    normalize_amount,
    verify_order_amount,
    secure_compare,
    get_provider_credentials,
    PaymentVerificationError,
)


@pytest.mark.parametrize(
    "value, expected",
    [
        ("100000", Decimal("100000")),
        ("150000.50", Decimal("150000.50")),
        (1000, Decimal("1000")),
        ("0.01", Decimal("0.01")),
    ],
)
def test_valid_payment_amount(value, expected):
    assert normalize_amount(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        "0",
        "-100",
        "abc",
        "",
        None,
        "NaN",
        "Infinity",
        "100.001",
        100.50,
    ],
)
def test_invalid_payment_amount(value):
    with pytest.raises(PaymentVerificationError):
        normalize_amount(value)


def test_correct_order_amount():
    result = verify_order_amount(
        expected_amount="150000.00",
        received_amount="150000",
    )

    assert result == Decimal("150000.00")


def test_incorrect_order_amount():
    with pytest.raises(PaymentVerificationError):
        verify_order_amount(
            expected_amount="150000",
            received_amount="149000",
        )


def test_secure_compare():
    assert secure_compare("abc123", "abc123") is True
    assert secure_compare("abc123", "wrong") is False


@pytest.mark.django_db
def test_live_payments_disabled(settings):
    settings.PAYMENT_MODE = "disabled"

    with pytest.raises(PaymentVerificationError):
        get_provider_credentials("click")
