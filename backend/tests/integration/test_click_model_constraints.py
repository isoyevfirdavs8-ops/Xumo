
from decimal import Decimal

import pytest

from django.db import IntegrityError, transaction

from apps.payments.models import ClickTransaction


@pytest.mark.django_db
def test_click_transaction_amount_must_be_positive():
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            ClickTransaction.objects.create(
                click_trans_id="click-negative-001",
                category="competition",
                order_id="negative-order-001",
                amount=Decimal("-100.00"),
                status=ClickTransaction.Status.PREPARED,
            )


@pytest.mark.django_db
def test_only_one_completed_click_transaction_per_order():
    ClickTransaction.objects.create(
        click_trans_id="click-completed-001",
        category="competition",
        order_id="completed-order-001",
        amount=Decimal("50000.00"),
        status=ClickTransaction.Status.COMPLETED,
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            ClickTransaction.objects.create(
                click_trans_id="click-completed-002",
                category="competition",
                order_id="completed-order-001",
                amount=Decimal("50000.00"),
                status=ClickTransaction.Status.COMPLETED,
            )


@pytest.mark.django_db
def test_different_orders_can_have_completed_transactions():
    ClickTransaction.objects.create(
        click_trans_id="click-completed-003",
        category="competition",
        order_id="completed-order-002",
        amount=Decimal("50000.00"),
        status=ClickTransaction.Status.COMPLETED,
    )

    ClickTransaction.objects.create(
        click_trans_id="click-completed-004",
        category="competition",
        order_id="completed-order-003",
        amount=Decimal("50000.00"),
        status=ClickTransaction.Status.COMPLETED,
    )

    assert ClickTransaction.objects.filter(
        status=ClickTransaction.Status.COMPLETED,
        order_id__in=[
            "completed-order-002",
            "completed-order-003",
        ],
    ).count() == 2
