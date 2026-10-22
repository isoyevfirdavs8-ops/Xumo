
import pytest

from django.urls import reverse
from rest_framework.test import APIClient


@pytest.fixture
def client():
    return APIClient()


@pytest.mark.django_db
def test_click_prepare_rejects_unsigned_request(
    client,
    settings,
):
    settings.PAYMENT_MODE = "disabled"

    response = client.post(
        reverse("click-prepare"),
        {
            "click_trans_id": "123",
            "merchant_trans_id": "football:1",
            "amount": "100000",
            "action": "0",
        },
    )

    assert response.status_code == 200
    assert response.data["error"] != 0


@pytest.mark.django_db
def test_click_complete_rejects_unsigned_request(
    client,
    settings,
):
    settings.PAYMENT_MODE = "disabled"

    response = client.post(
        reverse("click-complete"),
        {
            "click_trans_id": "123",
            "merchant_trans_id": "football:1",
            "merchant_prepare_id": "1",
            "amount": "100000",
            "action": "1",
        },
    )

    assert response.status_code == 200
    assert response.data["error"] != 0
