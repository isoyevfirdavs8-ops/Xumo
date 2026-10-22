
import uuid
from django.conf import settings
from django.db import models


class RestaurantOrder(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "To‘lov kutilmoqda"
        PAID = "paid", "To‘langan"
        CANCELLED = "cancelled", "Bekor qilingan"
        EXPIRED = "expired", "Muddati tugagan"
        REFUNDED = "refunded", "Qaytarilgan"

    class FulfillmentStatus(models.TextChoices):
        NEW = "new", "Yangi buyurtma"
        ACCEPTED = "accepted", "Qabul qilindi"
        PREPARING = "preparing", "Tayyorlanmoqda"
        DELIVERED = "delivered", "Yetkazib berildi"

    class Provider(models.TextChoices):
        CLICK = "click", "Click"
        PAYME = "payme", "Payme"

    fulfillment_status = models.CharField(
        max_length=20,
        choices=FulfillmentStatus.choices,
        default=FulfillmentStatus.NEW,
        db_index=True,
    )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="restaurant_orders",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    provider = models.CharField(
        max_length=10,
        choices=Provider.choices,
    )
    total_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
    )
    idempotency_key = models.UUIDField(
        unique=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]


class RestaurantOrderItem(models.Model):
    order = models.ForeignKey(
        RestaurantOrder,
        on_delete=models.PROTECT,
        related_name="items",
    )
    food = models.ForeignKey(
        "foods.Food",
        on_delete=models.PROTECT,
    )
    name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    subtotal = models.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["order", "food"],
                name="unique_food_per_restaurant_order",
            )
        ]


class RestaurantPayment(models.Model):
    order = models.OneToOneField(
        RestaurantOrder,
        on_delete=models.PROTECT,
        related_name="payment",
    )
    provider = models.CharField(max_length=10)
    provider_transaction_id = models.CharField(
        max_length=150,
        null=True,
        blank=True,
    )
    provider_state = models.CharField(
        max_length=40,
        default="created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "provider_transaction_id"],
                name="unique_restaurant_provider_transaction",
            )
        ]

