
import pytest

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient


User = get_user_model()


@pytest.fixture
def ordinary_user(db):
    return User.objects.create_user(
        phone_number="+998901234567",
        password="StrongPassword123!",
        full_name="Oddiy User",
    )


@pytest.fixture
def dashboard_admin(db):
    return User.objects.create_superuser(
        phone_number="+998909876543",
        password="StrongAdminPassword123!",
        full_name="Dashboard Admin",
    )


@pytest.mark.django_db
def test_users_requires_authentication():
    response = APIClient().get(reverse("dashboard-users"))

    assert response.status_code == 401


@pytest.mark.django_db
def test_ordinary_user_cannot_list_users(ordinary_user):
    client = APIClient()
    client.force_authenticate(user=ordinary_user)

    response = client.get(reverse("dashboard-users"))

    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_can_list_users(dashboard_admin, ordinary_user):
    client = APIClient()
    client.force_authenticate(user=dashboard_admin)

    response = client.get(reverse("dashboard-users"))

    assert response.status_code == 200
    assert response.data["count"] >= 2


@pytest.mark.django_db
def test_admin_can_search_users(dashboard_admin, ordinary_user):
    client = APIClient()
    client.force_authenticate(user=dashboard_admin)

    response = client.get(
        reverse("dashboard-users"),
        {"search": "Oddiy User"},
    )

    assert response.status_code == 200
    assert response.data["count"] == 1


@pytest.mark.django_db
def test_user_password_never_exposed(dashboard_admin, ordinary_user):
    client = APIClient()
    client.force_authenticate(user=dashboard_admin)

    response = client.get(
        reverse("dashboard-user-detail", args=[ordinary_user.pk])
    )

    assert response.status_code == 200
    assert "password" not in response.data
    assert "is_superuser" not in response.data


@pytest.mark.django_db
def test_users_endpoint_read_only(dashboard_admin, ordinary_user):
    client = APIClient()
    client.force_authenticate(user=dashboard_admin)

    response = client.patch(
        reverse("dashboard-user-detail", args=[ordinary_user.pk]),
        {"role": "admin"},
        format="json",
    )

    assert response.status_code == 405
