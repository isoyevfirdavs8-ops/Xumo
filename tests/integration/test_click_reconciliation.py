
from datetime import timedelta

import pytest

from django.core.management import call_command
from django.utils import timezone

from apps.payments.click_reconciliation import (
    get_stale_click_transactions,
    get_click_reconciliation_summary,
)
from apps.payments.click_services import prepare_click_payment
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


@pytest.fixture
def prepared_click(click_order):
    payload = make_payload(click_order)
    return prepare_click_payment(payload)


def make_stale(tx):
    ClickTransaction.objects.filter(
        pk=tx.pk
    ).update(
        created_at=timezone.now() - timedelta(minutes=30)
    )


@pytest.mark.django_db
def test_recent_prepared_transaction_not_stale(prepared_click):
    result = get_stale_click_transactions(
        older_than_minutes=15
    )

    assert result == []


@pytest.mark.django_db
def test_old_prepared_transaction_is_detected(prepared_click):
    make_stale(prepared_click)

    result = get_stale_click_transactions(
        older_than_minutes=15
    )

    assert len(result) == 1
    assert result[0].pk == prepared_click.pk


@pytest.mark.django_db
def test_completed_transaction_is_not_stale(prepared_click):
    make_stale(prepared_click)

    ClickTransaction.objects.filter(
        pk=prepared_click.pk
    ).update(
        status=ClickTransaction.Status.COMPLETED
    )

    result = get_stale_click_transactions()

    assert result == []


@pytest.mark.django_db
def test_cancelled_transaction_is_not_stale(prepared_click):
    make_stale(prepared_click)

    ClickTransaction.objects.filter(
        pk=prepared_click.pk
    ).update(
        status=ClickTransaction.Status.CANCELLED
    )

    result = get_stale_click_transactions()

    assert result == []


@pytest.mark.django_db
def test_reconciliation_is_read_only(prepared_click):
    make_stale(prepared_click)

    get_stale_click_transactions()
    get_click_reconciliation_summary()

    prepared_click.refresh_from_db()

    assert prepared_click.status == ClickTransaction.Status.PREPARED


@pytest.mark.django_db
def test_reconciliation_summary_counts_stale(prepared_click):
    make_stale(prepared_click)

    summary = get_click_reconciliation_summary()

    assert summary["stale_prepared_count"] == 1
    assert summary["older_than_minutes"] == 15


@pytest.mark.django_db
def test_reconciliation_rejects_invalid_parameters():
    with pytest.raises(ValueError):
        get_stale_click_transactions(
            older_than_minutes=0
        )

    with pytest.raises(ValueError):
        get_stale_click_transactions(limit=0)

    with pytest.raises(ValueError):
        get_click_reconciliation_summary(
            older_than_minutes=-1
        )


@pytest.mark.django_db
def test_reconciliation_management_command(capsys, prepared_click):
    make_stale(prepared_click)

    call_command(
        "check_click_reconciliation",
        minutes=15,
    )

    output = capsys.readouterr().out

    assert '"stale_prepared_count": 1' in output
