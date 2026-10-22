from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone

from apps.finance.models import RevenueEntry
from apps.finance.recording import record_successful_payment
from apps.payments.exceptions import (
    PaymentOrderUnavailable,
    PaymentTransactionConflict,
)

from .models import (
    FootballSubscription,
    FootballAcademyPayment,
)


@transaction.atomic
def confirm_football_academy_payment(
    *,
    subscription_id,
    provider,
    provider_transaction_id,
    verified_amount,
):
    if provider not in FootballAcademyPayment.Provider.values:
        raise PaymentTransactionConflict()

    if not provider_transaction_id:
        raise PaymentTransactionConflict()

    provider_transaction_id = str(provider_transaction_id)

    if isinstance(verified_amount, (float, bool)):
        raise PaymentTransactionConflict()

    try:
        amount = Decimal(str(verified_amount))
    except (InvalidOperation, TypeError, ValueError):
        raise PaymentTransactionConflict()

    if (
        not amount.is_finite()
        or amount <= 0
        or amount != amount.quantize(Decimal("0.01"))
    ):
        raise PaymentTransactionConflict()

    # Lock tartibi: avval subscription, keyin payment.
    subscription = (
        FootballSubscription.objects
        .select_for_update(of=("self",))
        .select_related("user")
        .get(pk=subscription_id)
    )

    if amount != subscription.price_snapshot:
        raise PaymentTransactionConflict()

    existing = (
        FootballAcademyPayment.objects
        .select_for_update()
        .filter(
            subscription=subscription,
            status=FootballAcademyPayment.Status.SUCCEEDED,
        )
        .first()
    )

    if existing:
        if (
            existing.provider != provider
            or existing.provider_transaction_id
            != provider_transaction_id
            or existing.amount != amount
            or subscription.status != FootballSubscription.Status.PAID
        ):
            raise PaymentTransactionConflict()

        return subscription

    if subscription.status != FootballSubscription.Status.PENDING_PAYMENT:
        raise PaymentOrderUnavailable()

    now = timezone.now()

    if (
        subscription.payment_expires_at is None
        or subscription.payment_expires_at <= now
    ):
        raise PaymentOrderUnavailable()

    FootballAcademyPayment.objects.create(
        subscription=subscription,
        provider=provider,
        provider_transaction_id=provider_transaction_id,
        amount=amount,
        status=FootballAcademyPayment.Status.SUCCEEDED,
        is_demo=False,
        paid_at=now,
    )

    subscription.status = FootballSubscription.Status.PAID
    subscription.paid_at = now
    subscription.save(
        update_fields=["status", "paid_at", "updated_at"]
    )

    record_successful_payment(
        category=RevenueEntry.Category.FOOTBALL,
        source="football_academy_subscription",
        source_payment_id=str(subscription.pk),
        amount=amount,
        provider=provider,
        user=subscription.user,
        paid_at=now,
    )

    return subscription