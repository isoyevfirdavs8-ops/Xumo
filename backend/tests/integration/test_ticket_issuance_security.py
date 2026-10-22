
import uuid

import pytest
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.competitions.models import Ticket, TicketOrder
from apps.competitions.services import (
    create_ticket_order,
    issue_tickets_for_paid_order,
)

from tests.integration.test_competition_orders import (
    competition_user,
    competition,
    order_data,
)
from tests.integration.test_click_http_integration import (
    click_order,
    click_settings,
)


@pytest.mark.django_db
def test_paid_order_tickets_are_not_duplicated(paid_click_order):
    order = paid_click_order

    with transaction.atomic():
        first_tickets = issue_tickets_for_paid_order(order)
        second_tickets = issue_tickets_for_paid_order(order)

    assert len(first_tickets) == order.quantity
    assert len(second_tickets) == order.quantity

    tickets = Ticket.objects.filter(order=order)

    assert tickets.count() == order.quantity

    assert {ticket.pk for ticket in first_tickets} == {
        ticket.pk for ticket in second_tickets
    }


@pytest.mark.django_db
def test_partial_ticket_issuance_is_rejected(
    order_data,
    click_settings,
):
    data = {
        **order_data,
        "quantity": 2,
        "idempotency_key": uuid.uuid4(),
    }

    order = create_ticket_order(**data)

    order.status = TicketOrder.Status.PAID
    order.paid_at = timezone.now()
    order.provider_transaction_id = f"test-click-{order.pk}"

    order.save(
        update_fields=[
            "status",
            "paid_at",
            "provider_transaction_id",
        ]
    )

    Ticket.objects.create(order=order)

    with pytest.raises(
        ValidationError,
        match="Buyurtmadagi chiptalar soni mos kelmayapti",
    ):
        with transaction.atomic():
            issue_tickets_for_paid_order(order)

    assert Ticket.objects.filter(order=order).count() == 1
