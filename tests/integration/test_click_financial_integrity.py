from decimal import Decimal
from unittest.mock import patch

import pytest
from apps.competitions.models import Ticket
from apps.payments.models import ClickTransaction
from apps.payments.click_verification import ClickVerificationResult
from apps.finance.models import RevenueEntry

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


@pytest.mark.django_db
def test_provider_amount_mismatch_cannot_settle(
    client,
    click_order,
):
    prepare_data = make_payload(click_order)
    prepared = post_prepare(client, prepare_data)

    assert prepared.json()["error"] == 0

    payload = make_payload(
        click_order,
        action="1",
        click_trans_id=prepare_data["click_trans_id"],
        prepare_id=prepared.json()["merchant_prepare_id"],
    )

    def wrong_amount_provider(
        *,
        click_trans_id,
        merchant_trans_id,
        amount,
    ):
        return ClickVerificationResult(
            verified=True,
            click_trans_id=click_trans_id,
            merchant_trans_id=merchant_trans_id,
            amount=Decimal(str(amount)) + Decimal("1.00"),
        )

    with patch(
        "apps.payments.click_services.verify_click_payment_with_provider",
        side_effect=wrong_amount_provider,
    ):
        response = post_complete(client, payload)

    assert response.status_code == 200
    assert response.json()["error"] == -9

    click_order.refresh_from_db()
    assert click_order.status == click_order.Status.PENDING

    tx = ClickTransaction.objects.get(
        click_trans_id=prepare_data["click_trans_id"],
    )
    assert tx.status == ClickTransaction.Status.PREPARED

    assert not RevenueEntry.objects.filter(
        source="competition_ticket_order",
        source_payment_id=str(click_order.pk),
    ).exists()


@pytest.mark.django_db
def test_revenue_failure_rolls_back_entire_click_settlement(
    client,
    click_order,
    verified_click_provider,
):
    prepare_data = make_payload(click_order)

    prepared = post_prepare(client, prepare_data)
    assert prepared.json()["error"] == 0

    payload = make_payload(
        click_order,
        action="1",
        click_trans_id=prepare_data["click_trans_id"],
        prepare_id=prepared.json()["merchant_prepare_id"],
    )
    tickets_before = Ticket.objects.filter(
        order_id=click_order.pk,
    ).count()


    with patch(
        "apps.finance.payment_settlement.record_successful_payment",
        side_effect=RuntimeError("Simulated revenue database failure"),
    ):
        with pytest.raises(RuntimeError, match="Simulated revenue database failure"):
            post_complete(client, payload)

    # Order PAID bo'lib qolmasligi kerak.
    click_order.refresh_from_db()
    assert click_order.status == click_order.Status.PENDING
    assert click_order.paid_at is None
    assert not click_order.provider_transaction_id

    # ClickTransaction COMPLETED bo'lmasligi kerak.
    tx = ClickTransaction.objects.get(
        click_trans_id=prepare_data["click_trans_id"],
    )
    assert tx.status == ClickTransaction.Status.PREPARED

    # Revenue yaratilmasligi kerak.
    assert not RevenueEntry.objects.filter(
        source="competition_ticket_order",
        source_payment_id=str(click_order.pk),
    ).exists()

    # Revenue xatosidan keyin yaratilgan chiptalar
    # ham rollback bo'lishi kerak.
    tickets_after = Ticket.objects.filter(
        order_id=click_order.pk,
    ).count()

    assert tickets_after == tickets_before