
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


@pytest.fixture
def prepared_click(client, click_order):
    prepare_data = make_payload(click_order)
    response = post_prepare(client, prepare_data)

    assert response.status_code == 200
    assert response.json()["error"] == 0

    return {
        "order": click_order,
        "transaction_id": prepare_data["click_trans_id"],
        "prepare_id": response.json()["merchant_prepare_id"],
    }


@pytest.mark.django_db
def test_cancelled_complete_keeps_order_unpaid(
    client,
    prepared_click,
):
    order = prepared_click["order"]

    payload = make_payload(
        order,
        action="1",
        click_trans_id=prepared_click["transaction_id"],
        prepare_id=prepared_click["prepare_id"],
        error="-1",
    )

    response = post_complete(client, payload)

    order.refresh_from_db()
    tx = ClickTransaction.objects.get()

    assert response.status_code == 200
    assert tx.status == ClickTransaction.Status.CANCELLED
    assert order.status == TicketOrder.Status.PENDING


@pytest.mark.django_db
def test_cancelled_transaction_rejects_later_success(
    client,
    prepared_click,
):
    order = prepared_click["order"]

    cancelled = make_payload(
        order,
        action="1",
        click_trans_id=prepared_click["transaction_id"],
        prepare_id=prepared_click["prepare_id"],
        error="-1",
    )

    post_complete(client, cancelled)

    success = make_payload(
        order,
        action="1",
        click_trans_id=prepared_click["transaction_id"],
        prepare_id=prepared_click["prepare_id"],
        error="0",
    )

    response = post_complete(client, success)

    assert response.json()["error"] == -9

    order.refresh_from_db()
    assert order.status == TicketOrder.Status.PENDING



@pytest.mark.django_db
def test_cancelled_complete_is_acknowledged_without_settlement(
    client,
    prepared_click,
):
    order = prepared_click["order"]

    payload = make_payload(
        order,
        action="1",
        click_trans_id=prepared_click["transaction_id"],
        prepare_id=prepared_click["prepare_id"],
        error="-1",
    )

    response = post_complete(client, payload)

    assert response.status_code == 200

    body = response.json()

    # Server cancellation callbackni qayta ishlagan.
    # Bu provider tomonidan to'lov amalga oshganini
    # anglatmaydi.
    assert body["error"] == 0
    assert body["click_trans_id"] == (
        prepared_click["transaction_id"]
    )
    assert str(body["merchant_confirm_id"]) == str(
        prepared_click["prepare_id"]
    )

    tx = ClickTransaction.objects.get(
        click_trans_id=prepared_click["transaction_id"]
    )

    order.refresh_from_db()

    assert tx.status == ClickTransaction.Status.CANCELLED
    assert order.status == TicketOrder.Status.PENDING
