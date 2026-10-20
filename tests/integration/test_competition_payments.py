
import uuid
from datetime import timedelta
from unittest.mock import patch

import pytest
from apps.payments.exceptions import (
    PaymentOrderUnavailable,
    PaymentTransactionConflict,
)
from django.utils import timezone

from apps.competitions.models import Ticket, TicketOrder
from apps.competitions.services import create_ticket_order
from apps.finance.models import RevenueEntry
from apps.finance.payment_settlement import settle_competition_payment

from tests.integration.test_competition_orders import (
    competition_user,
    competition,
    order_data,
)


@pytest.mark.django_db
def test_successful_competition_payment(order_data):
    order = create_ticket_order(**order_data)

    paid_order = settle_competition_payment(
        order_id=order.pk,
        provider="click",
        provider_transaction_id="competition-payment-001",
    )

    paid_order.refresh_from_db()

    assert paid_order.status == TicketOrder.Status.PAID
    assert paid_order.paid_at is not None
    assert paid_order.provider_transaction_id == "competition-payment-001"

    assert Ticket.objects.filter(order=paid_order).count() == 2


@pytest.mark.django_db
def test_payment_creates_unique_tickets(order_data):
    order = create_ticket_order(**order_data)

    settle_competition_payment(
        order_id=order.pk,
        provider="click",
        provider_transaction_id="competition-payment-002",
    )

    tickets = list(Ticket.objects.filter(order=order))

    assert len(tickets) == order.quantity

    ticket_numbers = {ticket.ticket_number for ticket in tickets}

    assert len(ticket_numbers) == order.quantity


@pytest.mark.django_db
def test_duplicate_payment_callback_is_idempotent(order_data):
    order = create_ticket_order(**order_data)

    kwargs = {
        "order_id": order.pk,
        "provider": "click",
        "provider_transaction_id": "competition-payment-003",
    }

    first = settle_competition_payment(**kwargs)
    second = settle_competition_payment(**kwargs)

    assert first.pk == second.pk

    assert Ticket.objects.filter(order=order).count() == order.quantity

    assert RevenueEntry.objects.filter(
        source="competition_ticket_order",
        source_payment_id=str(order.pk),
        entry_type=RevenueEntry.EntryType.PAYMENT,
    ).count() == 1



@pytest.mark.django_db
def test_different_transaction_id_rejected(order_data):
    order = create_ticket_order(**order_data)

    settle_competition_payment(
        order_id=order.pk,
        provider="click",
        provider_transaction_id="competition-payment-004",
    )

    with pytest.raises(PaymentTransactionConflict):
        settle_competition_payment(
            order_id=order.pk,
            provider="click",
            provider_transaction_id="competition-payment-005",
        )

    order.refresh_from_db()

    assert order.status == TicketOrder.Status.PAID
    assert Ticket.objects.filter(order=order).count() == order.quantity


@pytest.mark.django_db
def test_wrong_provider_rejected(order_data):
    order = create_ticket_order(**order_data)

    with pytest.raises(PaymentTransactionConflict):
        settle_competition_payment(
            order_id=order.pk,
            provider="payme",
            provider_transaction_id="competition-payment-006",
        )

    order.refresh_from_db()

    assert order.status == TicketOrder.Status.PENDING
    assert Ticket.objects.filter(order=order).count() == 0


@pytest.mark.django_db
def test_expired_competition_payment_rejected(order_data):
    order = create_ticket_order(**order_data)

    TicketOrder.objects.filter(pk=order.pk).update(
        payment_expires_at=timezone.now() - timedelta(minutes=1)
    )

    with pytest.raises(PaymentOrderUnavailable):
        settle_competition_payment(
            order_id=order.pk,
            provider="click",
            provider_transaction_id="competition-payment-007",
        )

    order.refresh_from_db()

    assert order.status == TicketOrder.Status.PENDING
    assert Ticket.objects.filter(order=order).count() == 0

@pytest.mark.django_db
def test_payment_finance_record_created(order_data):
    order = create_ticket_order(**order_data)

    settle_competition_payment(
        order_id=order.pk,
        provider="click",
        provider_transaction_id="competition-payment-008",
    )

    entries = RevenueEntry.objects.filter(
        source="competition_ticket_order",
        source_payment_id=str(order.pk),
        entry_type=RevenueEntry.EntryType.PAYMENT,
    )

    assert entries.count() == 1
    assert entries.first().amount == order.total_amount


@pytest.mark.django_db
def test_payment_rolls_back_when_finance_fails(order_data):
    order = create_ticket_order(**order_data)

    with patch(
        "apps.finance.payment_settlement.record_successful_payment",
        side_effect=RuntimeError("Finance failure"),
    ):
        with pytest.raises(RuntimeError):
            settle_competition_payment(
                order_id=order.pk,
                provider="click",
                provider_transaction_id="competition-payment-009",
            )

    order.refresh_from_db()

    assert order.status == TicketOrder.Status.PENDING
    assert order.paid_at is None
    assert order.provider_transaction_id is None

    assert Ticket.objects.filter(order=order).count() == 0

    assert RevenueEntry.objects.filter(
        source_payment_id=str(order.pk),
    ).count() == 0
