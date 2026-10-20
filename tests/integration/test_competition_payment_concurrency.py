
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from django.db import close_old_connections, connections

from apps.competitions.models import Ticket, TicketOrder
from apps.competitions.services import create_ticket_order
from apps.finance.models import RevenueEntry
from apps.finance.payment_settlement import (
    settle_competition_payment,
)
from apps.payments.exceptions import (
    PaymentOrderUnavailable,
    PaymentTransactionConflict,
)

from tests.integration.test_competition_orders import (
    competition_user,
    competition,
    order_data,
)
from apps.payments.exceptions import PaymentTransactionConflict

def payment_worker(order_id, transaction_id, barrier):
    close_old_connections()

    try:
        barrier.wait(timeout=10)

        order = settle_competition_payment(
            order_id=order_id,
            provider="click",
            provider_transaction_id=transaction_id,
        )

        return ("success", str(order.pk))


    except PaymentTransactionConflict as exc:
        return ("rejected", str(exc))

    finally:
        connections.close_all()


@pytest.mark.django_db(transaction=True)
def test_parallel_same_payment_callback_is_idempotent(order_data):
    order = create_ticket_order(**order_data)

    transaction_id = f"parallel-{uuid.uuid4()}"
    barrier = Barrier(2)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(
                payment_worker,
                order.pk,
                transaction_id,
                barrier,
            )
            for _ in range(2)
        ]

        results = [
            future.result(timeout=20)
            for future in futures
        ]

    assert all(
        result[0] == "success"
        for result in results
    ), results

    assert results[0][1] == results[1][1]

    order.refresh_from_db()

    assert order.status == TicketOrder.Status.PAID
    assert order.provider_transaction_id == transaction_id

    assert Ticket.objects.filter(order=order).count() == order.quantity

    assert RevenueEntry.objects.filter(
        source="competition_ticket_order",
        source_payment_id=str(order.pk),
        entry_type=RevenueEntry.EntryType.PAYMENT,
    ).count() == 1


@pytest.mark.django_db(transaction=True)
def test_parallel_different_transaction_ids_rejected(order_data):
    order = create_ticket_order(**order_data)

    barrier = Barrier(2)

    transaction_ids = [
        f"parallel-{uuid.uuid4()}",
        f"parallel-{uuid.uuid4()}",
    ]

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(
                payment_worker,
                order.pk,
                transaction_id,
                barrier,
            )
            for transaction_id in transaction_ids
        ]

        results = [
            future.result(timeout=20)
            for future in futures
        ]

    successes = [
        result for result in results
        if result[0] == "success"
    ]

    rejected = [
        result for result in results
        if result[0] == "rejected"
    ]

    assert len(successes) == 1, results
    assert len(rejected) == 1, results

    order.refresh_from_db()

    assert order.status == TicketOrder.Status.PAID
    assert order.provider_transaction_id in transaction_ids

    assert Ticket.objects.filter(order=order).count() == order.quantity

    assert RevenueEntry.objects.filter(
        source="competition_ticket_order",
        source_payment_id=str(order.pk),
        entry_type=RevenueEntry.EntryType.PAYMENT,
    ).count() == 1
