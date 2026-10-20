
import pytest

from django.urls import reverse

from apps.payments.models import ClickTransaction
from apps.finance.models import RevenueEntry

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


@pytest.mark.django_db
@pytest.mark.parametrize(
    "field,value",
    [
        ("amount", "-100"),
        ("amount", "NaN"),
        ("merchant_trans_id", "invalid"),
        ("sign_string", "invalid"),
    ],
)
def test_invalid_prepare_does_not_create_transaction(
    client,
    click_order,
    field,
    value,
):
    payload = make_payload(click_order)
    payload[field] = value

    initial_transactions = ClickTransaction.objects.count()
    initial_revenue = RevenueEntry.objects.count()
    initial_status = click_order.status

    response = client.post(
        reverse("click-prepare"),
        data=payload,
    )

    assert response.status_code == 200
    assert response.json()["error"] != 0

    click_order.refresh_from_db()

    assert ClickTransaction.objects.count() == initial_transactions
    assert RevenueEntry.objects.count() == initial_revenue
    assert click_order.status == initial_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "field,value",
    [
        ("merchant_prepare_id", "invalid"),
        ("merchant_prepare_id", "-1"),
        ("amount", "-100"),
        ("sign_string", "invalid"),
    ],
)
def test_invalid_complete_preserves_payment_state(
    client,
    click_order,
    field,
    value,
):
    prepare_payload = make_payload(click_order)

    prepare_response = client.post(
        reverse("click-prepare"),
        data=prepare_payload,
    )

    assert prepare_response.status_code == 200
    assert prepare_response.json()["error"] == 0

    prepare_id = prepare_response.json()["merchant_prepare_id"]

    complete_payload = make_payload(
        click_order,
        action="1",
        click_trans_id=prepare_payload["click_trans_id"],
        prepare_id=prepare_id,
    )

    complete_payload[field] = value

    initial_revenue = RevenueEntry.objects.count()
    initial_status = click_order.status

    response = client.post(
        reverse("click-complete"),
        data=complete_payload,
    )

    assert response.status_code == 200
    assert response.json()["error"] != 0

    transaction = ClickTransaction.objects.get(
        merchant_prepare_id=prepare_id,
    )

    click_order.refresh_from_db()

    assert transaction.status == "prepared"
    assert click_order.status == initial_status
    assert RevenueEntry.objects.count() == initial_revenue
