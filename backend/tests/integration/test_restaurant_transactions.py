
import uuid
from decimal import Decimal
from unittest.mock import patch

import pytest

from django.contrib.auth import get_user_model
from django.db import IntegrityError

from apps.categories.models import Category, SubCategory
from apps.foods.models import Food
from apps.restaurant_orders.models import (
    RestaurantOrder,
    RestaurantOrderItem,
    RestaurantPayment,
)
from apps.restaurant_orders.services import create_restaurant_order
from apps.finance.models import RevenueEntry
from apps.finance.payment_settlement import settle_restaurant_payment


@pytest.fixture
def transaction_user(db):
    User = get_user_model()

    return User.objects.create_user(
        phone_number="+998901234570",
        password="TestPassword123!",
    )


@pytest.fixture
def transaction_food(db):
    category = Category.objects.create(
        name="Transaction Test Category",
        slug="transaction-test-category",
        image="categories/test.jpg",
        is_active=True,
    )

    subcategory = SubCategory.objects.create(
        category=category,
        name="Transaction Test Subcategory",
        is_active=True,
    )

    return Food.objects.create(
        subcategory=subcategory,
        name="Transaction Test Burger",
        price=Decimal("35000.00"),
        stock=10,
        is_active=True,
    )


@pytest.mark.django_db
def test_order_creation_rolls_back_when_payment_creation_fails(
    transaction_user,
    transaction_food,
):
    with patch.object(
        RestaurantPayment.objects,
        "create",
        side_effect=RuntimeError("Simulated payment failure"),
    ):
        with pytest.raises(RuntimeError):
            create_restaurant_order(
                user=transaction_user,
                items=[
                    {
                        "food_id": transaction_food.pk,
                        "quantity": 3,
                    }
                ],
                provider="click",
                key=uuid.uuid4(),
            )

    transaction_food.refresh_from_db()

    assert transaction_food.stock == 10
    assert RestaurantOrder.objects.count() == 0
    assert RestaurantOrderItem.objects.count() == 0
    assert RestaurantPayment.objects.count() == 0


@pytest.mark.django_db
def test_payment_settlement_rolls_back_when_revenue_fails(
    transaction_user,
    transaction_food,
):
    order = create_restaurant_order(
        user=transaction_user,
        items=[
            {
                "food_id": transaction_food.pk,
                "quantity": 2,
            }
        ],
        provider="click",
        key=uuid.uuid4(),
    )

    with patch(
        "apps.finance.payment_settlement.record_successful_payment",
        side_effect=RuntimeError("Simulated finance failure"),
    ):
        with pytest.raises(RuntimeError):
            settle_restaurant_payment(
                order_id=order.pk,
                provider="click",
                provider_transaction_id="rollback-test-001",
            )

    order.refresh_from_db()
    payment = RestaurantPayment.objects.get(order=order.pk)
    transaction_food.refresh_from_db()

    assert order.status == RestaurantOrder.Status.PENDING
    assert order.paid_at is None
    assert payment.provider_state == "created"
    assert payment.provider_transaction_id is None

    # Buyurtma hali PENDING: rezerv saqlanadi.
    assert transaction_food.stock == 8

    assert RevenueEntry.objects.count() == 0


@pytest.mark.django_db
def test_payment_can_be_retried_after_rollback(
    transaction_user,
    transaction_food,
):
    order = create_restaurant_order(
        user=transaction_user,
        items=[
            {
                "food_id": transaction_food.pk,
                "quantity": 2,
            }
        ],
        provider="click",
        key=uuid.uuid4(),
    )

    with patch(
        "apps.finance.payment_settlement.record_successful_payment",
        side_effect=RuntimeError("Temporary finance failure"),
    ):
        with pytest.raises(RuntimeError):
            settle_restaurant_payment(
                order_id=order.pk,
                provider="click",
                provider_transaction_id="rollback-test-002",
            )

    paid_order = settle_restaurant_payment(
        order_id=order.pk,
        provider="click",
        provider_transaction_id="rollback-test-002",
    )

    assert paid_order.status == RestaurantOrder.Status.PAID

    assert RevenueEntry.objects.filter(
        source="restaurant_order",
        source_payment_id=str(order.pk),
        entry_type=RevenueEntry.EntryType.PAYMENT,
    ).count() == 1


@pytest.mark.django_db
def test_duplicate_checkout_key_does_not_reserve_twice(
    transaction_user,
    transaction_food,
):
    key = uuid.uuid4()

    kwargs = {
        "user": transaction_user,
        "items": [
            {
                "food_id": transaction_food.pk,
                "quantity": 4,
            }
        ],
        "provider": "click",
        "key": key,
    }

    first = create_restaurant_order(**kwargs)
    second = create_restaurant_order(**kwargs)

    transaction_food.refresh_from_db()

    assert first.pk == second.pk
    assert transaction_food.stock == 6
    assert RestaurantOrder.objects.count() == 1
