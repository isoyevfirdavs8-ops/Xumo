
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import (
    PermissionDenied,
    ValidationError,
)

from .models import TennisPayment, TennisSubscription


def ensure_demo_mode():
    if (
        not settings.DEBUG
        or settings.PAYMENT_MODE != "demo"
    ):
        raise PermissionDenied(
            "Demo to'lov rejimi o'chirilgan."
        )


@transaction.atomic
def create_demo_payment(*, user, subscription_id, provider):
    ensure_demo_mode()

    if provider not in TennisPayment.Provider.values:
        raise ValidationError({
            "provider": "Click yoki Payme tanlang."
        })

    subscription = (
        TennisSubscription.objects
        .select_for_update()
        .select_related("court")
        .get(pk=subscription_id, user=user)
    )

    if subscription.status == TennisSubscription.Status.PAID:
        raise ValidationError(
            "Bu obuna allaqachon to'langan."
        )

    if subscription.status != (
        TennisSubscription.Status.PENDING_PAYMENT
    ):
        raise ValidationError(
            "Ushbu obuna to'lov uchun faol emas."
        )

    if subscription.court.status != "active":
        raise ValidationError(
            "Tennis korti hozir faol emas."
        )

    payment = (
        TennisPayment.objects
        .filter(
            subscription=subscription,
            status=TennisPayment.Status.PENDING,
        )
        .order_by("-created_at")
        .first()
    )

    if payment:
        if payment.provider == provider:
            return payment

        payment.status = TennisPayment.Status.FAILED
        payment.save(update_fields=["status"])

    return TennisPayment.objects.create(
        subscription=subscription,
        provider=provider,
        amount=subscription.price_snapshot,
        status=TennisPayment.Status.PENDING,
        is_demo=True,
    )


@transaction.atomic
def complete_demo_payment(*, user, payment_id, success):
    ensure_demo_mode()

    # Obunani avval lock qilamiz. Barcha to'lov
    # operatsiyalarida lock tartibi bir xil.
    payment_info = (
        TennisPayment.objects
        .filter(pk=payment_id, subscription__user=user)
        .values("subscription_id")
        .first()
    )

    if not payment_info:
        raise ValidationError("To'lov topilmadi.")

    subscription = (
        TennisSubscription.objects
        .select_for_update()
        .get(pk=payment_info["subscription_id"], user=user)
    )

    payment = (
        TennisPayment.objects
        .select_for_update()
        .get(pk=payment_id, subscription=subscription)
    )

    if not payment.is_demo:
        raise ValidationError(
            "Bu test to'lovi emas."
        )

    if payment.status != TennisPayment.Status.PENDING:
        return payment

    if subscription.status != (
        TennisSubscription.Status.PENDING_PAYMENT
    ):
        raise ValidationError(
            "Obuna holati to'lovga ruxsat bermaydi."
        )

    if payment.amount != subscription.price_snapshot:
        raise ValidationError(
            "To'lov summasi mos kelmadi."
        )

    if not success:
        payment.status = TennisPayment.Status.FAILED
        payment.save(update_fields=["status"])
        return payment

    now = timezone.now()

    payment.status = TennisPayment.Status.SUCCEEDED
    payment.paid_at = now
    payment.save(update_fields=["status", "paid_at"])

    subscription.status = TennisSubscription.Status.PAID
    subscription.paid_at = now
    subscription.save(
        update_fields=["status", "paid_at", "updated_at"]
    )

    return payment
