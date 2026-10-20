

import pytest

from django.urls import reverse

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
        ("click_trans_id", ""),
        ("click_trans_id", " "),
        ("merchant_trans_id", ""),
        ("merchant_trans_id", " "),
        ("amount", "NaN"),
        ("amount", "Infinity"),
        ("amount", "-100"),
        ("amount", "0"),
        ("action", "invalid"),
        ("sign_time", "invalid"),
        ("sign_string", "invalid"),
    ],
)
def test_invalid_prepare_callback_is_rejected(
    client,
    click_order,
    field,
    value,
):
    payload = make_payload(click_order)
    payload[field] = value

    response = client.post(
        reverse("click-prepare"),
        data=payload,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["error"] != 0


@pytest.mark.django_db
@pytest.mark.parametrize(
    "field,value",
    [
        ("merchant_prepare_id", ""),
        ("merchant_prepare_id", "abc"),
        ("merchant_prepare_id", "-1"),
        ("error", "invalid"),
        ("error", ""),
        ("amount", "NaN"),
        ("amount", "-100"),
        ("sign_string", "invalid"),
    ],
)
def test_invalid_complete_callback_is_rejected(
    client,
    click_order,
    field,
    value,
):
    prepare_payload = make_payload(
        click_order,
        action="0",
    )

    prepare_response = client.post(
        reverse("click-prepare"),
        data=prepare_payload,
    )

    assert prepare_response.json()["error"] == 0

    prepare_id = prepare_response.json()[
        "merchant_prepare_id"
    ]

    complete_payload = make_payload(
        click_order,
        action="1",
        click_trans_id=prepare_payload["click_trans_id"],
        prepare_id=prepare_id,
    )

    complete_payload[field] = value

    response = client.post(
        reverse("click-complete"),
        data=complete_payload,
    )

    assert response.status_code == 200
    assert response.json()["error"] != 0
