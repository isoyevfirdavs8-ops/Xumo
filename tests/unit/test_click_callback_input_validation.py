
import pytest

from apps.payments.click_security import (
    validate_click_identifier,
    validate_click_prepare_id,
    validate_click_amount,
    validate_click_error,
)

from apps.payments.security import PaymentVerificationError


@pytest.mark.parametrize(
    "value",
    [
        "",
        " ",
        " abc",
        "abc ",
        "abc def",
        "a" * 101,
        None,
        True,
    ],
)
def test_invalid_click_identifier(value):
    with pytest.raises(PaymentVerificationError):
        validate_click_identifier(
            value,
            field_name="click_trans_id",
            max_length=100,
        )


@pytest.mark.parametrize(
    "value",
    [
        "",
        "abc",
        "0",
        "-1",
        "1.5",
        " 25",
        "25 ",
        True,
        "9223372036854775808",
    ],
)
def test_invalid_prepare_id(value):
    with pytest.raises(PaymentVerificationError):
        validate_click_prepare_id(value)


@pytest.mark.parametrize(
    "value",
    [
        "",
        "NaN",
        "Infinity",
        "-100",
        "0",
        "10.123",
        "abc",
        True,
        10.5,
    ],
)
def test_invalid_amount(value):
    with pytest.raises(PaymentVerificationError):
        validate_click_amount(value)


@pytest.mark.parametrize(
    "value",
    [
        "",
        "abc",
        "1.5",
        " 0",
        "0 ",
        True,
    ],
)
def test_invalid_error(value):
    with pytest.raises(PaymentVerificationError):
        validate_click_error(value)


def test_valid_callback_values():
    assert validate_click_identifier(
        "123456",
        field_name="click_trans_id",
        max_length=100,
    ) == "123456"

    assert validate_click_prepare_id("25") == "25"

    assert str(validate_click_amount("50000.00")) == "50000.00"

    assert validate_click_error("-1") == "-1"
