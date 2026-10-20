
import uuid
from datetime import timedelta
from decimal import Decimal

import pytest

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.categories.models import Category, SubCategory
from apps.foods.models import Food
from apps.restaurant_orders.models import (
    RestaurantOrder,
    RestaurantOrderItem,
    RestaurantPayment,
)
from apps.restaurant_orders.services import (
    create_restaurant_order,
    expire_restaurant_order,
)
from apps.finance.models import RevenueEntry
from apps.finance.payment_settlement import (
    settle_restaurant_payment,
)

from apps.payments.exceptions import (
    PaymentOrderUnavailable,
    PaymentTransactionConflict,
)

@pytest.fixture
def restaurant_user(db):
    User = get_user_model()

    return User.objects.create_user(
        phone_number="+998901234569",
        password="TestPassword123!",
    )



@pytest.fixture
def restaurant_food(db):
    category = Category.objects.create(
        name="Test Restaurant Category",
        slug="test-restaurant-category",
        image="categories/test-category.jpg",
        is_active=True,
    )

    subcategory = SubCategory.objects.create(
        category=category,
        name="Test Restaurant Subcategory",
        is_active=True,
    )

    return Food.objects.create(
        subcategory=subcategory,
        name="Test Burger",
        price=Decimal("35000.00"),
        stock=20,
        is_active=True,
    )


@pytest.fixture
def pending_restaurant_order(
    restaurant_user,
    restaurant_food,
):
    return create_restaurant_order(
        user=restaurant_user,
        items=[
            {
                "food_id": restaurant_food.pk,
                "quantity": 2,
            }
        ],
        provider=RestaurantOrder.Provider.CLICK,
        key=uuid.uuid4(),
    )


@pytest.mark.django_db
def test_create_order_reserves_stock(
    pending_restaurant_order,
    restaurant_food,
):
    order = pending_restaurant_order

    restaurant_food.refresh_from_db()

    assert order.status == RestaurantOrder.Status.PENDING
    assert order.total_amount == Decimal("70000.00")
    assert restaurant_food.stock == 18

    assert RestaurantOrderItem.objects.filter(
        order=order
    ).count() == 1

    payment = RestaurantPayment.objects.get(order=order)

    assert payment.provider == "click"
    assert payment.provider_state == "created"


@pytest.mark.django_db
def test_duplicate_checkout_is_idempotent(
    restaurant_user,
    restaurant_food,
):
    key = uuid.uuid4()

    kwargs = {
        "user": restaurant_user,
        "items": [
            {
                "food_id": restaurant_food.pk,
                "quantity": 2,
            }
        ],
        "provider": "click",
        "key": key,
    }

    first = create_restaurant_order(**kwargs)
    second = create_restaurant_order(**kwargs)

    assert first.pk == second.pk
    assert RestaurantOrder.objects.count() == 1

    restaurant_food.refresh_from_db()
    assert restaurant_food.stock == 18


@pytest.mark.django_db
def test_insufficient_stock_rejected(
    restaurant_user,
    restaurant_food,
):
    with pytest.raises(ValidationError):
        create_restaurant_order(
            user=restaurant_user,
            items=[
                {
                    "food_id": restaurant_food.pk,
                    "quantity": 21,
                }
            ],
            provider="click",
            key=uuid.uuid4(),
        )

    restaurant_food.refresh_from_db()

    assert restaurant_food.stock == 20
    assert RestaurantOrder.objects.count() == 0


@pytest.mark.django_db
def test_duplicate_food_rejected(
    restaurant_user,
    restaurant_food,
):
    with pytest.raises(ValidationError):
        create_restaurant_order(
            user=restaurant_user,
            items=[
                {
                    "food_id": restaurant_food.pk,
                    "quantity": 1,
                },
                {
                    "food_id": restaurant_food.pk,
                    "quantity": 2,
                },
            ],
            provider="click",
            key=uuid.uuid4(),
        )

    assert RestaurantOrder.objects.count() == 0


@pytest.mark.django_db
def test_successful_payment_marks_order_paid(
    pending_restaurant_order,
):
    order = settle_restaurant_payment(
        order_id=pending_restaurant_order.pk,
        provider="click",
        provider_transaction_id="restaurant-click-001",
    )

    order.refresh_from_db()

    assert order.status == RestaurantOrder.Status.PAID
    assert order.paid_at is not None

    payment = order.payment
    payment.refresh_from_db()

    assert payment.provider_transaction_id == "restaurant-click-001"
    assert payment.provider_state == "succeeded"


@pytest.mark.django_db
def test_successful_payment_creates_revenue(
    pending_restaurant_order,
):
    order = settle_restaurant_payment(
        order_id=pending_restaurant_order.pk,
        provider="click",
        provider_transaction_id="restaurant-click-002",
    )

    revenue = RevenueEntry.objects.get(
        source="restaurant_order",
        source_payment_id=str(order.pk),
        entry_type=RevenueEntry.EntryType.PAYMENT,
    )

    assert revenue.category == RevenueEntry.Category.RESTAURANT
    assert revenue.amount == Decimal("70000.00")
    assert revenue.provider == "click"
    assert revenue.user_id == order.user_id


@pytest.mark.django_db
def test_duplicate_payment_callback_is_idempotent(
    pending_restaurant_order,
):
    kwargs = {
        "order_id": pending_restaurant_order.pk,
        "provider": "click",
        "provider_transaction_id": "restaurant-click-003",
    }

    first = settle_restaurant_payment(**kwargs)
    second = settle_restaurant_payment(**kwargs)

    assert first.pk == second.pk

    assert RevenueEntry.objects.filter(
        source="restaurant_order",
        source_payment_id=str(first.pk),
        entry_type=RevenueEntry.EntryType.PAYMENT,
    ).count() == 1


@pytest.mark.django_db
def test_different_transaction_rejected(
    pending_restaurant_order,
):
    settle_restaurant_payment(
        order_id=pending_restaurant_order.pk,
        provider="click",
        provider_transaction_id="restaurant-click-004",
    )

    with pytest.raises(PaymentTransactionConflict):
        settle_restaurant_payment(
            order_id=pending_restaurant_order.pk,
            provider="click",
            provider_transaction_id="restaurant-click-005",
        )

    assert RevenueEntry.objects.count() == 1


@pytest.mark.django_db
def test_wrong_provider_rejected(
    pending_restaurant_order,
):
    with pytest.raises(PaymentTransactionConflict):
        settle_restaurant_payment(
            order_id=pending_restaurant_order.pk,
            provider="payme",
            provider_transaction_id="restaurant-payme-001",
        )

    pending_restaurant_order.refresh_from_db()

    assert pending_restaurant_order.status == RestaurantOrder.Status.PENDING
    assert RevenueEntry.objects.count() == 0


@pytest.mark.django_db
def test_expired_order_releases_stock(
    pending_restaurant_order,
    restaurant_food,
):
    RestaurantOrder.objects.filter(
        pk=pending_restaurant_order.pk
    ).update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )

    result = expire_restaurant_order(
        pending_restaurant_order.pk
    )

    pending_restaurant_order.refresh_from_db()
    restaurant_food.refresh_from_db()

    assert result is True
    assert pending_restaurant_order.status == RestaurantOrder.Status.EXPIRED
    assert restaurant_food.stock == 20

    # Ikkinchi marta stock qaytarilmasligi kerak.
    assert expire_restaurant_order(
        pending_restaurant_order.pk
    ) is False

    restaurant_food.refresh_from_db()
    assert restaurant_food.stock == 20


@pytest.mark.django_db
def test_expired_order_cannot_be_paid(
    pending_restaurant_order,
):
    RestaurantOrder.objects.filter(
        pk=pending_restaurant_order.pk
    ).update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )

    with pytest.raises(PaymentOrderUnavailable):
        settle_restaurant_payment(
            order_id=pending_restaurant_order.pk,
            provider="click",
            provider_transaction_id="restaurant-click-expired",
        )

    assert RevenueEntry.objects.count() == 0


@pytest.mark.django_db
def test_paid_order_does_not_release_stock(
    pending_restaurant_order,
    restaurant_food,
):
    settle_restaurant_payment(
        order_id=pending_restaurant_order.pk,
        provider="click",
        provider_transaction_id="restaurant-click-006",
    )

    RestaurantOrder.objects.filter(
        pk=pending_restaurant_order.pk
    ).update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )

    assert expire_restaurant_order(
        pending_restaurant_order.pk
    ) is False

    restaurant_food.refresh_from_db()
    assert restaurant_food.stock == 18


@pytest.mark.django_db
@pytest.mark.parametrize(
    "invalid_quantity",
    [-2, 0, 1.5, "2", True, None],
)
def test_invalid_quantity_rejected(
    restaurant_user,
    restaurant_food,
    invalid_quantity,
):
    with pytest.raises(ValidationError):
        create_restaurant_order(
            user=restaurant_user,
            items=[
                {
                    "food_id": restaurant_food.pk,
                    "quantity": invalid_quantity,
                }
            ],
            provider="click",
            key=uuid.uuid4(),
        )

    restaurant_food.refresh_from_db()

    assert restaurant_food.stock == 20
    assert RestaurantOrder.objects.count() == 0