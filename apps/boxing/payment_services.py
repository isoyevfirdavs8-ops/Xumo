
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import (
    NotFound,
    PermissionDenied,
    ValidationError,
)

from .models import BoxingSubscription, BoxingPayment


def ensure_demo_mode():
    if not (
        settings.DEBUG
        and getattr(settings, "PAYMENT_MODE", None) == "demo"
    ):
        raise PermissionDenied(
            "Demo to'lovlar ushbu muhitda o'chirilgan."
        )


@transaction.atomic
def start_demo_payment(*, user, subscription_id, provider):
    ensure_demo_mode()

    if provider not in BoxingPayment.Provider.values:
        raise ValidationError({
            "provider": "click yoki payme tanlang."
        })

    try:
        subscription = (
            BoxingSubscription.objects
            .select_for_update()
            .get(pk=subscription_id, user=user)
        )
    except BoxingSubscription.DoesNotExist:
        raise NotFound("Obuna topilmadi.")

    if subscription.status == BoxingSubscription.Status.PAID:
        raise ValidationError(
            "Bu obuna allaqachon to'langan."
        )

    if subscription.status != BoxingSubscription.Status.PENDING_PAYMENT:
        raise ValidationError(
            "Bu obuna uchun to'lovni boshlash mumkin emas."
        )

    if (
        subscription.payment_expires_at
        and subscription.payment_expires_at < timezone.now()
    ):
        # Obuna qayta ishlatiladi, narx yangilanmaydi.
        subscription.payment_expires_at = (
            timezone.now() + timedelta(minutes=30)
        )
        subscription.save(
            update_fields=["payment_expires_at", "updated_at"]
        )

    existing = (
        BoxingPayment.objects
        .filter(
            subscription=subscription,
            provider=provider,
            status=BoxingPayment.Status.PENDING,
            is_demo=True,
        )
        .order_by("-created_at")
        .first()
    )

    if existing:
        return existing

    return BoxingPayment.objects.create(
        subscription=subscription,
        provider=provider,
        amount=subscription.price_snapshot,
        status=BoxingPayment.Status.PENDING,
        is_demo=True,
    )


@transaction.atomic
def complete_demo_payment(*, user, payment_id, success):
    ensure_demo_mode()

    try:
        payment_lookup = BoxingPayment.objects.get(
            pk=payment_id,
            subscription__user=user,
        )
    except BoxingPayment.DoesNotExist:
        raise NotFound("To'lov topilmadi.")

    subscription = (
        BoxingSubscription.objects
        .select_for_update()
        .get(pk=payment_lookup.subscription_id)
    )

    payment = (
        BoxingPayment.objects
        .select_for_update()
        .get(pk=payment_lookup.pk)
    )

    if not payment.is_demo:
        raise PermissionDenied(
            "Faqat demo to'lovni tasdiqlash mumkin."
        )

    if payment.status == BoxingPayment.Status.SUCCEEDED:
        return payment

    if payment.status == BoxingPayment.Status.FAILED:
        raise ValidationError(
            "Rad etilgan to'lovni qayta tasdiqlab bo'lmaydi."
        )

    if subscription.status != BoxingSubscription.Status.PENDING_PAYMENT:
        raise ValidationError(
            "Obuna to'lov qabul qiladigan holatda emas."
        )

    if payment.amount != subscription.price_snapshot:
        raise ValidationError(
            "To'lov summasi obuna narxiga mos emas."
        )

    if success:
        other_success = BoxingPayment.objects.filter(
            subscription=subscription,
            status=BoxingPayment.Status.SUCCEEDED,
        ).exclude(pk=payment.pk).exists()

        if other_success:
            raise ValidationError(
                "Bu obuna uchun to'lov allaqachon mavjud."
            )

        payment.status = BoxingPayment.Status.SUCCEEDED
        payment.paid_at = timezone.now()
        payment.save(update_fields=["status", "paid_at"])

        subscription.status = BoxingSubscription.Status.PAID
        subscription.paid_at = payment.paid_at
        subscription.save(
            update_fields=["status", "paid_at", "updated_at"]
        )
    else:
        payment.status = BoxingPayment.Status.FAILED
        payment.save(update_fields=["status"])

    return payment
