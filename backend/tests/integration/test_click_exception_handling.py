
from unittest.mock import patch

import pytest

from apps.competitions.models import TicketOrder
from apps.payments.models import ClickTransaction
from apps.payments.exceptions import (
    PaymentOrderUnavailable,
    PaymentTransactionConflict,
    PaymentTemporaryFailure,
    PaymentSettlementError,
)

from tests.integration.test_competition_orders import (
    competition_user,
    competition,
    order_data,
)
from tests.integration.test_click_http_integration import (
    click_settings,
    click_order,
    make_payload,
    post_prepare,
    post_complete,
)


@pytest.fixture
def prepared_payment(client, click_order):
    prepare = make_payload(click_order)
    response = post_prepare(client, prepare)

    assert response.json()["error"] == 0

    return {
        "order": click_order,
        "click_trans_id": prepare["click_trans_id"],
        "prepare_id": response.json()["merchant_prepare_id"],
    }


def make_complete(prepared_payment):
    return make_payload(
        prepared_payment["order"],
        action="1",
        click_trans_id=prepared_payment["click_trans_id"],
        prepare_id=prepared_payment["prepare_id"],
        error="0",
    )


def assert_not_settled(prepared_payment):
    order = prepared_payment["order"]
    order.refresh_from_db()

    tx = ClickTransaction.objects.get(
        click_trans_id=prepared_payment["click_trans_id"]
    )

    assert order.status == TicketOrder.Status.PENDING
    assert tx.status == ClickTransaction.Status.PREPARED


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("exception", "expected_code"),
    [
        (PaymentOrderUnavailable(), -9),
        (PaymentTransactionConflict(), -4),
        (PaymentTemporaryFailure(), -9),
        (PaymentSettlementError("Internal settlement details"), -9),
    ],
)
def test_settlement_exception_mapping(
    client,
    prepared_payment,
    exception,
    expected_code,
    verified_click_provider,
):
    payload = make_complete(prepared_payment)

    with patch(
        "apps.payments.click_services.settle_competition_payment",
        side_effect=exception,
    ):
        response = post_complete(client, payload)

    assert response.status_code == 200
    assert response.json()["error"] == expected_code
    assert "Internal settlement details" not in (
        response.json()["error_note"]
    )

    assert_not_settled(prepared_payment)


@pytest.mark.django_db
def test_temporary_failure_then_successful_retry(
    client,
    prepared_payment,
    verified_click_provider,
):
    payload = make_complete(prepared_payment)

    with patch(
        "apps.payments.click_services.settle_competition_payment",
        side_effect=PaymentTemporaryFailure(),
    ):
        failed = post_complete(client, payload)

    assert failed.json()["error"] == -9
    assert_not_settled(prepared_payment)

    recovered = post_complete(client, payload)

    assert recovered.json()["error"] == 0

    order = prepared_payment["order"]
    order.refresh_from_db()

    assert order.status == TicketOrder.Status.PAID

    tx = ClickTransaction.objects.get(
        click_trans_id=prepared_payment["click_trans_id"]
    )
    assert tx.status == ClickTransaction.Status.COMPLETED
