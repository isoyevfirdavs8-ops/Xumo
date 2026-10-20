
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest

from django.db import close_old_connections, connection

from apps.competitions.models import Ticket, TicketOrder
from apps.finance.models import RevenueEntry
from apps.payments.click_services import (
    ClickError,
    prepare_click_payment,
    complete_click_payment,
)
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
)


def run_parallel(functions):
    start = Event()

    def worker(func):
        close_old_connections()
        try:
            start.wait(timeout=10)
            return func()
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=len(functions)) as pool:
        futures = [
            pool.submit(worker, func)
            for func in functions
        ]

        start.set()

        results = []
        for future in futures:
            try:
                results.append(("ok", future.result(timeout=30)))
            except ClickError as exc:
                results.append(("click_error", exc.code))

        return results


@pytest.fixture
def prepared_transaction(click_order):
    data = make_payload(click_order)
    tx = prepare_click_payment(data)

    return {
        "order": click_order,
        "tx": tx,
        "prepare_data": data,
    }


@pytest.mark.django_db(transaction=True)
def test_parallel_prepare_same_transaction(
    click_order,
):
    assert connection.vendor == "postgresql"

    payload = make_payload(click_order)

    results = run_parallel([
        lambda: prepare_click_payment(payload),
        lambda: prepare_click_payment(payload),
    ])

    assert len(results) == 2
    assert all(status == "ok" for status, _ in results)

    assert ClickTransaction.objects.filter(
        click_trans_id=payload["click_trans_id"]
    ).count() == 1

    assert (
        results[0][1].merchant_prepare_id
        == results[1][1].merchant_prepare_id
    )


@pytest.mark.django_db(transaction=True)
def test_parallel_prepare_different_transactions(
    click_order,
):
    assert connection.vendor == "postgresql"

    first = make_payload(click_order)
    second = make_payload(click_order)

    results = run_parallel([
        lambda: prepare_click_payment(first),
        lambda: prepare_click_payment(second),
    ])

    successes = [
        value
        for status, value in results
        if status == "ok"
    ]

    conflicts = [
        value
        for status, value in results
        if status == "click_error"
    ]

    assert len(successes) == 1
    assert conflicts == [-4]

    assert ClickTransaction.objects.filter(
        category="competition",
        order_id=str(click_order.pk),
        status=ClickTransaction.Status.PREPARED,
    ).count() == 1


@pytest.mark.django_db(transaction=True)
def test_parallel_complete_settles_once(
    prepared_transaction,
verified_click_provider
):
    assert connection.vendor == "postgresql"

    order = prepared_transaction["order"]
    tx = prepared_transaction["tx"]
    prepare_data = prepared_transaction["prepare_data"]

    payload = make_payload(
        order,
        action="1",
        click_trans_id=prepare_data["click_trans_id"],
        prepare_id=tx.merchant_prepare_id,
        error="0",
    )

    results = run_parallel([
        lambda: complete_click_payment(payload),
        lambda: complete_click_payment(payload),
    ])

    assert len(results) == 2
    assert all(status == "ok" for status, _ in results)

    order.refresh_from_db()
    tx.refresh_from_db()

    assert order.status == TicketOrder.Status.PAID
    assert tx.status == ClickTransaction.Status.COMPLETED

    assert Ticket.objects.filter(
        order=order,
    ).count() == order.quantity

    assert RevenueEntry.objects.filter(
        source="competition_ticket_order",
        source_payment_id=str(order.pk),
        entry_type=RevenueEntry.EntryType.PAYMENT,
    ).count() == 1
