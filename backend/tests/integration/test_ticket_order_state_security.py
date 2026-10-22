
from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction

from apps.competitions.models import TicketOrder

from tests.integration.test_competition_orders import (
    competition_user,
    competition,
    order_data,
)
from tests.integration.test_click_http_integration import (
    click_order,
    click_settings,
)


@pytest.mark.django_db
def test_pending_order_price_is_immutable(click_order):
    original_amount = click_order.total_amount

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            TicketOrder.objects.filter(
                pk=click_order.pk,
            ).update(total_amount=Decimal("1.00"))

    click_order.refresh_from_db()
    assert click_order.total_amount == original_amount


@pytest.mark.django_db
def test_paid_order_cannot_return_to_pending(paid_click_order):
    order = paid_click_order

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            TicketOrder.objects.filter(
                pk=order.pk,
            ).update(status=TicketOrder.Status.PENDING)

    order.refresh_from_db()
    assert order.status == TicketOrder.Status.PAID


@pytest.mark.django_db
def test_cancelled_order_cannot_be_paid(click_order):
    click_order.status = TicketOrder.Status.CANCELLED
    click_order.save(update_fields=["status"])

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            TicketOrder.objects.filter(
                pk=click_order.pk,
            ).update(status=TicketOrder.Status.PAID)

    click_order.refresh_from_db()
    assert click_order.status == TicketOrder.Status.CANCELLED


@pytest.mark.django_db
def test_paid_order_can_be_refunded(paid_click_order):
    order = paid_click_order

    TicketOrder.objects.filter(pk=order.pk).update(
        status=TicketOrder.Status.REFUNDED,
    )

    order.refresh_from_db()
    assert order.status == TicketOrder.Status.REFUNDED


@pytest.mark.django_db
def test_refunded_order_cannot_be_paid_again(paid_click_order):
    order = paid_click_order

    order.status = TicketOrder.Status.REFUNDED
    order.save(update_fields=["status"])

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            TicketOrder.objects.filter(
                pk=order.pk,
            ).update(status=TicketOrder.Status.PAID)

    order.refresh_from_db()
    assert order.status == TicketOrder.Status.REFUNDED
