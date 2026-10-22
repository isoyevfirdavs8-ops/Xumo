
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.db import close_old_connections, connections

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


@pytest.mark.django_db(transaction=True)
def test_parallel_ticket_issuance_does_not_duplicate(
    paid_click_order,
):
    assert connections["default"].vendor == "postgresql"

    order = paid_click_order
    order_id = order.pk

    barrier = Barrier(2, timeout=10)

    def worker():
        close_old_connections()

        try:
            locked_order = TicketOrder.objects.get(
                pk=order_id,
            )

            barrier.wait()

            tickets = issue_tickets_for_paid_order(
                locked_order,
            )

            return {ticket.pk for ticket in tickets}

        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(worker)
            for _ in range(2)
        ]

        results = [
            future.result(timeout=20)
            for future in futures
        ]

    assert len(results) == 2
    assert results[0] == results[1]

    tickets = Ticket.objects.filter(order_id=order_id)

    assert tickets.count() == order.quantity
    assert len(
        set(
            tickets.values_list(
                "ticket_number",
                flat=True,
            )
        )
    ) == order.quantity
