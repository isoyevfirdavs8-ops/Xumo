
import uuid
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone
from apps.payments.exceptions import (
    PaymentOrderUnavailable,
    PaymentTransactionConflict,
)
from apps.competitions.models import Ticket, TicketOrder
from apps.competitions.services import (
    create_ticket_order,
    expire_ticket_order,
    issue_tickets_for_paid_order,
)
from apps.finance.models import RevenueEntry
from apps.finance.payment_settlement import (
    settle_competition_payment,
)

from tests.integration.test_competition_orders import (
    competition_user,
    competition,
    order_data,
)


def settle(order, transaction_id=None):
    return settle_competition_payment(
        order_id=order.pk,
        provider="click",
        provider_transaction_id=transaction_id or f"test-{uuid.uuid4()}",
    )


@pytest.mark.django_db
def test_ticket_creation_failure_rolls_back(order_data):
    order = create_ticket_order(**order_data)

    with patch(
        "apps.finance.payment_settlement.issue_tickets_for_paid_order",
        side_effect=RuntimeError("Ticket creation failure"),
    ):
        with pytest.raises(RuntimeError):
            settle(order)

    order.refresh_from_db()

    assert order.status == TicketOrder.Status.PENDING
    assert order.paid_at is None
    assert order.provider_transaction_id is None
    assert Ticket.objects.filter(order=order).count() == 0
    assert RevenueEntry.objects.filter(
        source_payment_id=str(order.pk)
    ).count() == 0


@pytest.mark.django_db
def test_finance_failure_rolls_back_tickets(order_data):
    order = create_ticket_order(**order_data)

    with patch(
        "apps.finance.payment_settlement.record_successful_payment",
        side_effect=RuntimeError("Finance failure"),
    ):
        with pytest.raises(RuntimeError):
            settle(order)

    order.refresh_from_db()

    assert order.status == TicketOrder.Status.PENDING
    assert order.paid_at is None
    assert order.provider_transaction_id is None
    assert Ticket.objects.filter(order=order).count() == 0
    assert RevenueEntry.objects.filter(
        source_payment_id=str(order.pk)
    ).count() == 0


@pytest.mark.django_db
def test_payment_retry_after_rollback(order_data):
    order = create_ticket_order(**order_data)
    transaction_id = f"retry-{uuid.uuid4()}"

    with patch(
        "apps.finance.payment_settlement.record_successful_payment",
        side_effect=RuntimeError("Temporary finance failure"),
    ):
        with pytest.raises(RuntimeError):
            settle(order, transaction_id)

    paid_order = settle(order, transaction_id)

    assert paid_order.status == TicketOrder.Status.PAID
    assert Ticket.objects.filter(order=order).count() == order.quantity

    assert RevenueEntry.objects.filter(
        source_payment_id=str(order.pk),
        entry_type=RevenueEntry.EntryType.PAYMENT,
    ).count() == 1


@pytest.mark.django_db
def test_expired_order_cannot_be_paid(order_data):
    order = create_ticket_order(**order_data)

    TicketOrder.objects.filter(pk=order.pk).update(
        payment_expires_at=timezone.now() - timedelta(seconds=1)
    )

    with pytest.raises(PaymentOrderUnavailable):
        settle(order)

    order.refresh_from_db()

    assert order.status == TicketOrder.Status.PENDING
    assert Ticket.objects.filter(order=order).count() == 0


@pytest.mark.django_db
def test_cancelled_order_cannot_be_paid(order_data):
    order = create_ticket_order(**order_data)

    TicketOrder.objects.filter(pk=order.pk).update(
        payment_expires_at=timezone.now() - timedelta(seconds=1)
    )

    assert expire_ticket_order(order.pk) is True

    with pytest.raises(PaymentOrderUnavailable):
        settle(order)

    order.refresh_from_db()

    assert order.status == TicketOrder.Status.CANCELLED
    assert Ticket.objects.filter(order=order).count() == 0


@pytest.mark.django_db
def test_paid_order_cannot_be_expired(order_data):
    order = create_ticket_order(**order_data)

    settle(order)

    TicketOrder.objects.filter(pk=order.pk).update(
        payment_expires_at=timezone.now() - timedelta(seconds=1)
    )

    result = expire_ticket_order(order.pk)

    order.refresh_from_db()

    assert result is False
    assert order.status == TicketOrder.Status.PAID
    assert Ticket.objects.filter(order=order).count() == order.quantity


@pytest.mark.django_db
def test_partial_ticket_creation_is_rejected(order_data):
    order = create_ticket_order(**order_data)

    # Noto'g'ri, qisman yaratilgan chipta holatini simulyatsiya qilamiz.
    Ticket.objects.create(order=order)

    with pytest.raises(Exception):
        settle(order)

    order.refresh_from_db()

    assert order.status == TicketOrder.Status.PENDING
    assert order.paid_at is None

    # Oldindan mavjud bo'lgan chipta saqlanadi,
    # yangi chipta yaratilmaydi.
    assert Ticket.objects.filter(order=order).count() == 1

    assert RevenueEntry.objects.filter(
        source_payment_id=str(order.pk)
    ).count() == 0


@pytest.mark.django_db
def test_ticket_issuance_is_idempotent(order_data):
    order = create_ticket_order(**order_data)

    settle(order)

    first_numbers = set(
        Ticket.objects.filter(order=order)
        .values_list("ticket_number", flat=True)
    )

    order.refresh_from_db()

    issue_tickets_for_paid_order(order)

    second_numbers = set(
        Ticket.objects.filter(order=order)
        .values_list("ticket_number", flat=True)
    )

    assert first_numbers == second_numbers
    assert len(second_numbers) == order.quantity
