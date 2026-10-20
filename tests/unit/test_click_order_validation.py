
from unittest.mock import patch

import pytest

from django.core.exceptions import ValidationError
from django.db import DataError

from apps.competitions.models import TicketOrder

from apps.payments.click_orders import (
    get_click_order,
    find_click_order,
)
from apps.payments.security import PaymentVerificationError


@pytest.mark.parametrize(
    "merchant_trans_id",
    [
        "",
        "competition",
        "competition:",
        "unknown:123",
        None,
    ],
)
def test_invalid_merchant_trans_id_rejected(
    merchant_trans_id,
):
    with pytest.raises(PaymentVerificationError):
        get_click_order(merchant_trans_id)


@pytest.mark.parametrize(
    "exception",
    [
        ValueError("invalid ID"),
        TypeError("invalid ID type"),
        ValidationError("invalid UUID"),
        DataError("invalid database value"),
    ],
)
def test_invalid_pk_errors_are_normalized(exception):
    with patch(
        "apps.payments.click_orders.TicketOrder.objects.filter",
        side_effect=exception,
    ):
        with pytest.raises(PaymentVerificationError):
            find_click_order(TicketOrder, "invalid-id")
