
from datetime import timedelta

import pytest

from django.utils import timezone

from apps.competitions.models import TicketOrder
from apps.payments.click_services import prepare_click_payment
from apps.payments.click_reconciliation import (
    audit_stale_click_transactions,
)
from apps.payments.reconciliation_audit import (
    audit_stale_click_transaction,
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
def prepared_click(click_order):
    return prepare_click_payment(
        make_payload(click_order)
    )


def make_stale(tx):
    ClickTransaction.objects.filter(
        pk=tx.pk
    ).update(
        created_at=timezone.now() - timedelta(minutes=30)
    )


@pytest.mark.django_db
def test_audit_creates_record(prepared_click):
    make_stale(prepared_click)

    audit = audit_stale_click_transaction(
        prepared_click.pk
    )

    assert audit is not None
    assert audit.provider == "click"
    assert audit.result == (
        PaymentReconciliationAudit.Result.STALE_PREPARED
    )
    assert PaymentReconciliationAudit.objects.count() == 1



@pytest.mark.django_db
def test_audit_does_not_change_transaction(prepared_click):
    # Transactionni 30 daqiqa eski qilamiz.
    make_stale(prepared_click)

    audit = audit_stale_click_transaction(
        prepared_click.pk
    )

    prepared_click.refresh_from_db()

    # Audit yaratilgan bo'lishi kerak.
    assert audit is not None

    # Audit payment holatini o'zgartirmasligi kerak.
    assert prepared_click.status == ClickTransaction.Status.PREPARED

    # Faqat bitta audit yozuvi yaratiladi.
    assert PaymentReconciliationAudit.objects.count() == 1


@pytest.mark.django_db
def test_audit_does_not_change_order(click_order):
    # Click Prepare transaction yaratamiz.
    tx = prepare_click_payment(
        make_payload(click_order)
    )

    # Transactionni 30 daqiqa eski qilamiz.
    make_stale(tx)

    audit = audit_stale_click_transaction(
        tx.pk
    )

    click_order.refresh_from_db()
    tx.refresh_from_db()

    assert audit is not None

    assert click_order.status == TicketOrder.Status.PENDING


    assert tx.status == ClickTransaction.Status.PREPARED


    assert PaymentReconciliationAudit.objects.count() == 1



@pytest.mark.django_db
def test_completed_transaction_not_audited(prepared_click):
    ClickTransaction.objects.filter(
        pk=prepared_click.pk
    ).update(
        status=ClickTransaction.Status.COMPLETED
    )

    result = audit_stale_click_transaction(
        prepared_click.pk
    )

    assert result is None
    assert PaymentReconciliationAudit.objects.count() == 0


@pytest.mark.django_db
def test_cancelled_transaction_not_audited(prepared_click):
    ClickTransaction.objects.filter(
        pk=prepared_click.pk
    ).update(
        status=ClickTransaction.Status.CANCELLED
    )

    result = audit_stale_click_transaction(
        prepared_click.pk
    )

    assert result is None


@pytest.mark.django_db
def test_unknown_transaction_not_audited():
    result = audit_stale_click_transaction(
        999999999
    )

    assert result is None


@pytest.mark.django_db
def test_stale_transaction_is_audited(prepared_click):
    make_stale(prepared_click)

    audit_ids = audit_stale_click_transactions()

    assert len(audit_ids) == 1
    assert PaymentReconciliationAudit.objects.count() == 1


@pytest.mark.django_db
def test_recent_transaction_not_audited(prepared_click):
    audit_ids = audit_stale_click_transactions()

    assert audit_ids == []
    assert PaymentReconciliationAudit.objects.count() == 0

