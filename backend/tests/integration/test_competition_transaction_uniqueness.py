
import uuid

import pytest

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.competitions.models import TicketOrder
from apps.competitions.services import create_ticket_order
from apps.finance.payment_settlement import (
    settle_competition_payment,
)

from tests.integration.test_competition_orders import (
    competition_user,
    competition,
    order_data,
)

from tests.integration.test_click_http_integration import (
    click_order,
    click_settings,
)


def create_second_order(order_data, *, provider=None):
    data = {
        **order_data,
        "idempotency_key": uuid.uuid4(),
    }

    if provider is not None:
        data["provider"] = provider

    return create_ticket_order(**data)


@pytest.mark.django_db
def test_same_provider_transaction_id_is_rejected(
    click_order,
    order_data,
):
    second_order = create_second_order(order_data)

    transaction_id = f"click-{uuid.uuid4()}"

    TicketOrder.objects.filter(
        pk=click_order.pk,
    ).update(
        status=TicketOrder.Status.PAID,
        paid_at=timezone.now(),
        provider_transaction_id=transaction_id,
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            TicketOrder.objects.filter(
                pk=second_order.pk,
            ).update(
                status=TicketOrder.Status.PAID,
                paid_at=timezone.now(),
                provider_transaction_id=transaction_id,
            )

    second_order.refresh_from_db()

    assert second_order.status == TicketOrder.Status.PENDING
    assert second_order.provider_transaction_id is None


@pytest.mark.django_db
def test_different_providers_can_share_transaction_id(
    click_order,
    order_data,
):
    payme_order = create_second_order(
        order_data,
        provider=TicketOrder.Provider.PAYME,
    )

    transaction_id = f"shared-{uuid.uuid4()}"

    for order in (click_order, payme_order):
        TicketOrder.objects.filter(pk=order.pk).update(
            status=TicketOrder.Status.PAID,
            paid_at=timezone.now(),
            provider_transaction_id=transaction_id,
        )

    click_order.refresh_from_db()
    payme_order.refresh_from_db()

    assert click_order.status == TicketOrder.Status.PAID
    assert payme_order.status == TicketOrder.Status.PAID


@pytest.mark.django_db
def test_pending_orders_without_transaction_id_are_allowed(
    click_order,
    order_data,
):
    second_order = create_second_order(order_data)

    assert click_order.status == TicketOrder.Status.PENDING
    assert second_order.status == TicketOrder.Status.PENDING

    assert click_order.provider_transaction_id is None
    assert second_order.provider_transaction_id is None


@pytest.mark.django_db
def test_different_transaction_ids_are_allowed(
    click_order,
    order_data,
):
    second_order = create_second_order(order_data)

    for order in (click_order, second_order):
        TicketOrder.objects.filter(pk=order.pk).update(
            status=TicketOrder.Status.PAID,
            paid_at=timezone.now(),
            provider_transaction_id=f"tx-{uuid.uuid4()}",
        )

    click_order.refresh_from_db()
    second_order.refresh_from_db()

    assert click_order.status == TicketOrder.Status.PAID
    assert second_order.status == TicketOrder.Status.PAID


@pytest.mark.django_db
def test_settlement_rejects_reused_provider_transaction_id(
    click_order,
    order_data,
):
    second_order = create_second_order(order_data)

    transaction_id = f"settlement-{uuid.uuid4()}"

    settle_competition_payment(
        order_id=click_order.pk,
        provider=click_order.provider,
        provider_transaction_id=transaction_id,
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            settle_competition_payment(
                order_id=second_order.pk,
                provider=second_order.provider,
                provider_transaction_id=transaction_id,
            )

    second_order.refresh_from_db()

    assert second_order.status == TicketOrder.Status.PENDING
