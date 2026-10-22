
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

from tests.integration.test_click_sign_time_security import (
    resign_click_payload,
)


@pytest.mark.django_db
def test_complete_accepts_different_valid_sign_time(
    client,
    click_order,
verified_click_provider,
):
    prepare_data = make_payload(click_order)
    prepare_data["sign_time"] = "2026-10-14 10:00:00"
    resign_click_payload(prepare_data)

    prepared = post_prepare(client, prepare_data)
    assert prepared.json()["error"] == 0

    complete_data = make_payload(
        click_order,
        action="1",
        click_trans_id=prepare_data["click_trans_id"],
        prepare_id=prepared.json()["merchant_prepare_id"],
    )
    complete_data["sign_time"] = "2026-10-14 10:05:00"
    resign_click_payload(complete_data)

    completed = post_complete(client, complete_data)

    assert completed.json()["error"] == 0

    tx = ClickTransaction.objects.get(
        click_trans_id=prepare_data["click_trans_id"],
    )
    assert tx.status == ClickTransaction.Status.COMPLETED


@pytest.mark.django_db
def test_repeated_complete_with_new_sign_time_is_idempotent(
    client,
    click_order,
verified_click_provider,
):
    prepare_data = make_payload(click_order)
    prepared = post_prepare(client, prepare_data)

    assert prepared.json()["error"] == 0

    complete_data = make_payload(
        click_order,
        action="1",
        click_trans_id=prepare_data["click_trans_id"],
        prepare_id=prepared.json()["merchant_prepare_id"],
    )

    first = post_complete(client, complete_data)
    assert first.json()["error"] == 0

    repeated = dict(complete_data)
    repeated["sign_time"] = "2026-10-15 12:00:00"
    resign_click_payload(repeated)

    second = post_complete(client, repeated)

    assert second.json()["error"] == 0
    assert (
        first.json()["merchant_confirm_id"]
        == second.json()["merchant_confirm_id"]
    )

    assert ClickTransaction.objects.filter(
        click_trans_id=prepare_data["click_trans_id"],
        status=ClickTransaction.Status.COMPLETED,
    ).count() == 1


@pytest.mark.django_db
def test_repeated_prepare_with_new_sign_time_returns_same_id(
    client,
    click_order,
verified_click_provider,
):
    payload = make_payload(click_order)

    first = post_prepare(client, payload)
    assert first.json()["error"] == 0

    repeated = dict(payload)
    repeated["sign_time"] = "2026-10-15 12:30:00"
    resign_click_payload(repeated)

    second = post_prepare(client, repeated)

    assert second.json()["error"] == 0
    assert (
        first.json()["merchant_prepare_id"]
        == second.json()["merchant_prepare_id"]
    )

    assert ClickTransaction.objects.filter(
        click_trans_id=payload["click_trans_id"],
    ).count() == 1
