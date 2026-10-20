from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class Attendance(models.Model):
    class Status(models.TextChoices):
        PRESENT = "present", "Kelgan"
        ABSENT = "absent", "Kelmagan"

    boxing_subscription = models.ForeignKey(
        "boxing.BoxingSubscription",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="attendance_records",
    )

    tennis_subscription = models.ForeignKey(
        "tennis.TennisSubscription",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="attendance_records",
    )

    date = models.DateField(db_index=True)

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
    )

    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="marked_attendance",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-created_at"]

        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(
                        boxing_subscription__isnull=False,
                        tennis_subscription__isnull=True,
                    )
                    | Q(
                        boxing_subscription__isnull=True,
                        tennis_subscription__isnull=False,
                    )
                ),
                name="attendance_exactly_one_subscription",
            ),
            models.UniqueConstraint(
                fields=["boxing_subscription", "date"],
                condition=Q(boxing_subscription__isnull=False),
                name="unique_boxing_attendance_date",
            ),
            models.UniqueConstraint(
                fields=["tennis_subscription", "date"],
                condition=Q(tennis_subscription__isnull=False),
                name="unique_tennis_attendance_date",
            ),
        ]

    def clean(self):
        super().clean()

        has_boxing = self.boxing_subscription_id is not None
        has_tennis = self.tennis_subscription_id is not None

        if has_boxing == has_tennis:
            raise ValidationError(
                "Bitta davomat faqat boks yoki tennis broniga "
                "tegishli bo'lishi kerak."
            )

        subscription = (
            self.boxing_subscription
            if has_boxing
            else self.tennis_subscription
        )

        if subscription.status != "paid":
            raise ValidationError(
                "Faqat to'langan bron uchun davomat belgilash mumkin."
            )

        if self.date and (
            self.date.year != subscription.month.year
            or self.date.month != subscription.month.month
        ):
            raise ValidationError({
                "date": "Davomat sanasi bron qilingan oyda bo'lishi kerak."
            })

    def __str__(self):
        subscription = (
            self.boxing_subscription_id
            or self.tennis_subscription_id
        )

        return f"{subscription} | {self.date} | {self.status}"