
from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction

from apps.competitions.models import Ticket, TicketOrder
from apps.competitions.services import issue_tickets_for_paid_order

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
def test_ticket_issuance_rejects_modified_paid_order_quantity(
    paid_click_order,
):
    order = paid_click_order

    tickets = issue_tickets_for_paid_order(order)
    original_quantity = order.quantity

    assert len(tickets) == original_quantity

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            TicketOrder.objects.filter(
                pk=order.pk,
            ).update(quantity=original_quantity + 1)

    order.refresh_from_db()

    assert order.quantity == original_quantity
    assert Ticket.objects.filter(
        order=order,
    ).count() == original_quantity

    repeated_tickets = issue_tickets_for_paid_order(order)

    assert {ticket.pk for ticket in repeated_tickets} == {
        ticket.pk for ticket in tickets
    }


@pytest.mark.django_db
def test_paid_order_financial_fields_are_immutable(paid_click_order):
    order = paid_click_order

    original_quantity = order.quantity
    original_unit_price = order.unit_price
    original_total = order.total_amount

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            TicketOrder.objects.filter(
                pk=order.pk,
            ).update(
                quantity=original_quantity + 1,
                unit_price=Decimal("1.00"),
                total_amount=Decimal("1.00"),
            )

    order.refresh_from_db()

    assert order.quantity == original_quantity
    assert order.unit_price == original_unit_price
    assert order.total_amount == original_total
