from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch

import pytest
from django.db import close_old_connections, connections

from apps.payments.click_verification import ClickVerificationResult
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
    post_prepare,
    post_complete,
)
from apps.finance.models import RevenueEntry


@pytest.mark.django_db(transaction=True)
def test_parallel_complete_callbacks_settle_once(
    client,
    click_order,
):
    assert connections["default"].vendor == "postgresql"

    prepare_data = make_payload(click_order)
    prepared = post_prepare(client, prepare_data)

    assert prepared.json()["error"] == 0

    payload = make_payload(
        click_order,
        action="1",
        click_trans_id=prepare_data["click_trans_id"],
        prepare_id=prepared.json()["merchant_prepare_id"],
    )

    barrier = Barrier(2, timeout=10)

    def verify_provider(*, click_trans_id, merchant_trans_id, amount):
        return ClickVerificationResult(
            verified=True,
            click_trans_id=click_trans_id,
            merchant_trans_id=merchant_trans_id,
            amount=amount,
        )

    def worker():
        close_old_connections()

        try:
            from django.test import Client

            thread_client = Client()

            barrier.wait()

            return post_complete(
                thread_client,
                payload,
            )

        finally:
            connections.close_all()

    with patch(
        "apps.payments.click_services.verify_click_payment_with_provider",
        side_effect=verify_provider,
    ):
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(worker) for _ in range(2)]
            responses = [future.result(timeout=20) for future in futures]

    assert all(response.status_code == 200 for response in responses)
    assert all(response.json()["error"] == 0 for response in responses)

    tx = ClickTransaction.objects.get(
        click_trans_id=prepare_data["click_trans_id"],
    )
    assert tx.status == ClickTransaction.Status.COMPLETED

    # Buyurtma to'langan holatda bo'lishi kerak.
    click_order.refresh_from_db()

    assert click_order.status == click_order.Status.PAID

    # Shu transaction bo'yicha faqat bitta completed yozuv.
    assert ClickTransaction.objects.filter(
        click_trans_id=prepare_data["click_trans_id"],
        status=ClickTransaction.Status.COMPLETED,
    ).count() == 1

    # Buyurtmaning yakuniy holati.
    click_order.refresh_from_db()
    assert click_order.status == click_order.Status.PAID

    # Shu buyurtmaga tegishli moliyaviy yozuvlar.
    revenue_entries = RevenueEntry.objects.filter(
        source="competition_ticket_order",
        source_payment_id=str(click_order.pk),
    )

    # Parallel callbacklar revenue'ni takrorlamasligi kerak.
    assert revenue_entries.count() == 1

    # Moliyaviy summa buyurtma summasiga teng bo'lishi kerak.
    revenue = revenue_entries.get()
    assert revenue.amount == click_order.total_amount


