from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.db import connection, close_old_connections

from apps.football.models import (
    FootballSubscription,
    FootballAcademyPayment,
)
from django.db import connections
from apps.finance.models import RevenueEntry
from apps.payments.models import ClickTransaction
from apps.payments.click_services import complete_click_payment

from tests.api.test_football_academy_click_complete import (
    subscription,
    prepare_subscription,
    complete_payload,
)
from tests.integration.test_click_http_integration import (
    click_settings,
)


pytestmark = pytest.mark.django_db(transaction=True)


def test_parallel_click_complete_only_one_payment(
    client,
    subscription,
    verified_click_provider,
):
    assert connection.vendor == "postgresql", (
        "Bu test PostgreSQL bilan bajarilishi kerak"
    )

    prepared, prepare_id = prepare_subscription(
        client,
        subscription,
    )

    payload = complete_payload(
        subscription,
        prepared,
        prepare_id,
    )

    barrier = Barrier(2)

    def worker():
        close_old_connections()

        try:
            barrier.wait(timeout=10)
            return complete_click_payment(payload)
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

    subscription.refresh_from_db()

    assert (
        subscription.status
        == FootballSubscription.Status.PAID
    )

    assert FootballAcademyPayment.objects.filter(
        subscription=subscription,
        status=FootballAcademyPayment.Status.SUCCEEDED,
    ).count() == 1

    assert RevenueEntry.objects.filter(
        source="football_academy_subscription",
        source_payment_id=str(subscription.pk),
        entry_type=RevenueEntry.EntryType.PAYMENT,
    ).count() == 1

    assert ClickTransaction.objects.filter(
        click_trans_id=prepared["click_trans_id"],
        status=ClickTransaction.Status.COMPLETED,
    ).count() == 1