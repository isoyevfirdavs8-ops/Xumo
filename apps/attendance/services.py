from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from apps.football.models import FootballSubscription
from apps.boxing.models import BoxingSubscription
from apps.tennis.models import TennisSubscription
from .access import require_subscription_access
from .models import Attendance


def mark_attendance(*, sport, subscription_id, date, status, user):
    if sport == "boxing":
        subscription_model = BoxingSubscription
        subscription_field = "boxing_subscription"

    elif sport == "tennis":
        subscription_model = TennisSubscription
        subscription_field = "tennis_subscription"

    elif sport == "football":
        subscription_model = FootballSubscription
        subscription_field = "football_subscription"

    else:
        raise ValidationError({
            "sport": "Sport turi noto'g'ri."
        })

    if date > timezone.localdate():
        raise ValidationError({
            "date": "Kelajakdagi sana uchun davomat belgilab bo'lmaydi."
        })

    with transaction.atomic():
        subscription = (
            subscription_model.objects
            .select_for_update()
            .filter(pk=subscription_id)
            .first()
        )

        if subscription is None:
            raise ValidationError({
                "subscription_id": "Bron topilmadi."
            })
        require_subscription_access(
            user=user,
            subscription=subscription,
            sport=sport,
        )

        if subscription.status != subscription_model.Status.PAID:
            raise ValidationError({
                "subscription_id": "Faqat to'langan bron uchun davomat mumkin."
            })

        if (
            date.year != subscription.month.year
            or date.month != subscription.month.month
        ):
            raise ValidationError({
                "date": "Davomat sanasi bron oyiga mos emas."
            })

        lookup = {
            subscription_field: subscription,
            "date": date,
        }

        attendance = (
            Attendance.objects
            .select_for_update()
            .filter(**lookup)
            .first()
        )

        created = attendance is None

        if created:
            attendance = Attendance(
                **lookup,
                status=status,
                marked_by=user,
            )
        else:
            attendance.status = status
            attendance.marked_by = user

        try:
            attendance.full_clean()
        except DjangoValidationError as exc:
            raise ValidationError(
                exc.message_dict
                if hasattr(exc, "message_dict")
                else {"detail": exc.messages}
            )

        if created:
            attendance.save(force_insert=True)
        else:
            attendance.save(
                update_fields=[
                    "status",
                    "marked_by",
                    "updated_at",
                ]
            )

        return attendance, created