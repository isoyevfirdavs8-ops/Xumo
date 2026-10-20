
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
from threading import Barrier

import pytest

from django.contrib.auth import get_user_model
from django.db import close_old_connections, connections
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.competitions.models import Competition, TicketOrder
from apps.competitions.services import create_ticket_order


@pytest.fixture
def concurrency_competition(db):
    User = get_user_model()

    users = [
        User.objects.create_user(
            phone_number=f"+99890123459{i}",
            password="TestPassword123!",
        )
        for i in range(2)
    ]

    competition = Competition.objects.create(
        name="XUMO Parallel Championship",
        description="Parallel ticket booking test",
        banner="competitions/banners/test.jpg",
        start_time=timezone.now() + timedelta(days=7),
        min_age=12,
        max_age=60,
        price=Decimal("50000.00"),
        capacity=1,
        is_active=True,
    )

    return [user.pk for user in users], competition.pk


def checkout_worker(
    user_id,
    competition_id,
    barrier,
    key=None,
):
    close_old_connections()

    try:
        User = get_user_model()
        user = User.objects.get(pk=user_id)

        barrier.wait(timeout=10)

        order = create_ticket_order(
            user=user,
            competition_id=competition_id,
            full_name="Parallel Test User",
            phone_number="+998901234599",
            quantity=1,
            provider="click",
            idempotency_key=key or uuid.uuid4(),
        )

        return ("success", str(order.pk))

    except ValidationError:
        return ("rejected", None)

    finally:
        connections.close_all()


@pytest.mark.django_db(transaction=True)
def test_parallel_checkout_cannot_oversell(
    concurrency_competition,
):
    user_ids, competition_id = concurrency_competition

    barrier = Barrier(2)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(
                checkout_worker,
                user_id,
                competition_id,
                barrier,
            )
            for user_id in user_ids
        ]

        results = [
            future.result(timeout=20)
            for future in futures
        ]

    successes = [
        result for result in results
        if result[0] == "success"
    ]

    rejected = [
        result for result in results
        if result[0] == "rejected"
    ]

    assert len(successes) == 1
    assert len(rejected) == 1

    assert TicketOrder.objects.count() == 1

    order = TicketOrder.objects.get()
    assert order.quantity == 1
    assert order.status == TicketOrder.Status.PENDING



@pytest.mark.django_db(transaction=True)
def test_parallel_same_idempotency_key_creates_one_order(
    concurrency_competition,
):
    user_ids, competition_id = concurrency_competition

    key = uuid.uuid4()
    barrier = Barrier(2)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(
                checkout_worker,
                user_ids[0],
                competition_id,
                barrier,
                key,
            )
            for _ in range(2)
        ]

        results = [
            future.result(timeout=20)
            for future in futures
        ]

    assert len(results) == 2

    # Ikkala checkout ham muvaffaqiyatli.
    assert all(
        result[0] == "success"
        for result in results
    ), results

    # Bir xil buyurtma ID qaytadi.
    assert results[0][1] == results[1][1]

    # Faqat bitta buyurtma saqlangan.
    assert TicketOrder.objects.count() == 1

    order = TicketOrder.objects.get()

    assert str(order.pk) == results[0][1]
    assert order.quantity == 1
    assert order.status == TicketOrder.Status.PENDING
