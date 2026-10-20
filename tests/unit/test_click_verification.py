
from decimal import Decimal

import pytest

from apps.payments.click_verification import (
    ClickVerificationUnavailable,
    verify_click_payment_with_provider,
)


def test_click_verification_fails_closed():
    with pytest.raises(ClickVerificationUnavailable):
        verify_click_payment_with_provider(
            click_trans_id="12345",
            merchant_trans_id="competition:10",
            amount=Decimal("50000.00"),
        )
