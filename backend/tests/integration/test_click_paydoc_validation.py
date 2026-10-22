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
def test_prepare_rejects_different_paydoc_id(
    client,
    click_order,
):
    data = make_payload(click_order)
    data["click_paydoc_id"] = "paydoc-001"

    first = post_prepare(client, data)

    assert first.json()["error"] == 0

    repeated = dict(data)
    repeated["click_paydoc_id"] = "paydoc-002"

    response = post_prepare(client, repeated)

    assert response.json()["error"] == -4

    assert ClickTransaction.objects.filter(
        click_trans_id=data["click_trans_id"],
    ).count() == 1


@pytest.mark.django_db
def test_prepare_accepts_same_paydoc_id(
    client,
    click_order,
):
    data = make_payload(click_order)
    data["click_paydoc_id"] = "paydoc-003"

    first = post_prepare(client, data)
    second = post_prepare(client, data)

    assert first.json()["error"] == 0
    assert second.json()["error"] == 0

    assert (
        first.json()["merchant_prepare_id"]
        == second.json()["merchant_prepare_id"]
    )


@pytest.mark.django_db
def test_complete_rejects_different_paydoc_id(
    client,
    click_order,
):
    prepare_data = make_payload(click_order)
    prepare_data["click_paydoc_id"] = "paydoc-004"

    prepared = post_prepare(client, prepare_data)

    assert prepared.json()["error"] == 0

    complete_data = make_payload(
        click_order,
        action="1",
        click_trans_id=prepare_data["click_trans_id"],
        prepare_id=prepared.json()["merchant_prepare_id"],
    )
    complete_data["click_paydoc_id"] = "paydoc-005"

    response = post_complete(client, complete_data)

    assert response.json()["error"] == -4

    tx = ClickTransaction.objects.get(
        click_trans_id=prepare_data["click_trans_id"],
    )
    assert tx.status == ClickTransaction.Status.PREPARED


@pytest.mark.django_db
def test_complete_accepts_missing_paydoc_id(
    client,
    click_order,
    verified_click_provider,
):
    prepare_data = make_payload(click_order)
    prepare_data["click_paydoc_id"] = "paydoc-006"

    prepared = post_prepare(client, prepare_data)

    assert prepared.json()["error"] == 0

    complete_data = make_payload(
        click_order,
        action="1",
        click_trans_id=prepare_data["click_trans_id"],
        prepare_id=prepared.json()["merchant_prepare_id"],
    )

    assert "click_paydoc_id" not in complete_data

    response = post_complete(client, complete_data)

    assert response.json()["error"] == 0

    tx = ClickTransaction.objects.get(
        click_trans_id=prepare_data["click_trans_id"],
    )
    assert tx.status == ClickTransaction.Status.COMPLETED
