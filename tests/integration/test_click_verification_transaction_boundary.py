from decimal import Decimal
from unittest.mock import patch

import pytest
from django.db import connection

from apps.payments.click_verification import (
    ClickVerificationResult,
)

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
def test_click_provider_verification_runs_outside_atomic(
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

    def fake_provider_verification(
        *,
        click_trans_id,
        merchant_trans_id,
        amount,
    ):
        # Tashqi provider so'rovi vaqtida
        # Django transaction ochiq bo'lmasligi kerak.
        assert connection.in_atomic_block is False

        return ClickVerificationResult(
            verified=True,
            click_trans_id=click_trans_id,
            merchant_trans_id=merchant_trans_id,
            amount=Decimal(str(amount)),
        )

    with patch(
        "apps.payments.click_services."
        "verify_click_payment_with_provider",
        side_effect=fake_provider_verification,
    ):
        response = post_complete(client, payload)

    assert response.status_code == 200
    assert response.json()["error"] == 0