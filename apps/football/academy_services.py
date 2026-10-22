from datetime import date, timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import FootballAcademy, FootballSubscription


@transaction.atomic
def create_football_subscription(*, user, academy_id, month):
    if not user.is_authenticated or not user.is_active:
        raise ValidationError({
            "user": "Faol foydalanuvchi talab qilinadi."
        })

    if not isinstance(month, date) or isinstance(month, __import__("datetime").datetime):
        raise ValidationError({
            "month": "To'g'ri sana kiriting."
        })

    if month.day != 1:
        raise ValidationError({
            "month": "Oyning birinchi kunini kiriting."
        })

    current_month = timezone.localdate().replace(day=1)

    if month < current_month:
        raise ValidationError({
            "month": "O'tgan oyga obuna yaratib bo'lmaydi."
        })

    academy = (
        FootballAcademy.objects
        .select_for_update()
        .filter(
            pk=academy_id,
            status=FootballAcademy.Status.ACTIVE,
        )
        .first()
    )

    if academy is None:
        raise ValidationError({
            "academy": "Faol akademiya topilmadi."
        })

    existing = (
        FootballSubscription.objects
        .select_for_update()
        .filter(
            user=user,
            academy=academy,
            month=month,
        )
        .first()
    )

    if existing is not None:
        if existing.status == FootballSubscription.Status.PENDING_PAYMENT:
            if (
                existing.payment_expires_at is not None
                and existing.payment_expires_at <= timezone.now()
            ):
                raise ValidationError({
                    "subscription": (
                        "Oldingi to'lov muddati tugagan. "
                        "To'lovni qayta boshlash uchun alohida endpoint kerak."
                    )
                })

            return existing, False

        raise ValidationError({
            "subscription": "Bu oy uchun obuna allaqachon mavjud."
        })

    subscription = FootballSubscription.objects.create(
        user=user,
        academy=academy,
        month=month,
        price_snapshot=academy.monthly_price,
        status=FootballSubscription.Status.PENDING_PAYMENT,
        payment_expires_at=timezone.now() + timedelta(minutes=15),
    )

    return subscription, True