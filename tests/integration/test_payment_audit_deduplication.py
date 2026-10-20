
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Event

import pytest

from django.db import close_old_connections, connections
from django.utils import timezone

from apps.payments.click_services import prepare_click_payment
from apps.payments.reconciliation_audit import (
    audit_stale_click_transaction,
)
from apps.payments.audit_retention import (
    cleanup_old_payment_audits,
)
from apps.payments.models import (
    ClickTransaction,
    PaymentReconciliationAudit,
)

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


@pytest.fixture
def stale_click(click_order):
    tx = prepare_click_payment(
        make_payload(click_order)
    )

    ClickTransaction.objects.filter(
        pk=tx.pk
    ).update(
        created_at=timezone.now() - timedelta(minutes=30)
    )

    return tx


@pytest.mark.django_db
def test_repeated_audit_is_idempotent(stale_click):
    first = audit_stale_click_transaction(stale_click.pk)
    second = audit_stale_click_transaction(stale_click.pk)

    assert first.pk == second.pk
    assert PaymentReconciliationAudit.objects.count() == 1


@pytest.mark.django_db
def test_recent_transaction_not_audited(click_order):
    tx = prepare_click_payment(
        make_payload(click_order)
    )

    result = audit_stale_click_transaction(tx.pk)

    assert result is None
    assert PaymentReconciliationAudit.objects.count() == 0


@pytest.mark.django_db(transaction=True)
def test_parallel_audit_creates_single_record(stale_click):
    assert connections["default"].vendor == "postgresql"

    start = Event()

    def worker():
        close_old_connections()
        try:
            if not start.wait(timeout=10):
                raise TimeoutError("Start timeout")

            audit = audit_stale_click_transaction(
                stale_click.pk
            )
            return audit.pk
        finally:
            connections.close_all()

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

    assert results[0] == results[1]
    assert PaymentReconciliationAudit.objects.count() == 1


@pytest.mark.django_db
def test_retention_dry_run_does_not_delete(stale_click):
    audit = audit_stale_click_transaction(stale_click.pk)

    PaymentReconciliationAudit.objects.filter(
        pk=audit.pk
    ).update(
        created_at=timezone.now() - timedelta(days=200)
    )

    result = cleanup_old_payment_audits(
        retention_days=180,
        dry_run=True,
    )

    assert result["eligible"] == 1
    assert result["deleted"] == 0
    assert PaymentReconciliationAudit.objects.count() == 1


@pytest.mark.django_db
def test_retention_deletes_only_old_stale_audits(stale_click):
    audit = audit_stale_click_transaction(stale_click.pk)

    PaymentReconciliationAudit.objects.filter(
        pk=audit.pk
    ).update(
        created_at=timezone.now() - timedelta(days=200)
    )

    result = cleanup_old_payment_audits(
        retention_days=180,
        dry_run=False,
    )

    assert result["deleted"] == 1
    assert PaymentReconciliationAudit.objects.count() == 0

    assert ClickTransaction.objects.filter(
        pk=stale_click.pk
    ).exists()


@pytest.mark.django_db
def test_retention_rejects_short_period():
    with pytest.raises(ValueError):
        cleanup_old_payment_audits(
            retention_days=10
        )
