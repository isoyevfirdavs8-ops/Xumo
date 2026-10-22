from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from apps.football.models import (
    FootballAcademy,
    FootballSubscription,
)


pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    User = get_user_model()

    return User.objects.create_user(
        phone_number="+998901234567",
        password="StrongPass123!",
    )


@pytest.fixture
def academy():
    return FootballAcademy.objects.create(
        name="FC Bukhara Junior Academy",
        description="Professional futbol mashg'ulotlari",
        monthly_price=Decimal("350000.00"),
    )


@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


def test_academy_list_is_public(api_client, academy):
    response = api_client.get(
        reverse("football-academy-list")
    )

    assert response.status_code == 200

    data = response.data
    results = data.get("results", data) if isinstance(data, dict) else data

    assert any(item["id"] == academy.id for item in results)


def test_academy_detail_is_public(api_client, academy):
    response = api_client.get(
        reverse(
            "football-academy-detail",
            kwargs={"pk": academy.pk},
        )
    )

    assert response.status_code == 200
    assert response.data["name"] == academy.name


def test_anonymous_cannot_create_subscription(api_client, academy):
    response = api_client.post(
        reverse("football-subscription-create"),
        {
            "academy": academy.pk,
            "month": "2026-12-01",
        },
        format="json",
    )

    assert response.status_code in (401, 403)


def test_authenticated_user_can_create_subscription(
    authenticated_client,
    academy,
):
    response = authenticated_client.post(
        reverse("football-subscription-create"),
        {
            "academy": academy.pk,
            "month": "2026-12-01",
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.data["status"] == "pending_payment"

    subscription = FootballSubscription.objects.get(
        pk=response.data["id"]
    )

    assert subscription.price_snapshot == Decimal("350000.00")


def test_duplicate_request_returns_existing_subscription(
    authenticated_client,
    academy,
):
    url = reverse("football-subscription-create")

    payload = {
        "academy": academy.pk,
        "month": "2026-12-01",
    }

    first = authenticated_client.post(url, payload, format="json")
    second = authenticated_client.post(url, payload, format="json")

    assert first.status_code == 201
    assert second.status_code == 200
    assert first.data["id"] == second.data["id"]

    assert FootballSubscription.objects.count() == 1


def test_subscription_price_cannot_be_changed_by_client(
    authenticated_client,
    academy,
):
    response = authenticated_client.post(
        reverse("football-subscription-create"),
        {
            "academy": academy.pk,
            "month": "2026-12-01",
            "price_snapshot": "1.00",
            "status": "paid",
        },
        format="json",
    )

    assert response.status_code == 201

    subscription = FootballSubscription.objects.get(
        pk=response.data["id"]
    )

    assert subscription.price_snapshot == academy.monthly_price
    assert subscription.status == "pending_payment"


def test_my_subscriptions_are_private(
    authenticated_client,
    user,
    academy,
):
    FootballSubscription.objects.create(
        user=user,
        academy=academy,
        month=date(2026, 12, 1),
        price_snapshot=academy.monthly_price,
    )

    response = authenticated_client.get(
        reverse("football-my-subscriptions")
    )

    assert response.status_code == 200

    data = response.data
    results = data.get("results", data) if isinstance(data, dict) else data

    assert len(results) == 1