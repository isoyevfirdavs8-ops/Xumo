
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.competitions.models import Ticket, TicketOrder
from apps.finance.models import RevenueEntry
from apps.payments.models import ClickTransaction

from tests.integration.test_click_http_integration import (
    click_order,
    click_settings,
    make_payload,
    post_prepare,
    post_complete,
)
from tests.integration.test_competition_orders import (
    competition_user,
    competition,
    order_data,
)

@pytest.mark.django_db
def test_expired_order_prepare_rejected(client, click_order):
    TicketOrder.objects.filter(pk=click_order.pk).update(
        payment_expires_at=timezone.now() - timedelta(seconds=1)
    )

    response = post_prepare(
        client,
        make_payload(click_order),
    )

    assert response.status_code == 200
    assert response.json()["error"] == -9
    assert ClickTransaction.objects.count() == 0


@pytest.mark.django_db
def test_expired_order_complete_rejected(client, click_order):
    prepare = make_payload(click_order)
    prepared = post_prepare(client, prepare)

    assert prepared.json()["error"] == 0

    TicketOrder.objects.filter(pk=click_order.pk).update(
        payment_expires_at=timezone.now() - timedelta(seconds=1)
    )

    complete = make_payload(
        click_order,
        action="1",
        click_trans_id=prepare["click_trans_id"],
        prepare_id=prepared.json()["merchant_prepare_id"],
    )

    response = post_complete(client, complete)

    assert response.json()["error"] == -9

    click_order.refresh_from_db()

    assert click_order.status == TicketOrder.Status.PENDING
    assert Ticket.objects.filter(order=click_order).count() == 0
    assert RevenueEntry.objects.filter(
        source_payment_id=str(click_order.pk)
    ).count() == 0

    assert ClickTransaction.objects.get().status == (
        ClickTransaction.Status.PREPARED
    )


@pytest.mark.django_db
def test_cancelled_transaction_cannot_be_completed(
    client,
    click_order,
):
    prepare = make_payload(click_order)
    prepared = post_prepare(client, prepare)

    prepare_id = prepared.json()["merchant_prepare_id"]

    cancellation = make_payload(
        click_order,
        action="1",
        click_trans_id=prepare["click_trans_id"],
        prepare_id=prepare_id,
        error="-1",
    )

    post_complete(client, cancellation)

    successful_complete = make_payload(
        click_order,
        action="1",
        click_trans_id=prepare["click_trans_id"],
        prepare_id=prepare_id,
        error="0",
    )

    response = post_complete(client, successful_complete)

    assert response.json()["error"] == -9

    click_order.refresh_from_db()

    assert click_order.status == TicketOrder.Status.PENDING
    assert Ticket.objects.filter(order=click_order).count() == 0
    assert RevenueEntry.objects.filter(
        source_payment_id=str(click_order.pk)
    ).count() == 0


@pytest.mark.django_db
def test_different_transaction_cannot_replace_active_prepare(
    client,
    click_order,
):
    first = make_payload(click_order)
    second = make_payload(click_order)

    response1 = post_prepare(client, first)
    response2 = post_prepare(client, second)

    assert response1.json()["error"] == 0
    assert response2.json()["error"] == -4

    assert ClickTransaction.objects.count() == 1


@pytest.mark.django_db
def test_reused_transaction_id_for_other_order_rejected(
    client,
    click_order,
    order_data,
):
    from apps.competitions.services import create_ticket_order

    first = make_payload(click_order)
    response1 = post_prepare(client, first)

    assert response1.json()["error"] == 0

    second_data = {
        **order_data,
        "idempotency_key": __import__("uuid").uuid4(),
    }

    second_order = create_ticket_order(**second_data)

    replay = make_payload(
        second_order,
        click_trans_id=first["click_trans_id"],
    )

    response2 = post_prepare(client, replay)

    assert response2.json()["error"] == -4
    assert ClickTransaction.objects.count() == 1


@pytest.mark.django_db
def test_settlement_failure_rolls_back_click_transaction(
    client,
    click_order,
verified_click_provider
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

    with patch(
        "apps.payments.click_services.settle_competition_payment",
        side_effect=RuntimeError("Settlement failure"),
    ):
        with pytest.raises(RuntimeError):
            post_complete(client, complete)

    tx = ClickTransaction.objects.get()
    click_order.refresh_from_db()

    assert tx.status == ClickTransaction.Status.PREPARED
    assert click_order.status == TicketOrder.Status.PENDING

    assert Ticket.objects.filter(order=click_order).count() == 0
    assert RevenueEntry.objects.filter(
        source_payment_id=str(click_order.pk)
    ).count() == 0


@pytest.mark.django_db
def test_completed_transaction_cannot_be_cancelled(
    client,
    click_order,
verified_click_provider
):
    prepare = make_payload(click_order)
    prepared = post_prepare(client, prepare)

    prepare_id = prepared.json()["merchant_prepare_id"]

    success = make_payload(
        click_order,
        action="1",
        click_trans_id=prepare["click_trans_id"],
        prepare_id=prepare_id,
        error="0",
    )

    successful_response = post_complete(client, success)

    assert successful_response.json()["error"] == 0

    cancellation = make_payload(
        click_order,
        action="1",
        click_trans_id=prepare["click_trans_id"],
        prepare_id=prepare_id,
        error="-1",
    )

    response = post_complete(client, cancellation)

    assert response.json()["error"] == -9

    tx = ClickTransaction.objects.get()
    click_order.refresh_from_db()

    assert tx.status == ClickTransaction.Status.COMPLETED
    assert click_order.status == TicketOrder.Status.PAID

    assert Ticket.objects.filter(
        order=click_order
    ).count() == click_order.quantity

    assert RevenueEntry.objects.filter(
        source_payment_id=str(click_order.pk)
    ).count() == 1
