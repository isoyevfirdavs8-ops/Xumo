
import uuid
from datetime import timedelta
from decimal import Decimal

import pytest

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.competitions.models import Competition, TicketOrder
from apps.competitions.services import (
    PAYMENT_TIMEOUT_MINUTES,
    create_ticket_order,
    expire_ticket_order,
)


@pytest.fixture
def competition_user(db):
    User = get_user_model()

    return User.objects.create_user(
        phone_number="+998901234580",
        password="TestPassword123!",
    )


@pytest.fixture
def competition(db):
    return Competition.objects.create(
        name="XUMO SPORT TEST CHAMPIONSHIP",
        description="Integration test musobaqasi",
        banner="competitions/banners/test.jpg",
        start_time=timezone.now() + timedelta(days=7),
        min_age=12,
        max_age=60,
        price=Decimal("50000.00"),
        capacity=10,
        is_active=True,
    )


@pytest.fixture
def order_data(competition_user, competition):
    return {
        "user": competition_user,
        "competition_id": competition.pk,
        "full_name": "Test User",
        "phone_number": "+998901234580",
        "quantity": 2,
        "provider": "click",
        "idempotency_key": uuid.uuid4(),
    }


@pytest.mark.django_db
def test_create_ticket_order(order_data):
    before = timezone.now()

    order = create_ticket_order(**order_data)

    after = timezone.now()

    assert order.pk is not None
    assert order.status == TicketOrder.Status.PENDING
    assert order.quantity == 2
    assert order.unit_price == Decimal("50000.00")
    assert order.total_amount == Decimal("100000.00")

    assert (
        before + timedelta(minutes=PAYMENT_TIMEOUT_MINUTES)
        <= order.payment_expires_at
        <= after + timedelta(minutes=PAYMENT_TIMEOUT_MINUTES)
    )


@pytest.mark.django_db
def test_duplicate_checkout_is_idempotent(order_data):
    first = create_ticket_order(**order_data)
    second = create_ticket_order(**order_data)

    assert first.pk == second.pk
    assert TicketOrder.objects.count() == 1


@pytest.mark.django_db
def test_same_key_different_quantity_rejected(order_data):
    create_ticket_order(**order_data)

    changed_data = {
        **order_data,
        "quantity": 3,
    }

    with pytest.raises(ValidationError):
        create_ticket_order(**changed_data)

    assert TicketOrder.objects.count() == 1


@pytest.mark.django_db
def test_capacity_limit_rejected(order_data):
    order_data["quantity"] = 10

    create_ticket_order(**order_data)

    order_data["idempotency_key"] = uuid.uuid4()
    order_data["quantity"] = 1

    with pytest.raises(ValidationError):
        create_ticket_order(**order_data)

    assert TicketOrder.objects.count() == 1


@pytest.mark.django_db
def test_expired_pending_order_releases_capacity(order_data):
    order = create_ticket_order(**order_data)

    TicketOrder.objects.filter(pk=order.pk).update(
        payment_expires_at=timezone.now() - timedelta(seconds=1)
    )

    result = expire_ticket_order(order.pk)

    order.refresh_from_db()

    assert result is True
    assert order.status == TicketOrder.Status.CANCELLED

    new_data = {
        **order_data,
        "idempotency_key": uuid.uuid4(),
    }

    new_order = create_ticket_order(**new_data)

    assert new_order.pk != order.pk


@pytest.mark.django_db
def test_inactive_competition_rejected(order_data, competition):
    competition.is_active = False
    competition.save(update_fields=["is_active"])

    with pytest.raises(ValidationError):
        create_ticket_order(**order_data)

    assert TicketOrder.objects.count() == 0


@pytest.mark.django_db
def test_started_competition_rejected(order_data, competition):
    competition.start_time = timezone.now() - timedelta(hours=1)
    competition.save(update_fields=["start_time"])

    with pytest.raises(ValidationError):
        create_ticket_order(**order_data)

    assert TicketOrder.objects.count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize("quantity", [0, -1, 11, 100, "2", None])
def test_invalid_ticket_quantity_rejected(order_data, quantity):
    order_data["quantity"] = quantity

    with pytest.raises(ValidationError):
        create_ticket_order(**order_data)

    assert TicketOrder.objects.count() == 0


@pytest.mark.django_db
def test_invalid_provider_rejected(order_data):
    order_data["provider"] = "unknown"

    with pytest.raises(ValidationError):
        create_ticket_order(**order_data)

    assert TicketOrder.objects.count() == 0


@pytest.mark.django_db
def test_ticket_price_snapshot(order_data, competition):
    order = create_ticket_order(**order_data)

    competition.price = Decimal("90000.00")
    competition.save(update_fields=["price"])

    order.refresh_from_db()

    assert order.unit_price == Decimal("50000.00")
    assert order.total_amount == Decimal("100000.00")
