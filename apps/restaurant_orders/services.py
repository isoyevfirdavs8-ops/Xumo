
from datetime import timedelta
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError
import hashlib

from django.db import connection
from apps.foods.models import Food
from .models import (
    RestaurantOrder,
    RestaurantOrderItem,
    RestaurantPayment,
)


def lock_checkout_key(key):
    """
    PostgreSQL transaction-scoped advisory lock.

    Bir xil idempotency_key bilan kelgan checkout
    so'rovlarini ketma-ket bajaradi.
    """
    key_bytes = str(key).encode("utf-8")

    digest = hashlib.sha256(key_bytes).digest()

    lock_id = int.from_bytes(
        digest[:8],
        byteorder="big",
        signed=True,
    )

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT pg_advisory_xact_lock(%s)",
            [lock_id],
        )


def create_restaurant_order(*, user, items, provider, key):
    if provider not in {
        RestaurantOrder.Provider.CLICK,
        RestaurantOrder.Provider.PAYME,
    }:
        raise ValidationError({
            "provider": "Click yoki Payme tanlang."
        })

    if not items or len(items) > 100:
        raise ValidationError({
            "items": "1 tadan 100 tagacha taom turi kiriting."
        })

    quantities = {}

    for item in items:
        food_id = item["food_id"]
        quantity = item["quantity"]

        if type(quantity) is not int or quantity <= 0:
            raise ValidationError({
                "quantity": "Miqdor musbat butun son bo'lishi kerak."
            })

        if food_id in quantities:
            raise ValidationError(
                "Bitta taomni ikki marta yubormang."
            )

        quantities[food_id] = quantity

    with transaction.atomic():
        lock_checkout_key(key)

        existing = RestaurantOrder.objects.filter(
            idempotency_key=key
        ).first()

        if existing:
            if existing.user_id != user.pk:
                raise ValidationError("Checkout kaliti band.")

            if existing.provider != provider:
                raise ValidationError(
                    "Ushbu checkout kaliti boshqa to‘lov usulida ishlatilgan."
                )

            existing_items = {
                item.food_id: item.quantity
                for item in existing.items.all()
            }
            if existing_items != quantities:
                raise ValidationError(
                    "Ushbu checkout kaliti boshqa savatcha uchun ishlatilgan."
                )

            return existing

        foods = list(
            Food.objects.select_for_update()
            .filter(pk__in=quantities.keys())
            .select_related("subcategory__category")
            .order_by("pk")
        )

        if len(foods) != len(quantities):
            raise ValidationError("Taomlardan biri topilmadi.")

        total = Decimal("0.00")

        for food in foods:
            quantity = quantities[food.pk]

            if not (
                food.is_active
                and food.subcategory.is_active
                and food.subcategory.category.is_active
            ):
                raise ValidationError(
                    f"{food.name} hozir sotuvda emas."
                )

            if food.stock < quantity:
                raise ValidationError(
                    f"{food.name}: yetarli stock mavjud emas."
                )

            total += food.price * quantity

        try:
            order = RestaurantOrder.objects.create(
                user=user,
                provider=provider,
                total_amount=total,
                idempotency_key=key,
                expires_at=timezone.now() + timedelta(minutes=15),
            )
        except IntegrityError:
            # Bir vaqtdagi duplicate so‘rovni yuqori qatlam
            # qayta o‘qib, natijani tekshirishi kerak.
            raise ValidationError(
                "Checkout so‘rovi allaqachon qayta ishlanmoqda."
            )

        order_items = []

        for food in foods:
            quantity = quantities[food.pk]

            # To‘lov davrida stock vaqtincha band qilinadi.
            food.stock -= quantity
            food.save(update_fields=["stock"])

            order_items.append(
                RestaurantOrderItem(
                    order=order,
                    food=food,
                    name=food.name,
                    quantity=quantity,
                    unit_price=food.price,
                    subtotal=food.price * quantity,
                )
            )

        RestaurantOrderItem.objects.bulk_create(order_items)

        RestaurantPayment.objects.create(
            order=order,
            provider=provider,
        )

        return order



from django.db.models import F


def expire_restaurant_order(order_id):
    with transaction.atomic():
        order = (
            RestaurantOrder.objects
            .select_for_update()
            .filter(pk=order_id)
            .first()
        )

        if order is None:
            return False

        if order.status != RestaurantOrder.Status.PENDING:
            return False

        if order.expires_at > timezone.now():
            return False

        items = list(
            order.items.order_by("food_id")
        )

        for item in items:
            Food.objects.filter(
                pk=item.food_id
            ).update(
                stock=F("stock") + item.quantity
            )

        order.status = RestaurantOrder.Status.EXPIRED
        order.save(update_fields=["status"])

        return True
