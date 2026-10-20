
import pytest

from django.db import IntegrityError, transaction

from apps.payments.models import ClickTransaction

from tests.integration.test_competition_orders import (
    competition_user,
    competition,
    order_data,
)
from tests.integration.test_click_http_integration import (
    click_settings,
    click_order,
    make_payload,
)
from apps.payments.click_services import prepare_click_payment


@pytest.mark.django_db(transaction=True)
def test_duplicate_click_transaction_rolls_back_to_savepoint(
    click_order,
):
    first_payload = make_payload(click_order)
    first = prepare_click_payment(first_payload)

    assert first.status == ClickTransaction.Status.PREPARED

    with transaction.atomic():
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                ClickTransaction.objects.create(
                    click_trans_id=first.click_trans_id,
                    category="competition",
                    order_id=str(click_order.pk),
                    amount=first.amount,
                    status=ClickTransaction.Status.PREPARED,
                )

        # Ichki savepoint rollback bo'ldi.
        # Tashqi transaction hali ishlashi kerak.
        assert ClickTransaction.objects.filter(
            click_trans_id=first.click_trans_id,
        ).count() == 1


@pytest.mark.django_db(transaction=True)
def test_unique_prepared_order_constraint(
    click_order,
):
    first = prepare_click_payment(
        make_payload(click_order)
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            ClickTransaction.objects.create(
                click_trans_id="another-click-transaction",
                category=first.category,
                order_id=first.order_id,
                amount=first.amount,
                status=ClickTransaction.Status.PREPARED,
            )

    assert ClickTransaction.objects.filter(
        category=first.category,
        order_id=first.order_id,
        status=ClickTransaction.Status.PREPARED,
    ).count() == 1


@pytest.mark.django_db(transaction=True)
def test_positive_amount_constraint(
    click_order,
):
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            ClickTransaction.objects.create(
                click_trans_id="invalid-zero-amount",
                category="competition",
                order_id=str(click_order.pk),
                amount=0,
                status=ClickTransaction.Status.PREPARED,
            )

    assert not ClickTransaction.objects.filter(
        click_trans_id="invalid-zero-amount",
    ).exists()
