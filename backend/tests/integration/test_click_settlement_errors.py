
from unittest.mock import patch

import pytest

from apps.competitions.models import TicketOrder
from apps.payments.models import ClickTransaction

from tests.integration.test_competition_orders import (
    competition_user,
    competition,
    order_data,
)
from tests.integration.test_click_http_integration import (
    click_settings,
    click_order,
    make_payload,
    post_prepare,
    post_complete,
)
from apps.payments.exceptions import PaymentSettlementError

@pytest.mark.django_db
def test_settlement_value_error_returns_safe_response(
    client,
    click_order,
):
    prepare_data = make_payload(click_order)
    prepare_response = post_prepare(client, prepare_data)

    assert prepare_response.json()["error"] == 0

    complete_data = make_payload(
        click_order,
        action="1",
        click_trans_id=prepare_data["click_trans_id"],
        prepare_id=prepare_response.json()["merchant_prepare_id"],
    )

    with patch(
        "apps.payments.click_services.settle_competition_payment",
        side_effect=PaymentSettlementError(),
    ):
        response = post_complete(client, complete_data)

    assert response.status_code == 200
    assert response.json()["error"] == -9
    assert "Internal settlement details" not in (
        response.json()["error_note"]
    )

    click_order.refresh_from_db()

    assert click_order.status == TicketOrder.Status.PENDING
    assert ClickTransaction.objects.get().status == (
        ClickTransaction.Status.PREPARED
    )
