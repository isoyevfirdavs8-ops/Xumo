
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
def test_prepare_rejects_missing_signature(client, click_order):
    payload = make_payload(click_order)
    payload.pop("sign_string")

    response = post_prepare(client, payload)

    assert response.status_code == 200
    assert response.json()["error"] == -1

    assert not ClickTransaction.objects.filter(
        click_trans_id=payload["click_trans_id"],
    ).exists()


@pytest.mark.django_db
def test_prepare_rejects_missing_service_id(client, click_order):
    payload = make_payload(click_order)
    payload.pop("service_id")

    response = post_prepare(client, payload)

    assert response.status_code == 200
    assert response.json()["error"] == -1


@pytest.mark.django_db
def test_prepare_rejects_missing_amount(client, click_order):
    payload = make_payload(click_order)
    payload.pop("amount")

    response = post_prepare(client, payload)

    assert response.status_code == 200
    assert response.json()["error"] == -1


@pytest.mark.django_db
def test_prepare_rejects_invalid_action(client, click_order):
    payload = make_payload(click_order)
    payload["action"] = "99"

    response = post_prepare(client, payload)

    assert response.status_code == 200
    assert response.json()["error"] == -1


@pytest.mark.django_db
def test_complete_rejects_missing_prepare_id(client, click_order):
    prepare_data = make_payload(click_order)
    prepared = post_prepare(client, prepare_data)

    assert prepared.json()["error"] == 0

    payload = make_payload(
        click_order,
        action="1",
        click_trans_id=prepare_data["click_trans_id"],
        prepare_id=prepared.json()["merchant_prepare_id"],
    )

    payload.pop("merchant_prepare_id")

    response = post_complete(client, payload)

    assert response.status_code == 200
    assert response.json()["error"] == -1

    tx = ClickTransaction.objects.get(
        click_trans_id=prepare_data["click_trans_id"],
    )
    assert tx.status == ClickTransaction.Status.PREPARED


@pytest.mark.django_db
def test_complete_rejects_missing_error_field(client, click_order):
    prepare_data = make_payload(click_order)
    prepared = post_prepare(client, prepare_data)

    assert prepared.json()["error"] == 0

    payload = make_payload(
        click_order,
        action="1",
        click_trans_id=prepare_data["click_trans_id"],
        prepare_id=prepared.json()["merchant_prepare_id"],
    )

    payload.pop("error")

    response = post_complete(client, payload)

    assert response.status_code == 200
    assert response.json()["error"] == -1

    tx = ClickTransaction.objects.get(
        click_trans_id=prepare_data["click_trans_id"],
    )
    assert tx.status == ClickTransaction.Status.PREPARED


@pytest.mark.django_db
def test_prepare_rejects_non_numeric_amount(client, click_order):
    payload = make_payload(click_order)
    payload["amount"] = "not-a-number"

    response = post_prepare(client, payload)

    assert response.status_code == 200

    # Imzo amount qiymatiga bog'liq.
    # Shu sababli o'zgartirilgan amount
    # avval signature tekshiruvidan o'tmaydi.
    assert response.json()["error"] == -1

    assert not ClickTransaction.objects.filter(
        click_trans_id=payload["click_trans_id"],
    ).exists()
