
import uuid
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier

import pytest

from django.contrib.auth import get_user_model
from django.db import close_old_connections, connections
from rest_framework.exceptions import ValidationError

from apps.categories.models import Category, SubCategory
from apps.foods.models import Food
from apps.restaurant_orders.models import RestaurantOrder
from apps.restaurant_orders.services import create_restaurant_order


@pytest.fixture
def concurrency_data(db):
    User = get_user_model()

    user1 = User.objects.create_user(
        phone_number="+998901234571",
        password="TestPassword123!",
    )

    user2 = User.objects.create_user(
        phone_number="+998901234572",
        password="TestPassword123!",
    )

    category = Category.objects.create(
        name="Concurrency Test Category",
        slug="concurrency-test-category",
        image="categories/test.jpg",
        is_active=True,
    )

    subcategory = SubCategory.objects.create(
        category=category,
        name="Concurrency Test Subcategory",
        is_active=True,
    )

    food = Food.objects.create(
        subcategory=subcategory,
        name="Last Burger",
        price=Decimal("35000.00"),
        stock=1,
        is_active=True,
    )

    return user1.pk, user2.pk, food.pk


def checkout_worker(user_id, food_id, barrier):
    close_old_connections()

    try:
        User = get_user_model()
        user = User.objects.get(pk=user_id)

        # Ikkala thread checkoutni bir vaqtda boshlaydi.
        barrier.wait(timeout=10)

        order = create_restaurant_order(
            user=user,
            items=[
                {
                    "food_id": food_id,
                    "quantity": 1,
                }
            ],
            provider="click",
            key=uuid.uuid4(),
        )

        return ("success", str(order.pk))

    except ValidationError:
        return ("rejected", None)

    finally:
        connections.close_all()


@pytest.mark.django_db(transaction=True)
def test_parallel_checkout_cannot_oversell(concurrency_data):
    user1_id, user2_id, food_id = concurrency_data

    barrier = Barrier(2)

    with ThreadPoolExecutor(max_workers=2) as executor:
        future1 = executor.submit(
            checkout_worker,
            user1_id,
            food_id,
            barrier,
        )

        future2 = executor.submit(
            checkout_worker,
            user2_id,
            food_id,
            barrier,
        )

        results = [
            future1.result(timeout=20),
            future2.result(timeout=20),
        ]

    successes = [
        result for result in results
        if result[0] == "success"
    ]

    rejected = [
        result for result in results
        if result[0] == "rejected"
    ]

    food = Food.objects.get(pk=food_id)

    assert len(successes) == 1
    assert len(rejected) == 1

    assert food.stock == 0
    assert RestaurantOrder.objects.count() == 1



def idempotent_checkout_worker(
    user_id,
    food_id,
    idempotency_key,
    barrier,
):
    close_old_connections()

    try:
        User = get_user_model()
        user = User.objects.get(pk=user_id)

        barrier.wait(timeout=10)

        order = create_restaurant_order(
            user=user,
            items=[
                {
                    "food_id": food_id,
                    "quantity": 1,
                }
            ],
            provider="click",
            key=idempotency_key,
        )

        return ("success", str(order.pk))

    except ValidationError as exc:
        return ("rejected", str(exc))

    finally:
        connections.close_all()



@pytest.mark.django_db(transaction=True)
def test_parallel_same_idempotency_key(
    concurrency_data,
):
    user1_id, _, food_id = concurrency_data

    key = uuid.uuid4()
    barrier = Barrier(2)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(
                idempotent_checkout_worker,
                user1_id,
                food_id,
                key,
                barrier,
            )
            for _ in range(2)
        ]

        results = [
            future.result(timeout=20)
            for future in futures
        ]

    food = Food.objects.get(pk=food_id)

    assert len(results) == 2

    # Endi ikkala parallel so'rov ham
    # muvaffaqiyatli tugashi kerak.
    assert all(
        result[0] == "success"
        for result in results
    ), results

    # Ikkalasi ham bitta order ID qaytaradi.
    assert results[0][1] == results[1][1]

    # Faqat bitta buyurtma yaratilgan.
    assert RestaurantOrder.objects.count() == 1

    # Stock faqat bir marta kamaygan.
    assert food.stock == 0
