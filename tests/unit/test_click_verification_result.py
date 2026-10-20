
from decimal import Decimal

import pytest

from apps.payments.click_verification import (
    ClickVerificationError,
    ClickVerificationResult,
    validate_click_verification_result,
)


@pytest.fixture
def valid_result():
    return ClickVerificationResult(
        verified=True,
        click_trans_id="12345",
        merchant_trans_id="competition:10",
        amount=Decimal("50000.00"),
    )


def validate(result):
    validate_click_verification_result(
        result=result,
        click_trans_id="12345",
        merchant_trans_id="competition:10",
        amount=Decimal("50000.00"),
    )


def test_valid_provider_response(valid_result):
    validate(valid_result)


@pytest.mark.parametrize(
    "field,value",
    [
        ("verified", False),
        ("verified", 1),
        ("click_trans_id", "99999"),
        ("merchant_trans_id", "competition:99"),
        ("amount", Decimal("10000.00")),
        ("amount", Decimal("NaN")),
        ("amount", Decimal("Infinity")),
        ("amount", True),
        ("amount", 50000.0),
    ],
)
def test_invalid_provider_response_is_rejected(
    valid_result,
    field,
    value,
):
    data = {
        "verified": valid_result.verified,
        "click_trans_id": valid_result.click_trans_id,
        "merchant_trans_id": valid_result.merchant_trans_id,
        "amount": valid_result.amount,
    }

    data[field] = value

    result = ClickVerificationResult(**data)

    with pytest.raises(ClickVerificationError):
        validate(result)


def test_invalid_result_type_is_rejected():
    with pytest.raises(ClickVerificationError):
        validate({"verified": True})
