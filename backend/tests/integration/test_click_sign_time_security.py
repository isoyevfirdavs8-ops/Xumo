
import hashlib

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


def resign_click_payload(data):
    """
    Test credentials bilan Click imzosini
    qayta hisoblaydi.
    """
    parts = [
        str(data["click_trans_id"]),
        str(data["service_id"]),
        "test-secret-key",
        str(data["merchant_trans_id"]),
    ]

    if str(data["action"]) == "1":
        parts.append(str(data["merchant_prepare_id"]))

    parts.extend([
        str(data["amount"]),
        str(data["action"]),
        str(data["sign_time"]),
    ])

    data["sign_string"] = hashlib.md5(
        "".join(parts).encode("utf-8")
    ).hexdigest()

    return data


@pytest.mark.django_db
@pytest.mark.parametrize(
    "invalid_time",
    [
        "not-a-date",
        "2026-99-99 99:99:99",
        "2026-02-30 10:00:00",
        "2026-10-15",
        "",
    ],
)
def test_prepare_rejects_invalid_sign_time(
    client,
    click_order,
    invalid_time,
):
    payload = make_payload(click_order)
    payload["sign_time"] = invalid_time
    resign_click_payload(payload)

    response = post_prepare(client, payload)

    assert response.status_code == 200
    assert response.json()["error"] == -1

    assert not ClickTransaction.objects.filter(
        click_trans_id=payload["click_trans_id"],
    ).exists()


@pytest.mark.django_db
def test_prepare_accepts_valid_sign_time(
    client,
    click_order,
):
    payload = make_payload(click_order)
    payload["sign_time"] = "2026-10-15 14:30:00"
    resign_click_payload(payload)

    response = post_prepare(client, payload)

    assert response.status_code == 200
    assert response.json()["error"] == 0


@pytest.mark.django_db
def test_complete_rejects_invalid_sign_time_without_settlement(
    client,
    click_order,
):
    prepare_data = make_payload(click_order)
    prepared = post_prepare(client, prepare_data)

    assert prepared.json()["error"] == 0

    payload = make_payload(
        click_order,
        action="1",
        click_trans_id=prepare_data["click_trans_id"],
        prepare_id=prepared.json()["merchant_prepare_id"],
    )

    payload["sign_time"] = "invalid-complete-time"
    resign_click_payload(payload)

    response = post_complete(client, payload)

    assert response.status_code == 200
    assert response.json()["error"] == -1

    tx = ClickTransaction.objects.get(
        click_trans_id=prepare_data["click_trans_id"],
    )

    assert tx.status == ClickTransaction.Status.PREPARED


@pytest.mark.django_db
def test_old_but_valid_signed_callback_is_not_rejected_by_age(
    client,
    click_order,
):
    """
    Hozircha timestamp age policy yo'q.

    Bu test eski, lekin sintaktik to'g'ri
    sign_time bilan kelgan callbackni tekshiradi.
    """
    payload = make_payload(click_order)
    payload["sign_time"] = "2020-01-01 00:00:00"
    resign_click_payload(payload)

    response = post_prepare(client, payload)

    assert response.status_code == 200
    assert response.json()["error"] == 0
