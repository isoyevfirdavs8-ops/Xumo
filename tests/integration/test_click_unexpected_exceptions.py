
from unittest.mock import patch

import pytest

from django.db import IntegrityError

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
def test_unexpected_value_error_is_not_hidden(
    client,
    click_order,
):
    payload = make_payload(click_order)

    with patch(
        "apps.payments.click_views.prepare_click_payment",
        side_effect=ValueError("Unexpected programming error"),
    ):
        with pytest.raises(ValueError):
            post_prepare(client, payload)

    assert not ClickTransaction.objects.filter(
        click_trans_id=payload["click_trans_id"],
    ).exists()


@pytest.mark.django_db
def test_unexpected_integrity_error_is_not_hidden(
    client,
    click_order,
):
    payload = make_payload(click_order)

    with patch(
        "apps.payments.click_views.prepare_click_payment",
        side_effect=IntegrityError("Unexpected database error"),
    ):
        with pytest.raises(IntegrityError):
            post_prepare(client, payload)

    assert not ClickTransaction.objects.filter(
        click_trans_id=payload["click_trans_id"],
    ).exists()


@pytest.mark.django_db
def test_unexpected_complete_error_does_not_settle_order(
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

    with patch(
        "apps.payments.click_views.complete_click_payment",
        side_effect=ValueError("Unexpected settlement bug"),
    ):
        with pytest.raises(ValueError):
            post_complete(client, payload)

    tx = ClickTransaction.objects.get(
        click_trans_id=prepare_data["click_trans_id"],
    )

    assert tx.status == ClickTransaction.Status.PREPARED
