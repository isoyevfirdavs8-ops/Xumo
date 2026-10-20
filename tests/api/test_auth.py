import pytest

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        phone_number="+998901234567",
        password="SecurePassword123!",
        full_name="Test User",
    )


@pytest.mark.django_db
def test_register_success(api_client):
    response = api_client.post(
        reverse("auth-register"),
        {
            "phone_number": "+998909876543",
            "full_name": "New User",
            "password": "SecurePassword123!",
        },
        format="json",
    )

    assert response.status_code == 201
    assert User.objects.filter(phone_number="+998909876543").exists()


@pytest.mark.django_db
def test_register_cannot_assign_admin(api_client):
    response = api_client.post(
        reverse("auth-register"),
        {
            "phone_number": "+998909876543",
            "full_name": "New User",
            "password": "SecurePassword123!",
            "role": "admin",
            "is_superuser": True,
        },
        format="json",
    )

    assert response.status_code == 201

    created_user = User.objects.get(phone_number="+998909876543")

    assert created_user.role == User.Role.USER
    assert created_user.is_superuser is False


@pytest.mark.django_db
def test_duplicate_phone_rejected(api_client, user):
    response = api_client.post(
        reverse("auth-register"),
        {
            "phone_number": user.phone_number,
            "full_name": "Duplicate User",
            "password": "SecurePassword123!",
        },
        format="json",
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_login_success(api_client, user):
    response = api_client.post(
        reverse("auth-login"),
        {
            "phone_number": user.phone_number,
            "password": "SecurePassword123!",
        },
        format="json",
    )

    assert response.status_code == 200
    assert "access" in response.data
    assert "refresh" in response.data


@pytest.mark.django_db
def test_login_wrong_password(api_client, user):
    response = api_client.post(
        reverse("auth-login"),
        {
            "phone_number": user.phone_number,
            "password": "WrongPassword123!",
        },
        format="json",
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_profile_requires_authentication(api_client):
    response = api_client.get(reverse("auth-me"))
    assert response.status_code == 401


@pytest.mark.django_db
def test_profile_with_jwt(api_client, user):
    login_response = api_client.post(
        reverse("auth-login"),
        {
            "phone_number": user.phone_number,
            "password": "SecurePassword123!",
        },
        format="json",
    )

    access = login_response.data["access"]

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    response = api_client.get(reverse("auth-me"))

    assert response.status_code == 200
    assert response.data["phone_number"] == user.phone_number


@pytest.mark.django_db
def test_logout_blacklists_refresh_token(api_client, user):
    login_response = api_client.post(
        reverse("auth-login"),
        {
            "phone_number": user.phone_number,
            "password": "SecurePassword123!",
        },
        format="json",
    )

    access = login_response.data["access"]
    refresh = login_response.data["refresh"]

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    logout_response = api_client.post(
        reverse("auth-logout"),
        {"refresh": refresh},
        format="json",
    )

    assert logout_response.status_code == 204

    refresh_response = api_client.post(
        reverse("auth-refresh"),
        {"refresh": refresh},
        format="json",
    )

    assert refresh_response.status_code == 401