
from concurrent.futures import ThreadPoolExecutor
from threading import Event, Thread
from datetime import timedelta

import pytest

from django.db import (
    close_old_connections,
    connections,
    transaction,
)
from django.utils import timezone

from apps.competitions.models import TicketOrder
from apps.competitions.services import expire_ticket_order
from apps.payments.click_services import (
    ClickError,
    prepare_click_payment,
)
from apps.payments.models import ClickTransaction

from tests.integration.test_competition_orders import (
    competition_user,
    competition,
    order_data,
)
from tests.integration.test_click_http_integration import (
    click_order,
    click_settings,
    make_payload,
)


def run_in_thread(func):
    close_old_connections()
    try:
        return func()
    finally:
        connections.close_all()


def set_expired(order):
    TicketOrder.objects.filter(pk=order.pk).update(
        payment_expires_at=(
            timezone.now() - timedelta(minutes=5)
        )
    )


@pytest.mark.django_db(transaction=True)
def test_prepare_wins_expiration_race(click_order):
    """
    Prepare order lockni birinchi olsa,
    expiration faol transactionni bekor qilmasligi kerak.
    """
    assert connections["default"].vendor == "postgresql"

    payload = make_payload(click_order)

    lock_acquired = Event()
    release_lock = Event()

    def prepare_worker():
        def operation():
            with transaction.atomic():
                TicketOrder.objects.select_for_update().get(
                    pk=click_order.pk
                )
                tx = prepare_click_payment(payload)
                lock_acquired.set()

                if not release_lock.wait(timeout=10):
                    raise TimeoutError("Prepare lock timeout")

                return tx.pk

        return run_in_thread(operation)

    def expiration_worker():
        def operation():
            if not lock_acquired.wait(timeout=10):
                raise TimeoutError("Prepare did not acquire lock")

            return expire_ticket_order(click_order.pk)

        return run_in_thread(operation)

    with ThreadPoolExecutor(max_workers=2) as executor:
        prepare_future = executor.submit(prepare_worker)

        assert lock_acquired.wait(timeout=10)

        # Prepare hali commit qilinmagan.
        # Expiration shu orada ishga tushadi.
        expiration_future = executor.submit(expiration_worker)

        release_lock.set()

        prepare_future.result(timeout=20)
        expired = expiration_future.result(timeout=20)

    click_order.refresh_from_db()

    assert expired is False
    assert click_order.status == TicketOrder.Status.PENDING

    assert ClickTransaction.objects.filter(
        category="competition",
        order_id=str(click_order.pk),
        status=ClickTransaction.Status.PREPARED,
    ).count() == 1


@pytest.mark.django_db(transaction=True)
def test_expiration_wins_prepare_race(click_order):
    """
    Expiration order lockni birinchi olsa,
    muddati tugagan orderga Prepare ruxsat berilmaydi.
    """
    assert connections["default"].vendor == "postgresql"

    set_expired(click_order)

    payload = make_payload(click_order)

    lock_acquired = Event()
    release_lock = Event()

    def expiration_worker():
        def operation():
            with transaction.atomic():
                TicketOrder.objects.select_for_update().get(
                    pk=click_order.pk
                )

                lock_acquired.set()

                if not release_lock.wait(timeout=10):
                    raise TimeoutError("Expiration lock timeout")

                return expire_ticket_order(click_order.pk)

        return run_in_thread(operation)

    def prepare_worker():
        def operation():
            if not lock_acquired.wait(timeout=10):
                raise TimeoutError("Expiration did not acquire lock")

            try:
                prepare_click_payment(payload)
                return "prepared"
            except ClickError as exc:
                return exc.code

        return run_in_thread(operation)

    with ThreadPoolExecutor(max_workers=2) as executor:
        expiration_future = executor.submit(expiration_worker)

        assert lock_acquired.wait(timeout=10)

        prepare_future = executor.submit(prepare_worker)

        release_lock.set()

        expired = expiration_future.result(timeout=20)
        prepare_result = prepare_future.result(timeout=20)

    click_order.refresh_from_db()

    assert expired is True
    assert prepare_result == -9
    assert click_order.status == TicketOrder.Status.CANCELLED

    assert ClickTransaction.objects.filter(
        category="competition",
        order_id=str(click_order.pk),
    ).count() == 0


@pytest.mark.django_db(transaction=True)
def test_parallel_expiration_is_idempotent(click_order):
    """
    Ikkita expiration bir xil orderni
    parallel bekor qilganda faqat bittasi True qaytaradi.
    """
    assert connections["default"].vendor == "postgresql"

    set_expired(click_order)

    start = Event()

    def worker():
        def operation():
            if not start.wait(timeout=10):
                raise TimeoutError("Start timeout")

            return expire_ticket_order(click_order.pk)

        return run_in_thread(operation)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(worker)
            for _ in range(2)
        ]

        start.set()

        results = [
            future.result(timeout=20)
            for future in futures
        ]

    click_order.refresh_from_db()

    assert sorted(results) == [False, True]
    assert click_order.status == TicketOrder.Status.CANCELLED


@pytest.mark.django_db(transaction=True)
def test_prepared_transaction_prevents_expiration(
    click_order,
):
    """
    Click PREPARED mavjud bo'lsa,
    expiration orderni bekor qilmasligi kerak.
    """
    assert connections["default"].vendor == "postgresql"

    payload = make_payload(click_order)

    prepare_click_payment(payload)

    set_expired(click_order)

    result = expire_ticket_order(click_order.pk)

    click_order.refresh_from_db()

    assert result is False
    assert click_order.status == TicketOrder.Status.PENDING

    assert ClickTransaction.objects.filter(
        category="competition",
        order_id=str(click_order.pk),
        status=ClickTransaction.Status.PREPARED,
    ).exists()


@pytest.mark.django_db(transaction=True)
def test_paid_order_cannot_be_expired(click_order):
    """
    PAID orderni expiration o'zgartira olmaydi.
    """
    assert connections["default"].vendor == "postgresql"

    TicketOrder.objects.filter(pk=click_order.pk).update(
        status=TicketOrder.Status.PAID,
        paid_at=timezone.now(),
        provider_transaction_id=f"test-{click_order.pk}",
    )

    set_expired(click_order)

    result = expire_ticket_order(click_order.pk)

    click_order.refresh_from_db()

    assert result is False
    assert click_order.status == TicketOrder.Status.PAID
