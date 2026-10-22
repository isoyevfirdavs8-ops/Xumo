import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from tests.api.test_football_academy_click_complete import (
    subscription,
    click_settings,
)


pytestmark = pytest.mark.django_db


def make_user(phone, *, role="student", is_staff=False):
    User = get_user_model()

    return User.objects.create_user(
        phone_number=phone,
        password="StrongPass123!",
        role=role,
        is_staff=is_staff,
    )


def test_anonymous_cannot_view_subscriptions(subscription):
    client = APIClient()

    response = client.get(
        reverse("football-dashboard-subscriptions")
    )

    assert response.status_code in (401, 403)


def test_regular_user_cannot_view_subscriptions(subscription):
    user = make_user("+998901234570")
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(
        reverse("football-dashboard-subscriptions")
    )

    assert response.status_code == 403


def test_staff_without_admin_role_cannot_view(subscription):
    user = make_user(
        "+998901234571",
        is_staff=True,
    )

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(
        reverse("football-dashboard-subscriptions")
    )

    assert response.status_code == 403


def test_admin_can_view_subscriptions(subscription):
    user = make_user(
        "+998901234572",
        role="admin",
        is_staff=True,
    )

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(
        reverse("football-dashboard-subscriptions")
    )

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["id"] == subscription.pk


def test_admin_can_view_subscription_detail(subscription):
    user = make_user(
        "+998901234573",
        role="admin",
        is_staff=True,
    )

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(
        reverse(
            "football-dashboard-subscription-detail",
            kwargs={"pk": subscription.pk},
        )
    )

    assert response.status_code == 200
    assert response.data["id"] == subscription.pk
    assert response.data["phone_number"] == subscription.user.phone_number


def test_invalid_month_rejected(subscription):
    user = make_user(
        "+998901234574",
        role="admin",
        is_staff=True,
    )

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(
        reverse("football-dashboard-subscriptions"),
        {"month": "2026-10-15"},
    )

    assert response.status_code == 400