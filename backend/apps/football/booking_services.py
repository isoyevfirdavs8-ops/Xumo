from datetime import datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import FootballField, HourlyBooking, FieldClosure


TASHKENT = ZoneInfo("Asia/Tashkent")

CLOSED_START = time(16, 0)
CLOSED_END = time(20, 0)

HOLD_MINUTES = 10


def validate_booking_time(start_at, end_at):
    if timezone.is_naive(start_at) or timezone.is_naive(end_at):
        raise ValidationError(
            "Bron vaqtlari timezone-aware bo'lishi kerak."
        )

    if end_at <= start_at:
        raise ValidationError(
            "Tugash vaqti boshlanishdan keyin bo'lishi kerak."
        )

    if start_at <= timezone.now():
        raise ValidationError(
            "O'tgan vaqtga bron qilish mumkin emas."
        )

    duration = end_at - start_at

    if duration > timedelta(hours=12):
        raise ValidationError(
            "Bir bronning davomiyligi 12 soatdan oshmasligi kerak."
        )

    local_start = start_at.astimezone(TASHKENT)
    local_end = end_at.astimezone(TASHKENT)

    current_date = local_start.date()

    while current_date <= local_end.date():
        closed_start = datetime.combine(
            current_date,
            CLOSED_START,
            tzinfo=TASHKENT,
        )

        closed_end = datetime.combine(
            current_date,
            CLOSED_END,
            tzinfo=TASHKENT,
        )

        if local_start < closed_end and local_end > closed_start:
            raise ValidationError(
                "16:00 dan 20:00 gacha stadion bron qilish yopiq."
            )

        current_date += timedelta(days=1)


def expire_old_holds(field_id=None):
    now = timezone.now()

    queryset = HourlyBooking.objects.filter(
        status=HourlyBooking.Status.PENDING_PAYMENT,
        hold_expires_at__lte=now,
    )

    if field_id is not None:
        queryset = queryset.filter(field_id=field_id)

    return queryset.update(
        status=HourlyBooking.Status.EXPIRED,
        updated_at=now,
    )


def create_hourly_booking(*, user, field_id, start_at, end_at):
    validate_booking_time(start_at, end_at)

    try:
        with transaction.atomic():
            field = FootballField.objects.select_for_update().get(
                pk=field_id,
                status=FootballField.Status.ACTIVE,
            )

            expire_old_holds(field_id=field.id)

            has_closure = FieldClosure.objects.filter(
                field=field,
                start_at__lt=end_at,
                end_at__gt=start_at,
            ).exists()

            if has_closure:
                raise ValidationError(
                    "Bu vaqtda stadion vaqtincha yopilgan."
                )

            duration_hours = Decimal(
                str((end_at - start_at).total_seconds())
            ) / Decimal("3600")

            price = (
                field.hourly_price * duration_hours
            ).quantize(Decimal("0.01"))

            booking = HourlyBooking.objects.create(
                field=field,
                user=user,
                start_at=start_at,
                end_at=end_at,
                price_snapshot=price,
                status=HourlyBooking.Status.PENDING_PAYMENT,
                hold_expires_at=timezone.now()
                + timedelta(minutes=HOLD_MINUTES),
            )

            return booking

    except FootballField.DoesNotExist:
        raise ValidationError(
            "Stadion topilmadi yoki faol emas."
        )
    except IntegrityError:
        raise ValidationError(
            "Bu vaqt allaqachon band qilingan."
        )