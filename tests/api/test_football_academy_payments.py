from datetime import date, timedelta
from decimal import Decimal

import pytest

from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.football.models import (
    FootballAcademy,
    FootballSubscription,
    FootballAcademyPayment,
)
from apps.football.academy_payment_services import (
    confirm_football_academy_payment,
)
from apps.finance.models import RevenueEntry
from apps.payments.exceptions import (
    PaymentOrderUnavailable,
    PaymentTransactionConflict,
)


pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def subscription():
    User = get_user_model()

    user = User.objects.create_user(
        phone_number="+998901234567",
        password="StrongPass123!",
    )

    academy = FootballAcademy.objects.create(
        name="FC BUKHARA Academy",
        monthly_price=Decimal("300000.00"),
    )

    today = timezone.localdate()
    month = date(today.year, today.month, 1)

    return FootballSubscription.objects.create(
        user=user,
        academy=academy,
        month=month,
        price_snapshot=Decimal("300000.00"),
        status=FootballSubscription.Status.PENDING_PAYMENT,
        payment_expires_at=timezone.now() + timedelta(minutes=15),
    )


def settle(subscription, transaction_id="CLICK-1001", amount="300000.00"):
    return confirm_football_academy_payment(
        subscription_id=subscription.pk,
        provider="click",
        provider_transaction_id=transaction_id,
        verified_amount=Decimal(amount),
    )


def test_successful_payment(subscription):
    settle(subscription)

    subscription.refresh_from_db()

    assert subscription.status == FootballSubscription.Status.PAID
    assert subscription.paid_at is not None

    payment = FootballAcademyPayment.objects.get(
        subscription=subscription
    )

    assert payment.status == FootballAcademyPayment.Status.SUCCEEDED
    assert payment.is_demo is False
    assert payment.provider_transaction_id == "CLICK-1001"

    revenue = RevenueEntry.objects.get(
        source="football_academy_subscription",
        source_payment_id=str(subscription.pk),
    )

    assert revenue.amount == Decimal("300000.00")
    assert revenue.category == RevenueEntry.Category.FOOTBALL


def test_duplicate_callback_is_idempotent(subscription):
    settle(subscription)
    settle(subscription)

    assert FootballAcademyPayment.objects.filter(
        subscription=subscription,
        status=FootballAcademyPayment.Status.SUCCEEDED,
    ).count() == 1

    assert RevenueEntry.objects.filter(
        source="football_academy_subscription",
        source_payment_id=str(subscription.pk),
    ).count() == 1


def test_wrong_amount_rejected(subscription):
    with pytest.raises(PaymentTransactionConflict):
        settle(subscription, amount="100000.00")

    subscription.refresh_from_db()

    assert subscription.status == FootballSubscription.Status.PENDING_PAYMENT
    assert not FootballAcademyPayment.objects.filter(
        subscription=subscription
    ).exists()


def test_expired_subscription_rejected(subscription):
    subscription.payment_expires_at = (
        timezone.now() - timedelta(minutes=1)
    )
    subscription.save(update_fields=["payment_expires_at"])

    with pytest.raises(PaymentOrderUnavailable):
        settle(subscription)

    assert not FootballAcademyPayment.objects.filter(
        subscription=subscription
    ).exists()


def test_different_transaction_after_success_rejected(subscription):
    settle(subscription, transaction_id="CLICK-1001")

    with pytest.raises(PaymentTransactionConflict):
        settle(subscription, transaction_id="CLICK-2002")

    assert FootballAcademyPayment.objects.filter(
        subscription=subscription,
        status=FootballAcademyPayment.Status.SUCCEEDED,
    ).count() == 1


def test_invalid_amount_type_rejected(subscription):
    with pytest.raises(PaymentTransactionConflict):
        confirm_football_academy_payment(
            subscription_id=subscription.pk,
            provider="click",
            provider_transaction_id="CLICK-1003",
            verified_amount=300000.0,
        )


def test_invalid_provider_rejected(subscription):
    with pytest.raises(PaymentTransactionConflict):
        confirm_football_academy_payment(
            subscription_id=subscription.pk,
            provider="unknown",
            provider_transaction_id="TEST-1004",
            verified_amount=Decimal("300000.00"),
        )