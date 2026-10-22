
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import RangeOperators
from django.contrib.postgres.indexes import GistIndex
from django.contrib.postgres.fields.ranges import DateTimeRangeField
from django.db.models import Func
import uuid
from django.core.exceptions import ValidationError
from decimal import Decimal

class FootballField(models.Model):
    class FieldType(models.TextChoices):
        SUMMER = "summer", "Yozgi"
        WINTER = "winter", "Qishki"
        OTHER = "other", "Boshqa"

    class Status(models.TextChoices):
        ACTIVE = "active", "Faol"
        MAINTENANCE = "maintenance", "Ta'mirlashda"
        ARCHIVED = "archived", "Arxivlangan"

    name = models.CharField(
        max_length=150,
        unique=True,
        verbose_name="Stadion nomi",
    )

    field_type = models.CharField(
        max_length=20,
        choices=FieldType.choices,
        default=FieldType.SUMMER,
    )

    description = models.TextField(blank=True)

    hourly_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    capacity = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    length_m = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    width_m = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    has_lighting = models.BooleanField(default=True)
    has_changing_room = models.BooleanField(default=False)

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
        verbose_name = "Futbol maydoni"
        verbose_name_plural = "Futbol maydonlari"

    def __str__(self):
        return self.name


class FootballFieldImage(models.Model):
    field = models.ForeignKey(
        FootballField,
        on_delete=models.CASCADE,
        related_name="images",
    )

    image = models.ImageField(
        upload_to="football/fields/%Y/%m/",
    )

    is_primary = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"{self.field.name} - rasm #{self.pk}"


class FieldPriceHistory(models.Model):
    field = models.ForeignKey(
        FootballField,
        on_delete=models.PROTECT,
        related_name="price_history",
    )

    old_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    new_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-changed_at"]

    def __str__(self):
        return f"{self.field.name}: {self.old_price} -> {self.new_price}"



class BookingTimeRange(Func):
    function = "TSTZRANGE"
    template = "%(function)s(%(expressions)s, '[)')"
    output_field = DateTimeRangeField()


class HourlyBooking(models.Model):

    class Status(models.TextChoices):
        PENDING_PAYMENT = "pending_payment", "To'lov kutilmoqda"
        CONFIRMED = "confirmed", "Tasdiqlangan"
        CANCELLED = "cancelled", "Bekor qilingan"
        EXPIRED = "expired", "Muddati tugagan"

    field = models.ForeignKey(
        "FootballField",
        on_delete=models.PROTECT,
        related_name="bookings",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="football_bookings",
    )

    start_at = models.DateTimeField()
    end_at = models.DateTimeField()

    # PostgreSQL avtomatik hisoblaydigan vaqt oralig'i
    time_range = models.GeneratedField(
        expression=BookingTimeRange(
            models.F("start_at"),
            models.F("end_at"),
        ),
        output_field=DateTimeRangeField(),
        db_persist=True,
    )

    price_snapshot = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING_PAYMENT,
        db_index=True,
    )

    hold_expires_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

        constraints = [
            ExclusionConstraint(
                name="no_overlapping_active_field_bookings",
                expressions=[
                    ("field", RangeOperators.EQUAL),
                    ("time_range", RangeOperators.OVERLAPS),
                ],
                condition=Q(
                    status__in=[
                        "pending_payment",
                        "confirmed",
                    ]
                ),
            ),

            models.CheckConstraint(
                name="football_booking_end_after_start",
                condition=Q(
                    end_at__gt=models.F("start_at")
                ),
            ),
        ]

    def __str__(self):
        return (
            f"{self.field.name} | "
            f"{self.start_at} - {self.end_at}"
        )


class FieldClosure(models.Model):
    field = models.ForeignKey(
        "FootballField",
        on_delete=models.PROTECT,
        related_name="closures",
    )

    start_at = models.DateTimeField()
    end_at = models.DateTimeField()

    reason = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["start_at"]

        constraints = [
            models.CheckConstraint(
                name="football_closure_end_after_start",
                condition=Q(end_at__gt=models.F("start_at")),
            ),
        ]

    def __str__(self):
        return f"{self.field} | {self.start_at} - {self.end_at}"





import uuid

from django.db import models
from django.db.models import Q


class FootballPayment(models.Model):

    class Provider(models.TextChoices):
        CLICK = "click", "Click"
        PAYME = "payme", "Payme"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    booking = models.ForeignKey(
        "HourlyBooking",
        on_delete=models.PROTECT,
        related_name="payments",
    )

    provider = models.CharField(
        max_length=10,
        choices=Provider.choices,
    )

    provider_transaction_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    is_demo = models.BooleanField(default=False)

    paid_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["booking"],
                condition=Q(status="succeeded"),
                name="unique_success_football_payment",
            ),
            models.UniqueConstraint(
                fields=["provider", "provider_transaction_id"],
                condition=Q(
                    provider_transaction_id__isnull=False
                ),
                name="unique_football_provider_tx",
            ),
        ]

    def __str__(self):
        return f"{self.booking_id} - {self.status}"


class FootballAcademy(models.Model):
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
        validators=[MinValueValidator(Decimal("0.01"))],
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
        verbose_name = "Futbol akademiyasi"
        verbose_name_plural = "Futbol akademiyalari"

        constraints = [
            models.CheckConstraint(
                condition=Q(monthly_price__gt=0),
                name="football_academy_positive_price",
            ),
        ]

    def __str__(self):
        return self.name


class FootballAcademyImage(models.Model):
    academy = models.ForeignKey(
        FootballAcademy,
        on_delete=models.CASCADE,
        related_name="images",
    )

    image = models.ImageField(
        upload_to="football/academies/%Y/%m/",
    )

    is_primary = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"{self.academy.name} - rasm {self.pk}"


class FootballSubscription(models.Model):
    class Status(models.TextChoices):
        PENDING_PAYMENT = "pending_payment", "To'lov kutilmoqda"
        PAID = "paid", "To'langan"
        CANCELLED = "cancelled", "Bekor qilingan"
        EXPIRED = "expired", "Muddati tugagan"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="football_academy_subscriptions",
    )

    academy = models.ForeignKey(
        FootballAcademy,
        on_delete=models.PROTECT,
        related_name="subscriptions",
    )

    month = models.DateField()

    price_snapshot = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
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
                name="unique_football_academy_user_month",
            ),
            models.CheckConstraint(
                condition=Q(price_snapshot__gt=0),
                name="football_subscription_positive_price",
            ),
            models.CheckConstraint(
                condition=Q(month__day=1),
                name="football_subscription_first_day",
            ),
        ]

        indexes = [
            models.Index(
                fields=["academy", "month", "status"],
                name="football_sub_academy_idx",
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


class FootballAcademyPayment(models.Model):
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
        FootballSubscription,
        on_delete=models.PROTECT,
        related_name="payments",
    )

    provider = models.CharField(
        max_length=10,
        choices=Provider.choices,
    )

    provider_transaction_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
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

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name="football_academy_payment_positive",
            ),
            models.UniqueConstraint(
                fields=["subscription"],
                condition=Q(status="succeeded"),
                name="football_academy_one_success",
            ),
            models.UniqueConstraint(
                fields=["provider", "provider_transaction_id"],
                condition=Q(provider_transaction_id__isnull=False),
                name="unique_football_academy_provider_tx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.provider} | "
            f"{self.amount} | {self.status}"
        )