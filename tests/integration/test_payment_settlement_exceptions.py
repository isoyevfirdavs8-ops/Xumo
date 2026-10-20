
import uuid
from datetime import timedelta

import pytest
from django.utils import timezone

from apps.competitions.models import TicketOrder
from apps.finance.payment_settlement import (
    settle_competition_payment,
)
from apps.payments.exceptions import (
    PaymentOrderUnavailable,
    PaymentTransactionConflict,
)

from tests.integration.test_competition_orders import (
    competition_user,
    competition,
    order_data,
)


@pytest.fixture
def pending_order(order_data):
    from apps.competitions.services import create_ticket_order

    return create_ticket_order(**order_data)


@pytest.mark.django_db
def test_expired_competition_order_raises_specific_error(
    pending_order,
):
    TicketOrder.objects.filter(
        pk=pending_order.pk
    ).update(
        payment_expires_at=timezone.now()
        - timedelta(minutes=1)
    )

    with pytest.raises(PaymentOrderUnavailable):
        settle_competition_payment(
            order_id=pending_order.pk,
            provider="click",
            provider_transaction_id=str(uuid.uuid4()),
        )

    pending_order.refresh_from_db()

    assert pending_order.status == TicketOrder.Status.PENDING


@pytest.mark.django_db
def test_wrong_provider_raises_transaction_conflict(
    pending_order,
):
    with pytest.raises(PaymentTransactionConflict):
        settle_competition_payment(
            order_id=pending_order.pk,
            provider="payme",
            provider_transaction_id=str(uuid.uuid4()),
        )


@pytest.mark.django_db
def test_missing_transaction_id_raises_conflict(
    pending_order,
):
    with pytest.raises(PaymentTransactionConflict):
        settle_competition_payment(
            order_id=pending_order.pk,
            provider="click",
            provider_transaction_id="",
        )


@pytest.mark.django_db
def test_cancelled_order_raises_unavailable(
    pending_order,
):
    TicketOrder.objects.filter(
        pk=pending_order.pk
    ).update(
        status=TicketOrder.Status.CANCELLED
    )

    with pytest.raises(PaymentOrderUnavailable):
        settle_competition_payment(
            order_id=pending_order.pk,
            provider="click",
            provider_transaction_id=str(uuid.uuid4()),
        )
