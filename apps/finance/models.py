
import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q


class RevenueEntry(models.Model):
    class Category(models.TextChoices):
        FOOTBALL = "football", "Futbol"
        TENNIS = "tennis", "Tennis"
        BOXING = "boxing", "Boks"
        RESTAURANT = "restaurant", "Restoran"
        TOURNAMENT = "tournament", "Musobaqalar"

    class EntryType(models.TextChoices):
        PAYMENT = "payment", "To'lov"
        REFUND = "refund", "Qaytarilgan to'lov"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        db_index=True,
    )

    entry_type = models.CharField(
        max_length=10,
        choices=EntryType.choices,
        default=EntryType.PAYMENT,
    )

    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )

    # Har bir to'lov manbasining takrorlanmas identifikatori.
    source = models.CharField(max_length=50)
    source_payment_id = models.CharField(max_length=100)

    provider = models.CharField(
        max_length=30,
        blank=True,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="revenue_entries",
    )

    # Haqiqiy pul tushgan yoki qaytarilgan vaqt.
    occurred_at = models.DateTimeField(db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-occurred_at"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "source",
                    "source_payment_id",
                    "entry_type",
                ],
                name="unique_finance_source_event",
            ),
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name="finance_positive_amount",
            ),
        ]

        indexes = [
            models.Index(
                fields=["category", "occurred_at"],
                name="finance_category_date_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.category} | {self.entry_type} | "
            f"{self.amount}"
        )

