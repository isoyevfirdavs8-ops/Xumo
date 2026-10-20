
import uuid
from django.conf import settings
from django.db import models
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
)


class Competition(models.Model):
    name = models.CharField(max_length=255)

    description = models.TextField()

    banner = models.ImageField(
        upload_to="competitions/banners/"
    )

    start_time = models.DateTimeField(
        db_index=True
    )

    min_age = models.PositiveSmallIntegerField(
        validators=[MaxValueValidator(120)]
    )

    max_age = models.PositiveSmallIntegerField(
        validators=[MaxValueValidator(120)]
    )

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    capacity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["start_time"]
        indexes = [
            models.Index(
                fields=["is_active", "start_time"]
            ),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError

        if (
            self.min_age is not None
            and self.max_age is not None
            and self.min_age > self.max_age
        ):
            raise ValidationError({
                "max_age": "Maksimal yosh minimal yoshdan kichik bo‘lmasligi kerak."
            })

    def __str__(self):
        return self.name


class TicketOrder(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Kutilmoqda"
        PAID = "paid", "To‘langan"
        FAILED = "failed", "Muvaffaqiyatsiz"
        CANCELLED = "cancelled", "Bekor qilingan"
        REFUNDED = "refunded", "Qaytarilgan"

    class Provider(models.TextChoices):
        CLICK = "click", "Click"
        PAYME = "payme", "Payme"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    payment_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
    )

    idempotency_key = models.UUIDField(
        null=True,
        blank=True,
        unique=True,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="ticket_orders",
    )

    competition = models.ForeignKey(
        Competition,
        on_delete=models.PROTECT,
        related_name="ticket_orders"
    )

    full_name = models.CharField(max_length=200)

    phone_number = models.CharField(max_length=20)

    quantity = models.PositiveSmallIntegerField(
        default=1,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(10),
        ]
    )

    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    total_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2
    )

    provider = models.CharField(
        max_length=10,
        choices=Provider.choices
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True
    )

    provider_transaction_id = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        db_index=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    paid_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        ordering = ["-created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "provider",
                    "provider_transaction_id",
                ],
                condition=(
                        models.Q(
                            provider_transaction_id__isnull=False
                        )
                        & ~models.Q(provider_transaction_id="")
                ),
                name="unique_competition_provider_transaction",
            ),
        ]


class Ticket(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    order = models.ForeignKey(
        TicketOrder,
        on_delete=models.PROTECT,
        related_name="tickets"
    )

    ticket_number = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    is_used = models.BooleanField(default=False)

    used_at = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return str(self.ticket_number)

