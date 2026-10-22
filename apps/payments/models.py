
from django.db import models


class ClickTransaction(models.Model):
    class Status(models.TextChoices):
        PREPARED = "prepared", "Prepared"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    click_trans_id = models.CharField(
        max_length=100,
        unique=True,
    )

    click_paydoc_id = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )

    merchant_prepare_id = models.BigAutoField(
        primary_key=True,
    )

    category = models.CharField(
        max_length=30,
        choices=[
            ("restaurant", "Restaurant"),
            ("competition", "Competition"),
            ("football", "Football"),
            ("football_academy", "Football Academy"),
            ("hostel", "Hostel"),
        ],
    )

    order_id = models.CharField(max_length=100)

    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PREPARED,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["category", "order_id"],
                condition=models.Q(status="prepared"),
                name="unique_prepared_click_order",
            ),

            models.UniqueConstraint(
                fields=["category", "order_id"],
                condition=models.Q(status="completed"),
                name="unique_completed_click_order",
            ),

            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="click_transaction_positive_amount",
            ),
        ]

        indexes = [
            models.Index(
                fields=["category", "order_id"],
            ),
        ]


class PaymentReconciliationAudit(models.Model):
    class Result(models.TextChoices):
        STALE_PREPARED = (
            "stale_prepared",
            "Stale prepared",
        )
        VERIFIED = "verified", "Verified"
        FAILED = "failed", "Failed"
        MANUAL_REVIEW = (
            "manual_review",
            "Manual review",
        )

    provider = models.CharField(
        max_length=20,
        default="click",
    )

    transaction_id = models.CharField(
        max_length=100,
        db_index=True,
    )

    category = models.CharField(
        max_length=30,
    )

    order_id = models.CharField(
        max_length=100,
    )

    result = models.CharField(
        max_length=30,
        choices=Result.choices,
    )

    details = models.JSONField(
        default=dict,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        ordering = ["-created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "provider",
                    "transaction_id",
                    "result",
                ],
                condition=models.Q(
                    result="stale_prepared"
                ),
                name="unique_stale_payment_audit",
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    "provider",
                    "result",
                    "created_at",
                ],
                name="payment_audit_lookup_idx",
            ),
        ]
