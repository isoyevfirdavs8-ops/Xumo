
from django.conf import settings
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateRangeField, RangeOperators
from django.contrib.postgres.indexes import GistIndex
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q


class HostelRoom(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Faol"
        MAINTENANCE = "maintenance", "Ta'mirlashda"
        ARCHIVED = "archived", "Arxivlangan"

    number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Xona raqami",
    )
    name = models.CharField(
        max_length=150,
        verbose_name="Xona nomi",
    )
    description = models.TextField(blank=True)

    capacity = models.PositiveSmallIntegerField(
        choices=[
            (2, "2 kishilik"),
            (3, "3 kishilik"),
            (4, "4 kishilik"),
        ],
        verbose_name="Sig'imi",
    )

    daily_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(1)],
        verbose_name="Kunlik narx",
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
        ordering = ["number"]
        verbose_name = "Yotoqxona xonasi"
        verbose_name_plural = "Yotoqxona xonalari"

    def __str__(self):
        return f"{self.number} — {self.name} ({self.capacity} kishilik)"


class HostelRoomImage(models.Model):
    room = models.ForeignKey(
        HostelRoom,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(
        upload_to="hostel/rooms/%Y/%m/",
    )
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_primary", "id"]

    def __str__(self):
        return f"{self.room.number} rasmi"


class HostelReservation(models.Model):
    class Status(models.TextChoices):
        PENDING_PAYMENT = "pending_payment", "To'lov kutilmoqda"
        PAID = "paid", "To'langan"
        CANCELLED = "cancelled", "Bekor qilingan"
        EXPIRED = "expired", "Muddati tugagan"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="hostel_reservations",
    )

    check_in = models.DateField()
    check_out = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING_PAYMENT,
        db_index=True,
    )
    idempotency_key = models.UUIDField(
        null=True,
        blank=True,
        unique=True,
        editable=False,
    )

    total_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
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
            models.CheckConstraint(
                condition=Q(check_out__gt=models.F("check_in")),
                name="hostel_reservation_valid_dates",
            ),
        ]

    def clean(self):
        super().clean()

        if (
            self.check_in is not None
            and self.check_out is not None
            and self.check_out <= self.check_in
        ):
            raise ValidationError({
                "check_out": "Ketish sanasi kelish sanasidan keyin bo'lishi kerak."
            })

    @property
    def nights(self):
        return (self.check_out - self.check_in).days

    def __str__(self):
        return f"Hostel rezervatsiya #{self.pk}"


class HostelBooking(models.Model):
    class Status(models.TextChoices):
        PENDING_PAYMENT = "pending_payment", "To'lov kutilmoqda"
        PAID = "paid", "To'langan"
        CANCELLED = "cancelled", "Bekor qilingan"
        EXPIRED = "expired", "Muddati tugagan"

    reservation = models.ForeignKey(
        HostelReservation,
        on_delete=models.PROTECT,
        related_name="bookings",
    )

    room = models.ForeignKey(
        HostelRoom,
        on_delete=models.PROTECT,
        related_name="bookings",
    )

    # PostgreSQL daterange: [check_in, check_out)
    # Kelish kuni band, ketish kuni bo'sh.
    stay_period = DateRangeField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING_PAYMENT,
        db_index=True,
    )

    daily_price_snapshot = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(1)],
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            GistIndex(fields=["stay_period"]),
        ]
        constraints = [
            ExclusionConstraint(
                name="hostel_prevent_overlapping_bookings",
                expressions=[
                    ("room", RangeOperators.EQUAL),
                    ("stay_period", RangeOperators.OVERLAPS),
                ],
                condition=Q(
                    status__in=[
                        "pending_payment",
                        "paid",
                    ]
                ),
            ),
        ]

    def __str__(self):
        return f"Xona {self.room.number} — rezervatsiya #{self.reservation_id}"
