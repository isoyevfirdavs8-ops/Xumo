from datetime import date, timedelta
from decimal import Decimal

import pytest

from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.football.models import (
    FootballAcademy,
    FootballSubscription,
)
from apps.payments.click_services import (
    ClickError,
    prepare_click_payment,
)
from apps.payments.models import ClickTransaction


pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def subscription():
    User = get_user_model()

    user = User.objects.create_user(
        phone_number="+998901234568",
        password="StrongPass123!",
    )

    academy = FootballAcademy.objects.create(
        name="FC BUKHARA Click Academy",
        monthly_price=Decimal("350000.00"),
    )

    today = timezone.localdate()
    month = date(today.year, today.month, 1)

    return FootballSubscription.objects.create(
        user=user,
        academy=academy,
        month=month,
        price_snapshot=Decimal("350000.00"),
        status=FootballSubscription.Status.PENDING_PAYMENT,
        payment_expires_at=timezone.now() + timedelta(minutes=15),
    )


def prepare_data(subscription, click_trans_id="CLICK-ACADEMY-1", amount="350000.00"):
    return {
        "click_trans_id": click_trans_id,
        "merchant_trans_id": f"football_academy:{subscription.pk}",
        "click_paydoc_id": "PAYDOC-ACADEMY-1",
        "amount": amount,
        "action": "0",
    }


def test_academy_click_prepare_success(subscription):
    tx = prepare_click_payment(prepare_data(subscription))

    assert tx.category == "football_academy"
    assert tx.order_id == str(subscription.pk)
    assert tx.amount == Decimal("350000.00")
    assert tx.status == ClickTransaction.Status.PREPARED


def test_academy_click_prepare_is_idempotent(subscription):
    data = prepare_data(subscription)

    first = prepare_click_payment(data)
    second = prepare_click_payment(data)

    assert first.pk == second.pk

    assert ClickTransaction.objects.filter(
        category="football_academy",
        order_id=str(subscription.pk),
    ).count() == 1


def test_academy_click_prepare_wrong_amount(subscription):
    with pytest.raises(ClickError) as exc:
        prepare_click_payment(
            prepare_data(subscription, amount="100000.00")
        )

    assert exc.value.code == -2


def test_academy_click_prepare_expired(subscription):
    subscription.payment_expires_at = timezone.now() - timedelta(minutes=1)
    subscription.save(update_fields=["payment_expires_at"])

    with pytest.raises(ClickError) as exc:
        prepare_click_payment(prepare_data(subscription))

    assert exc.value.code == -9


def test_academy_click_prepare_second_transaction_rejected(subscription):
    prepare_click_payment(prepare_data(subscription))

    with pytest.raises(ClickError) as exc:
        prepare_click_payment(
            prepare_data(
                subscription,
                click_trans_id="CLICK-ACADEMY-2",
            )
        )

    assert exc.value.code == -4