
from decimal import Decimal

import pytest

from apps.payments.security import (
    PaymentVerificationError,
    normalize_amount,
    require_live_payments,
    secure_compare,
    verify_order_amount,
)


def test_live_payments_disabled(settings):
    settings.PAYMENT_MODE = "disabled"

    with pytest.raises(PaymentVerificationError):
        require_live_payments()


def test_secure_compare_valid():
    assert secure_compare(
        "correct-signature",
        "correct-signature",
    ) is True


def test_secure_compare_invalid():
    assert secure_compare(
        "wrong-signature",
        "correct-signature",
    ) is False


@pytest.mark.parametrize(
    "amount",
    [
        -100,
        0,
        "NaN",
        "Infinity",
        "-Infinity",
        "100.001",
        "invalid",
        None,
        100.50,
    ],
)
def test_invalid_amount_rejected(amount):
    with pytest.raises(PaymentVerificationError):
        normalize_amount(amount)


def test_valid_decimal_amount():
    amount = normalize_amount("50000.00")

    assert amount == Decimal("50000.00")


def test_correct_order_amount():
    result = verify_order_amount(
        expected_amount=Decimal("100000.00"),
        received_amount="100000.00",
    )

    assert result == Decimal("100000.00")


def test_wrong_order_amount_rejected():
    with pytest.raises(PaymentVerificationError):
        verify_order_amount(
            expected_amount=Decimal("100000.00"),
            received_amount="1000.00",
        )


def test_amount_with_one_decimal_place():
    result = normalize_amount("50000.5")

    assert result == Decimal("50000.50")
