
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


@pytest.mark.django_db
def test_cancelled_complete_response_is_not_success(
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
        error="-1",
    )

    response = post_complete(client, complete_data)

    tx = ClickTransaction.objects.get()
    click_order.refresh_from_db()

    assert tx.status == ClickTransaction.Status.CANCELLED
    assert click_order.status == TicketOrder.Status.PENDING

    # Cancellation javobini Click rasmiy protokoli
    # bilan solishtirib tasdiqlashimiz kerak.
    assert response.status_code == 200
    assert "error" in response.json()
    assert "error_note" in response.json()


@pytest.mark.django_db
def test_complete_response_contains_transaction_identifiers(
    client,
    click_order,
    verified_click_provider,
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

    response = post_complete(client, complete_data)

    assert response.status_code == 200
    assert response.json()["error"] == 0
    assert response.json()["click_trans_id"] == (
        prepare_data["click_trans_id"]
    )
    assert response.json()["merchant_trans_id"] == (
        prepare_data["merchant_trans_id"]
    )
    assert str(response.json()["merchant_confirm_id"]) == str(
        prepare_response.json()["merchant_prepare_id"]
    )
