
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q


class BoxingAcademy(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Faol"
        MAINTENANCE = "maintenance", "Ta'mirlashda"
        ARCHIVED = "archived", "Arxivlangan"

    name = models.CharField(
        max_length=150,
        unique=True,
    )
    description = models.TextField(blank=True)

    monthly_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]
        verbose_name = "Boks akademiyasi"
        verbose_name_plural = "Boks akademiyalari"

    def __str__(self):
        return self.name


class BoxingAcademyImage(models.Model):
    academy = models.ForeignKey(
        BoxingAcademy,
        on_delete=models.CASCADE,
        related_name="images",
    )

    image = models.ImageField(
        upload_to="boxing/academies/%Y/%m/",
    )

    is_primary = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"{self.academy.name} - rasm {self.pk}"


class BoxingSubscription(models.Model):
    class Status(models.TextChoices):
        PENDING_PAYMENT = "pending_payment", "To'lov kutilmoqda"
        PAID = "paid", "To'langan"
        CANCELLED = "cancelled", "Bekor qilingan"
        EXPIRED = "expired", "Muddati tugagan"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="boxing_subscriptions",
    )

    academy = models.ForeignKey(
        BoxingAcademy,
        on_delete=models.PROTECT,
        related_name="subscriptions",
    )

    # Masalan: 2026-11-01 = 2026-yil noyabr
    month = models.DateField()

    price_snapshot = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING_PAYMENT,
        db_index=True,
    )

    payment_expires_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    paid_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["user", "academy", "month"],
                name="unique_boxing_user_academy_month",
            ),
            models.CheckConstraint(
                condition=Q(price_snapshot__gt=0),
                name="boxing_subscription_positive_price",
            ),
        ]

    def clean(self):
        super().clean()

        if self.month and self.month.day != 1:
            raise ValidationError({
                "month": "Oyning birinchi kunini kiriting."
            })

    def __str__(self):
        return (
            f"{self.user} | {self.academy.name} | "
            f"{self.month:%Y-%m}"
        )


class BoxingPayment(models.Model):
    class Provider(models.TextChoices):
        CLICK = "click", "Click"
        PAYME = "payme", "Payme"

    class Status(models.TextChoices):
        PENDING = "pending", "Kutilmoqda"
        SUCCEEDED = "succeeded", "Muvaffaqiyatli"
        FAILED = "failed", "Muvaffaqiyatsiz"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    subscription = models.ForeignKey(
        BoxingSubscription,
        on_delete=models.PROTECT,
        related_name="payments",
    )

    provider = models.CharField(
        max_length=10,
        choices=Provider.choices,
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    is_demo = models.BooleanField(default=True)

    paid_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]

        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name="boxing_payment_positive_amount",
            ),
            models.UniqueConstraint(
                fields=["subscription"],
                condition=Q(status="succeeded"),
                name="boxing_one_successful_payment",
            ),
        ]

    def __str__(self):
        return (
            f"{self.provider} | "
            f"{self.amount} | {self.status}"
        )

