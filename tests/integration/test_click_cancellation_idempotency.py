
import pytest

from apps.payments.models import ClickTransaction

from tests.integration.test_competition_orders import (
    order_data,
    competition_user,
    competition,
)

from tests.integration.test_click_http_integration import (
    click_order,
    click_settings,
    make_payload,
    post_prepare,
    post_complete,
)


@pytest.mark.django_db
def test_repeated_cancellation_is_idempotent(
    client,
    click_order,
):
    prepare_data = make_payload(click_order)
    prepared = post_prepare(client, prepare_data)

    assert prepared.json()["error"] == 0

    cancellation = make_payload(
        click_order,
        action="1",
        click_trans_id=prepare_data["click_trans_id"],
        prepare_id=prepared.json()["merchant_prepare_id"],
        error="-1",
    )

    first = post_complete(client, cancellation)
    second = post_complete(client, cancellation)

    assert first.status_code == 200
    assert second.status_code == 200

    assert first.json()["error"] == 0
    assert second.json()["error"] == 0

    tx = ClickTransaction.objects.get(
        click_trans_id=prepare_data["click_trans_id"],
    )
    assert tx.status == ClickTransaction.Status.CANCELLED


@pytest.mark.django_db
def test_cancelled_transaction_cannot_be_completed(
    client,
    click_order,
):
    prepare_data = make_payload(click_order)
    prepared = post_prepare(client, prepare_data)

    cancellation = make_payload(
        click_order,
        action="1",
        click_trans_id=prepare_data["click_trans_id"],
        prepare_id=prepared.json()["merchant_prepare_id"],
        error="-1",
    )

    post_complete(client, cancellation)

    success = make_payload(
        click_order,
        action="1",
        click_trans_id=prepare_data["click_trans_id"],
        prepare_id=prepared.json()["merchant_prepare_id"],
        error="0",
    )

    response = post_complete(client, success)

    assert response.json()["error"] == -9

    tx = ClickTransaction.objects.get(
        click_trans_id=prepare_data["click_trans_id"],
    )
    assert tx.status == ClickTransaction.Status.CANCELLED


@pytest.mark.django_db
def test_completed_transaction_cannot_be_cancelled(
    client,
    click_order,
    verified_click_provider,
):
    prepare_data = make_payload(click_order)
    prepared = post_prepare(client, prepare_data)

    success = make_payload(
        click_order,
        action="1",
        click_trans_id=prepare_data["click_trans_id"],
        prepare_id=prepared.json()["merchant_prepare_id"],
        error="0",
    )

    completed = post_complete(client, success)
    assert completed.json()["error"] == 0

    cancellation = make_payload(
        click_order,
        action="1",
        click_trans_id=prepare_data["click_trans_id"],
        prepare_id=prepared.json()["merchant_prepare_id"],
        error="-1",
    )

    response = post_complete(client, cancellation)

    assert response.json()["error"] == -9

    tx = ClickTransaction.objects.get(
        click_trans_id=prepare_data["click_trans_id"],
    )
    assert tx.status == ClickTransaction.Status.COMPLETED
