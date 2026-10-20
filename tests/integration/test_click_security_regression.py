
import pytest

from apps.competitions.models import Ticket, TicketOrder
from apps.finance.models import RevenueEntry
from apps.payments.models import ClickTransaction
import uuid

from apps.competitions.models import TicketOrder
from apps.competitions.services import create_ticket_order
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
def test_disabled_payments_reject_prepare(
    client, click_order, settings
):
    settings.PAYMENT_MODE = "disabled"

    response = post_prepare(
        client,
        make_payload(click_order),
    )

    assert response.status_code == 200
    assert response.json()["error"] == -1
    assert ClickTransaction.objects.count() == 0


@pytest.mark.django_db
def test_missing_complete_error_rejected(
    client, click_order
):
    prepare = make_payload(click_order)
    prepared = post_prepare(client, prepare)

    assert prepared.json()["error"] == 0

    complete = make_payload(
        click_order,
        action="1",
        click_trans_id=prepare["click_trans_id"],
        prepare_id=prepared.json()["merchant_prepare_id"],
    )

    del complete["error"]

    response = post_complete(client, complete)

    assert response.json()["error"] == -1

    assert ClickTransaction.objects.get().status == (
        ClickTransaction.Status.PREPARED
    )


@pytest.mark.django_db
def test_complete_with_wrong_transaction_id_rejected(
    client, click_order
):
    prepare = make_payload(click_order)
    prepared = post_prepare(client, prepare)

    assert prepared.json()["error"] == 0

    complete = make_payload(
        click_order,
        action="1",
        click_trans_id="unknown-transaction",
        prepare_id=prepared.json()["merchant_prepare_id"],
    )

    response = post_complete(client, complete)

    assert response.json()["error"] == -6

    click_order.refresh_from_db()
    assert click_order.status == TicketOrder.Status.PENDING


@pytest.mark.django_db
def test_complete_with_modified_amount_rejected(
    client, click_order
):
    prepare = make_payload(click_order)
    prepared = post_prepare(client, prepare)

    assert prepared.json()["error"] == 0

    complete = make_payload(
        click_order,
        action="1",
        click_trans_id=prepare["click_trans_id"],
        prepare_id=prepared.json()["merchant_prepare_id"],
        amount="100.00",
    )

    response = post_complete(client, complete)

    assert response.json()["error"] == -2

    click_order.refresh_from_db()
    assert click_order.status == TicketOrder.Status.PENDING


@pytest.mark.django_db
def test_prepare_cannot_use_wrong_provider(
    client,
    order_data,
    click_settings,
):
    """
    PAYME uchun yaratilgan buyurtmani
    CLICK orqali to'lashga urinish rad etilishi kerak.
    """

    data = {
        **order_data,
        "provider": TicketOrder.Provider.PAYME,
        "idempotency_key": uuid.uuid4(),
    }

    payme_order = create_ticket_order(**data)

    assert payme_order.provider == TicketOrder.Provider.PAYME
    assert payme_order.status == TicketOrder.Status.PENDING

    payload = make_payload(payme_order)

    response = post_prepare(client, payload)

    assert response.status_code == 200
    assert response.json()["error"] != 0

    payme_order.refresh_from_db()

    assert payme_order.provider == TicketOrder.Provider.PAYME
    assert payme_order.status == TicketOrder.Status.PENDING


@pytest.mark.django_db
def test_failed_complete_cannot_create_tickets(
    client, click_order
):
    prepare = make_payload(click_order)
    prepared = post_prepare(client, prepare)

    assert prepared.json()["error"] == 0

    complete = make_payload(
        click_order,
        action="1",
        click_trans_id=prepare["click_trans_id"],
        prepare_id=prepared.json()["merchant_prepare_id"],
        error="-1",
    )

    post_complete(client, complete)

    click_order.refresh_from_db()

    assert click_order.status == TicketOrder.Status.PENDING

    assert Ticket.objects.filter(
        order=click_order
    ).count() == 0

    assert RevenueEntry.objects.filter(
        source_payment_id=str(click_order.pk)
    ).count() == 0
