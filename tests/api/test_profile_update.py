
import pytest

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient


User = get_user_model()


@pytest.fixture
def profile_user(db):
    return User.objects.create_user(
        phone_number="+998901234567",
        password="StrongTestPassword123!",
        full_name="Test User",
        role="student",
    )


@pytest.mark.django_db
def test_profile_requires_authentication():
    client = APIClient()

    response = client.get(reverse("auth-me"))

    assert response.status_code == 401


@pytest.mark.django_db
def test_profile_update_requires_authentication():
    client = APIClient()

    response = client.patch(
        reverse("auth-me"),
        {"full_name": "Test User"},
        format="json",
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_profile_update_success(profile_user):
    client = APIClient()
    client.force_authenticate(user=profile_user)

    response = client.patch(
        reverse("auth-me"),
        {
            "full_name": "Ali Valiyev",
            "email": "ali@example.com",
        },
        format="json",
    )

    assert response.status_code == 200

    profile_user.refresh_from_db()

    assert profile_user.full_name == "Ali Valiyev"
    assert profile_user.email == "ali@example.com"


@pytest.mark.django_db
def test_profile_cannot_change_role(profile_user):
    client = APIClient()
    client.force_authenticate(user=profile_user)

    old_role = profile_user.role

    response = client.patch(
        reverse("auth-me"),
        {
            "full_name": "Ali Valiyev",
            "role": "admin",
            "is_staff": True,
            "is_superuser": True,
            "is_phone_verified": True,
        },
        format="json",
    )

    assert response.status_code == 200

    profile_user.refresh_from_db()

    assert profile_user.role == old_role
    assert profile_user.is_staff is False
    assert profile_user.is_superuser is False
    assert profile_user.is_phone_verified is False


@pytest.mark.django_db
def test_profile_rejects_empty_name(profile_user):
    client = APIClient()
    client.force_authenticate(user=profile_user)

    response = client.patch(
        reverse("auth-me"),
        {"full_name": "   "},
        format="json",
    )

    assert response.status_code == 400
