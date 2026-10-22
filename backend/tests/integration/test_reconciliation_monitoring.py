
from datetime import timedelta

import pytest

from django.utils import timezone

from apps.payments.click_services import prepare_click_payment
from apps.payments.models import ClickTransaction
from apps.payments.reconciliation_monitoring import (
    check_click_reconciliation_health,
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
def test_monitoring_healthy_without_stale():
    result = check_click_reconciliation_health()

    assert result["status"] == "healthy"
    assert result["stale_prepared_count"] == 0


@pytest.mark.django_db
def test_monitoring_healthy_below_threshold(stale_click):
    result = check_click_reconciliation_health(
        warning_threshold=2,
        critical_threshold=5,
    )

    assert result["status"] == "healthy"
    assert result["stale_prepared_count"] == 1


@pytest.mark.django_db
def test_monitoring_warning(stale_click):
    result = check_click_reconciliation_health(
        warning_threshold=1,
        critical_threshold=5,
    )

    assert result["status"] == "warning"


@pytest.mark.django_db
def test_monitoring_critical(stale_click):
    result = check_click_reconciliation_health(
        warning_threshold=1,
        critical_threshold=2,
    )

    assert result["status"] == "warning"


@pytest.mark.django_db
def test_monitoring_does_not_change_payment(stale_click):
    check_click_reconciliation_health(
        warning_threshold=1,
        critical_threshold=5,
    )

    stale_click.refresh_from_db()

    assert stale_click.status == ClickTransaction.Status.PREPARED


@pytest.mark.django_db
def test_monitoring_rejects_invalid_threshold():
    with pytest.raises(ValueError):
        check_click_reconciliation_health(
            warning_threshold=0
        )

    with pytest.raises(ValueError):
        check_click_reconciliation_health(
            warning_threshold=5,
            critical_threshold=5,
        )
