
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.urls import reverse

from apps.payments.models import ClickTransaction
from apps.finance.models import RevenueEntry
from apps.payments.click_verification import (
    ClickVerificationResult,
    ClickVerificationUnavailable,
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


@pytest.mark.django_db
def test_provider_unavailable_does_not_complete_payment(
    client,
    click_order,
):
    prepare_payload = make_payload(click_order)

    prepare_response = client.post(
        reverse("click-prepare"),
        data=prepare_payload,
    )

    assert prepare_response.json()["error"] == 0

    prepare_id = prepare_response.json()["merchant_prepare_id"]

    complete_payload = make_payload(
        click_order,
        action="1",
        click_trans_id=prepare_payload["click_trans_id"],
        prepare_id=prepare_id,
    )

    original_status = click_order.status
    revenue_count = RevenueEntry.objects.count()

    with patch(
        "apps.payments.click_services.verify_click_payment_with_provider",
        side_effect=ClickVerificationUnavailable("Unavailable"),
    ):
        response = client.post(
            reverse("click-complete"),
            data=complete_payload,
        )

    assert response.status_code == 200
    assert response.json()["error"] != 0

    click_order.refresh_from_db()

    tx = ClickTransaction.objects.get(
        merchant_prepare_id=prepare_id,
    )

    assert tx.status == ClickTransaction.Status.PREPARED
    assert click_order.status == original_status
    assert RevenueEntry.objects.count() == revenue_count


@pytest.mark.django_db
def test_unverified_payment_does_not_settle(
    client,
    click_order,
):
    prepare_payload = make_payload(click_order)

    prepare_response = client.post(
        reverse("click-prepare"),
        data=prepare_payload,
    )

    assert prepare_response.json()["error"] == 0

    prepare_id = prepare_response.json()["merchant_prepare_id"]

    complete_payload = make_payload(
        click_order,
        action="1",
        click_trans_id=prepare_payload["click_trans_id"],
        prepare_id=prepare_id,
    )

    original_status = click_order.status
    revenue_count = RevenueEntry.objects.count()

    with patch(
        "apps.payments.click_services.verify_click_payment_with_provider",
        return_value=ClickVerificationResult(
            verified=False,
            click_trans_id=prepare_payload["click_trans_id"],
            merchant_trans_id=prepare_payload["merchant_trans_id"],
            amount=Decimal(str(click_order.total_amount)),
        ),
    ):
        response = client.post(
            reverse("click-complete"),
            data=complete_payload,
        )

    assert response.status_code == 200
    assert response.json()["error"] != 0

    click_order.refresh_from_db()

    tx = ClickTransaction.objects.get(
        merchant_prepare_id=prepare_id,
    )

    assert tx.status == ClickTransaction.Status.PREPARED
    assert click_order.status == original_status
    assert RevenueEntry.objects.count() == revenue_count
