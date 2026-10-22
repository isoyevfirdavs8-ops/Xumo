import hashlib
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

import pytest

from django.contrib.auth import get_user_model
from django.db import connection
from django.utils import timezone

from apps.football.models import (
    FootballAcademy,
    FootballSubscription,
    FootballAcademyPayment,
)
from apps.finance.models import RevenueEntry
from apps.payments.models import ClickTransaction
from apps.payments.click_verification import ClickVerificationResult

from tests.integration.test_click_http_integration import (
    click_settings,
    post_prepare,
    post_complete,
)


pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def subscription(click_settings):
    User = get_user_model()

    user = User.objects.create_user(
        phone_number="+998901234569",
        password="StrongPass123!",
    )

    academy = FootballAcademy.objects.create(
        name="FC BUKHARA Complete Academy",
        monthly_price=Decimal("350000.00"),
    )

    today = timezone.localdate()

    return FootballSubscription.objects.create(
        user=user,
        academy=academy,
        month=date(today.year, today.month, 1),
        price_snapshot=Decimal("350000.00"),
        status=FootballSubscription.Status.PENDING_PAYMENT,
        payment_expires_at=timezone.now() + timedelta(minutes=15),
    )


def make_academy_payload(
    subscription,
    *,
    action="0",
    click_trans_id=None,
    prepare_id=None,
    error="0",
    amount=None,
):
    data = {
        "click_trans_id": click_trans_id or str(uuid4()),
        "service_id": "12345",
        "merchant_trans_id": f"football_academy:{subscription.pk}",
        "amount": str(
            amount if amount is not None
            else subscription.price_snapshot
        ),
        "action": action,
        "sign_time": timezone.localtime().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
    }

    if action == "1":
        data["merchant_prepare_id"] = str(prepare_id)
        data["error"] = error

    parts = [
        data["click_trans_id"],
        data["service_id"],
        "test-secret-key",
        data["merchant_trans_id"],
    ]

    if action == "1":
        parts.append(data["merchant_prepare_id"])

    parts.extend([
        data["amount"],
        data["action"],
        data["sign_time"],
    ])

    data["sign_string"] = hashlib.md5(
        "".join(parts).encode("utf-8")
    ).hexdigest()

    return data


def prepare_subscription(client, subscription):
    payload = make_academy_payload(subscription)

    response = post_prepare(client, payload)

    assert response.status_code == 200
    assert response.json()["error"] == 0

    return payload, response.json()["merchant_prepare_id"]


def complete_payload(subscription, prepared, prepare_id, **kwargs):
    return make_academy_payload(
        subscription,
        action="1",
        click_trans_id=prepared["click_trans_id"],
        prepare_id=prepare_id,
        **kwargs,
    )


def assert_no_settlement(subscription):
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


def test_complete_success(
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

    response = post_complete(client, payload)

    assert response.status_code == 200
    assert response.json()["error"] == 0

    subscription.refresh_from_db()

    assert subscription.status == FootballSubscription.Status.PAID
    assert subscription.paid_at is not None

    payment = FootballAcademyPayment.objects.get(
        subscription=subscription,
        status=FootballAcademyPayment.Status.SUCCEEDED,
    )

    assert payment.provider == "click"
    assert payment.is_demo is False
    assert payment.provider_transaction_id == prepared["click_trans_id"]

    assert RevenueEntry.objects.filter(
        source="football_academy_subscription",
        source_payment_id=str(subscription.pk),
        entry_type=RevenueEntry.EntryType.PAYMENT,
    ).count() == 1

    assert ClickTransaction.objects.get(
        click_trans_id=prepared["click_trans_id"]
    ).status == ClickTransaction.Status.COMPLETED


def test_duplicate_complete_is_idempotent(
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


def test_wrong_prepare_id_rejected(
    client,
    subscription,
):
    prepared, prepare_id = prepare_subscription(
        client, subscription
    )

    payload = complete_payload(
        subscription,
        prepared,
        "999999999",
    )

    response = post_complete(client, payload)

    assert response.json()["error"] == -4

    assert_no_settlement(subscription)


def test_cancelled_complete_does_not_settle(
    client,
    subscription,
):
    prepared, prepare_id = prepare_subscription(
        client, subscription
    )

    payload = complete_payload(
        subscription,
        prepared,
        prepare_id,
        error="-1",
    )

    response = post_complete(client, payload)

    assert response.status_code == 200

    tx = ClickTransaction.objects.get(
        click_trans_id=prepared["click_trans_id"]
    )

    assert tx.status == ClickTransaction.Status.CANCELLED

    assert_no_settlement(subscription)


def test_provider_verification_outside_atomic(
    client,
    subscription,
):
    prepared, prepare_id = prepare_subscription(
        client, subscription
    )

    payload = complete_payload(
        subscription, prepared, prepare_id
    )

    def fake_verification(
        *,
        click_trans_id,
        merchant_trans_id,
        amount,
    ):
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
        side_effect=fake_verification,
    ):
        response = post_complete(client, payload)

    assert response.status_code == 200
    assert response.json()["error"] == 0

    subscription.refresh_from_db()
    assert subscription.status == FootballSubscription.Status.PAID