
from datetime import timedelta
import uuid

import pytest

from django.utils import timezone
from tests.integration.test_competition_orders import (
    competition_user,
    competition,
    order_data,
)
from apps.competitions.models import TicketOrder
from apps.competitions.services import expire_ticket_order
from apps.payments.models import ClickTransaction

from tests.integration.test_click_http_integration import (
    click_order,
    click_settings,
)


def mark_expired(order):
    TicketOrder.objects.filter(pk=order.pk).update(
        payment_expires_at=(
            timezone.now() - timedelta(minutes=5)
        )
    )


def create_click_transaction(
    order,
    *,
    status=ClickTransaction.Status.PREPARED,
):
    return ClickTransaction.objects.create(
        click_trans_id=f"test-{uuid.uuid4()}",
        category="competition",
        order_id=str(order.pk),
        amount=order.total_amount,
        status=status,
    )


@pytest.mark.django_db
def test_expired_order_without_click_transaction_is_cancelled(
    click_order,
):
    mark_expired(click_order)

    result = expire_ticket_order(click_order.pk)

    click_order.refresh_from_db()

    assert result is True
    assert click_order.status == TicketOrder.Status.CANCELLED


@pytest.mark.django_db
def test_expired_order_with_prepared_click_is_not_cancelled(
    click_order,
):
    mark_expired(click_order)

    create_click_transaction(
        click_order,
        status=ClickTransaction.Status.PREPARED,
    )

    result = expire_ticket_order(click_order.pk)

    click_order.refresh_from_db()

    assert result is False
    assert click_order.status == TicketOrder.Status.PENDING


@pytest.mark.django_db
def test_expired_order_with_cancelled_click_requires_reconciliation(
    click_order,
):
    mark_expired(click_order)

    create_click_transaction(
        click_order,
        status=ClickTransaction.Status.CANCELLED,
    )

    result = expire_ticket_order(click_order.pk)

    click_order.refresh_from_db()

    assert result is False
    assert click_order.status == TicketOrder.Status.PENDING


@pytest.mark.django_db
def test_non_expired_order_is_not_cancelled(
    click_order,
):
    TicketOrder.objects.filter(
        pk=click_order.pk,
    ).update(
        payment_expires_at=(
            timezone.now() + timedelta(minutes=30)
        )
    )

    result = expire_ticket_order(click_order.pk)

    click_order.refresh_from_db()

    assert result is False
    assert click_order.status == TicketOrder.Status.PENDING


@pytest.mark.django_db
def test_expiration_is_idempotent(
    click_order,
):
    mark_expired(click_order)

    first_result = expire_ticket_order(click_order.pk)
    second_result = expire_ticket_order(click_order.pk)

    click_order.refresh_from_db()

    assert first_result is True
    assert second_result is False
    assert click_order.status == TicketOrder.Status.CANCELLED
