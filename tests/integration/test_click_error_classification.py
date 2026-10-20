
import pytest

from apps.payments.exceptions import (
    PaymentSettlementError,
    PaymentOrderUnavailable,
    PaymentTransactionConflict,
    PaymentTemporaryFailure,
)


def test_order_unavailable_is_not_retryable():
    error = PaymentOrderUnavailable()

    assert isinstance(error, PaymentSettlementError)
    assert error.retryable is False


def test_transaction_conflict_is_not_retryable():
    error = PaymentTransactionConflict()

    assert isinstance(error, PaymentSettlementError)
    assert error.retryable is False


def test_temporary_failure_is_retryable():
    error = PaymentTemporaryFailure()

    assert isinstance(error, PaymentSettlementError)
    assert error.retryable is True


def test_base_settlement_error_default_is_not_retryable():
    error = PaymentSettlementError("Settlement failed")

    assert error.retryable is False


def test_custom_retryable_settlement_error():
    error = PaymentSettlementError(
        "Temporary database failure",
        retryable=True,
    )

    assert error.retryable is True
