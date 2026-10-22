
import hashlib
import uuid

import pytest
from django.urls import reverse

from apps.competitions.models import Ticket, TicketOrder
from apps.competitions.services import create_ticket_order
from apps.finance.models import RevenueEntry
from apps.payments.models import ClickTransaction

from tests.integration.test_competition_orders import (
    competition_user,
    competition,
    order_data,
)


@pytest.fixture
def click_settings(settings):
    settings.PAYMENT_MODE = "live"
    settings.CLICK_MERCHANT_ID = "test-merchant"
    settings.CLICK_SERVICE_ID = "12345"
    settings.CLICK_SECRET_KEY = "test-secret-key"
    return settings


@pytest.fixture
def click_order(order_data, click_settings):
    return create_ticket_order(**order_data)


def make_payload(
    order,
    *,
    action="0",
    click_trans_id=None,
    prepare_id=None,
    error="0",
    amount=None,
):
    data = {
        "click_trans_id": click_trans_id or str(uuid.uuid4()),
        "service_id": "12345",
        "merchant_trans_id": f"competition:{order.pk}",
        "amount": str(
            amount if amount is not None else order.total_amount
        ),
        "action": action,
        "sign_time": "2026-10-14 10:00:00",
    }

    if action == "1":
        data["merchant_prepare_id"] = str(prepare_id)
        data["error"] = error

    parts = [
        data["click_trans_id"],
        data["service_id"],
        "test-secret-key",
        data["merchant_trans_id"],
    ]

    if action == "1":
        parts.append(data["merchant_prepare_id"])

    parts.extend([
        data["amount"],
        data["action"],
        data["sign_time"],
    ])

    data["sign_string"] = hashlib.md5(
        "".join(parts).encode("utf-8")
    ).hexdigest()

    return data


def post_prepare(client, data):
    return client.post(
        reverse("click-prepare"),
        data=data,
    )


def post_complete(client, data):
    return client.post(
        reverse("click-complete"),
        data=data,
    )


@pytest.mark.django_db
def test_prepare_creates_transaction(client, click_order):
    data = make_payload(click_order)

    response = post_prepare(client, data)

    assert response.status_code == 200
    assert response.json()["error"] == 0

    assert ClickTransaction.objects.count() == 1

    tx = ClickTransaction.objects.get()

    assert tx.status == ClickTransaction.Status.PREPARED
    assert tx.order_id == str(click_order.pk)


@pytest.mark.django_db
def test_duplicate_prepare_returns_same_id(client, click_order):
    data = make_payload(click_order)

    first = post_prepare(client, data)
    second = post_prepare(client, data)

    assert first.json()["error"] == 0
    assert second.json()["error"] == 0

    assert (
        first.json()["merchant_prepare_id"]
        == second.json()["merchant_prepare_id"]
    )

    assert ClickTransaction.objects.count() == 1


@pytest.mark.django_db
def test_invalid_signature_does_not_create_transaction(
    client,
    click_order,
):
    data = make_payload(click_order)
    data["sign_string"] = "invalid"

    response = post_prepare(client, data)

    assert response.json()["error"] == -1
    assert ClickTransaction.objects.count() == 0


@pytest.mark.django_db
def test_wrong_amount_does_not_create_transaction(
    client,
    click_order,
):
    data = make_payload(click_order, amount="1000.00")

    response = post_prepare(client, data)

    assert response.json()["error"] == -2
    assert ClickTransaction.objects.count() == 0


@pytest.mark.django_db
def test_complete_creates_tickets_and_revenue(
    client,
    click_order,
    verified_click_provider,
):
    prepare_data = make_payload(click_order)
    prepare_response = post_prepare(client, prepare_data)

    assert prepare_response.json()["error"] == 0

    prepare_id = prepare_response.json()["merchant_prepare_id"]

    complete_data = make_payload(
        click_order,
        action="1",
        click_trans_id=prepare_data["click_trans_id"],
        prepare_id=prepare_id,
    )

    complete_response = post_complete(client, complete_data)

    assert complete_response.status_code == 200
    assert complete_response.json()["error"] == 0

    click_order.refresh_from_db()

    assert click_order.status == TicketOrder.Status.PAID

    assert Ticket.objects.filter(
        order=click_order
    ).count() == click_order.quantity

    assert RevenueEntry.objects.filter(
        source="competition_ticket_order",
        source_payment_id=str(click_order.pk),
        entry_type=RevenueEntry.EntryType.PAYMENT,
    ).count() == 1

    tx = ClickTransaction.objects.get()
    assert tx.status == ClickTransaction.Status.COMPLETED


@pytest.mark.django_db
def test_duplicate_complete_does_not_duplicate_finance(
    client,
    click_order,
    verified_click_provider,
):
    prepare_data = make_payload(click_order)
    prepare_response = post_prepare(client, prepare_data)

    prepare_id = prepare_response.json()["merchant_prepare_id"]

    complete_data = make_payload(
        click_order,
        action="1",
        click_trans_id=prepare_data["click_trans_id"],
        prepare_id=prepare_id,
    )

    first = post_complete(client, complete_data)
    second = post_complete(client, complete_data)

    assert first.json()["error"] == 0
    assert second.json()["error"] == 0

    assert Ticket.objects.filter(
        order=click_order
    ).count() == click_order.quantity

    assert RevenueEntry.objects.filter(
        source_payment_id=str(click_order.pk),
        entry_type=RevenueEntry.EntryType.PAYMENT,
    ).count() == 1


@pytest.mark.django_db
def test_wrong_prepare_id_rejected(client, click_order):
    prepare_data = make_payload(click_order)
    prepare_response = post_prepare(client, prepare_data)

    assert prepare_response.json()["error"] == 0

    complete_data = make_payload(
        click_order,
        action="1",
        click_trans_id=prepare_data["click_trans_id"],
        prepare_id="999999999",
    )

    response = post_complete(client, complete_data)

    assert response.json()["error"] == -4

    click_order.refresh_from_db()
    assert click_order.status == TicketOrder.Status.PENDING

    assert Ticket.objects.filter(order=click_order).count() == 0


@pytest.mark.django_db
def test_cancelled_complete_does_not_settle(
    client,
    click_order,
):
    prepare_data = make_payload(click_order)
    prepare_response = post_prepare(client, prepare_data)

    prepare_id = prepare_response.json()["merchant_prepare_id"]

    complete_data = make_payload(
        click_order,
        action="1",
        click_trans_id=prepare_data["click_trans_id"],
        prepare_id=prepare_id,
        error="-1",
    )

    post_complete(client, complete_data)

    tx = ClickTransaction.objects.get()
    click_order.refresh_from_db()

    assert tx.status == ClickTransaction.Status.CANCELLED
    assert click_order.status == TicketOrder.Status.PENDING

    assert Ticket.objects.filter(order=click_order).count() == 0

    assert RevenueEntry.objects.filter(
        source_payment_id=str(click_order.pk)
    ).count() == 0
