from unittest.mock import patch

import pytest

from apps.payments.click_verification import (
    ClickVerificationResult,
)
from apps.payments.models import ClickTransaction
from apps.competitions.models import TicketOrder

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


@pytest.mark.django_db(transaction=True)
def test_cancelled_during_verification_cannot_settle(
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

    def provider_verification(
        *,
        click_trans_id,
        merchant_trans_id,
        amount,
    ):
        # Provider javob berayotgan paytda
        # boshqa callback transactionni bekor qildi.
        ClickTransaction.objects.filter(
            click_trans_id=click_trans_id,
        ).update(
            status=ClickTransaction.Status.CANCELLED,
        )

        return ClickVerificationResult(
            verified=True,
            click_trans_id=click_trans_id,
            merchant_trans_id=merchant_trans_id,
            amount=amount,
        )

    with patch(
        "apps.payments.click_services."
        "verify_click_payment_with_provider",
        side_effect=provider_verification,
    ):
        response = post_complete(client, payload)

    assert response.status_code == 200
    assert response.json()["error"] == -9

    click_order.refresh_from_db()

    assert click_order.status == TicketOrder.Status.PENDING

    tx = ClickTransaction.objects.get(
        click_trans_id=prepare_data["click_trans_id"],
    )

    assert tx.status == ClickTransaction.Status.CANCELLED


@pytest.mark.django_db(transaction=True)
def test_completed_during_verification_is_idempotent(
    client,
    click_order,
):
    from apps.finance.models import RevenueEntry
    from apps.payments.click_services import (
        complete_click_payment,
    )

    prepare_data = make_payload(click_order)
    prepared = post_prepare(client, prepare_data)

    assert prepared.json()["error"] == 0

    payload = make_payload(
        click_order,
        action="1",
        click_trans_id=prepare_data["click_trans_id"],
        prepare_id=prepared.json()["merchant_prepare_id"],
    )

    def provider_verification(
        *,
        click_trans_id,
        merchant_trans_id,
        amount,
    ):
        verification = ClickVerificationResult(
            verified=True,
            click_trans_id=click_trans_id,
            merchant_trans_id=merchant_trans_id,
            amount=amount,
        )

        # Boshqa callback verification davomida
        # ayni tranzaksiyani muvaffaqiyatli yakunlaydi.
        with patch(
            "apps.payments.click_services."
            "verify_click_payment_with_provider",
            return_value=verification,
        ):
            complete_click_payment(payload)

        return verification

    with patch(
        "apps.payments.click_services."
        "verify_click_payment_with_provider",
        side_effect=provider_verification,
    ):
        response = post_complete(client, payload)

    assert response.status_code == 200
    assert response.json()["error"] == 0

    click_order.refresh_from_db()
    assert click_order.status == TicketOrder.Status.PAID

    tx = ClickTransaction.objects.get(
        click_trans_id=prepare_data["click_trans_id"],
    )
    assert tx.status == ClickTransaction.Status.COMPLETED

    assert RevenueEntry.objects.filter(
        source="competition_ticket_order",
        source_payment_id=str(click_order.pk),
    ).count() == 1