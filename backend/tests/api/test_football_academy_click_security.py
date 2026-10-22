from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.football.models import (
    FootballSubscription,
    FootballAcademyPayment,
)
from apps.finance.models import RevenueEntry
from apps.payments.models import ClickTransaction
from apps.payments.click_verification import (
    ClickVerificationError,
)

from tests.api.test_football_academy_click_complete import (
    subscription,
    prepare_subscription,
    complete_payload,
    post_complete,
)

from tests.integration.test_click_http_integration import (
    click_settings,
)


pytestmark = pytest.mark.django_db(transaction=True)


def assert_payment_not_completed(subscription, click_trans_id):
    subscription.refresh_from_db()

    assert (
        subscription.status
        == FootballSubscription.Status.PENDING_PAYMENT
    )

    assert not FootballAcademyPayment.objects.filter(
        subscription=subscription,
        status=FootballAcademyPayment.Status.SUCCEEDED,
    ).exists()

    assert not RevenueEntry.objects.filter(
        source="football_academy_subscription",
        source_payment_id=str(subscription.pk),
    ).exists()

    tx = ClickTransaction.objects.get(
        click_trans_id=click_trans_id
    )

    assert tx.status == ClickTransaction.Status.PREPARED


def test_provider_verification_rejected(client, subscription):
    prepared, prepare_id = prepare_subscription(
        client, subscription
    )

    payload = complete_payload(
        subscription, prepared, prepare_id
    )

    with patch(
        "apps.payments.click_services."
        "verify_click_payment_with_provider",
        side_effect=ClickVerificationError(
            "Provider verification failed"
        ),
    ):
        response = post_complete(client, payload)

    assert response.status_code == 200
    assert response.json()["error"] != 0

    assert_payment_not_completed(
        subscription,
        prepared["click_trans_id"],
    )


def test_invalid_signature_rejected(client, subscription):
    prepared, prepare_id = prepare_subscription(
        client, subscription
    )

    payload = complete_payload(
        subscription, prepared, prepare_id
    )

    payload["sign_string"] = "invalid-signature"

    response = post_complete(client, payload)

    assert response.status_code == 200
    assert response.json()["error"] == -1

    assert_payment_not_completed(
        subscription,
        prepared["click_trans_id"],
    )


def test_expired_subscription_not_settled(
    client,
    subscription,
    verified_click_provider,
):
    prepared, prepare_id = prepare_subscription(
        client, subscription
    )

    subscription.payment_expires_at = (
        timezone.now() - timezone.timedelta(minutes=1)
    )
    subscription.save(
        update_fields=["payment_expires_at"]
    )

    payload = complete_payload(
        subscription, prepared, prepare_id
    )

    response = post_complete(client, payload)

    assert response.status_code == 200
    assert response.json()["error"] != 0

    assert_payment_not_completed(
        subscription,
        prepared["click_trans_id"],
    )


def test_settlement_failure_rolls_back(
    client,
    subscription,
    verified_click_provider,
):
    prepared, prepare_id = prepare_subscription(
        client, subscription
    )

    payload = complete_payload(
        subscription, prepared, prepare_id
    )

    def fail_revenue_recording(**kwargs):
        raise ValueError("Simulated finance failure")

    # Django test client HTTP 500 exceptionni qayta ko'tarmasin.
    client.raise_request_exception = False

    with patch(
        "apps.football.academy_payment_services."
        "record_successful_payment",
        side_effect=fail_revenue_recording,
    ):
        response = post_complete(client, payload)

    # Kutilmagan settlement xatosi server xatosi sifatida qaytadi.
    assert response.status_code == 500

    # Muhim: payment, subscription va ClickTransaction
    # holatlari avvalgi qiymatida qolishi kerak.
    assert_payment_not_completed(
        subscription,
        prepared["click_trans_id"],
    )

def test_duplicate_callback_after_success(
    client,
    subscription,
    verified_click_provider,
):
    prepared, prepare_id = prepare_subscription(
        client, subscription
    )

    payload = complete_payload(
        subscription, prepared, prepare_id
    )

    first = post_complete(client, payload)
    second = post_complete(client, payload)

    assert first.json()["error"] == 0
    assert second.json()["error"] == 0

    assert FootballAcademyPayment.objects.filter(
        subscription=subscription,
        status=FootballAcademyPayment.Status.SUCCEEDED,
    ).count() == 1

    assert RevenueEntry.objects.filter(
        source="football_academy_subscription",
        source_payment_id=str(subscription.pk),
    ).count() == 1