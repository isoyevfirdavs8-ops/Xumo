import pytest

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from apps.users.services import (
    MAX_FAILED_ATTEMPTS,
    is_account_locked,
    record_failed_login,
    clear_failed_logins,
)

User = get_user_model()


@pytest.fixture
def test_user(db):
    return User.objects.create_user(
        phone_number="+998901234555",
        password="SecurePassword123!",
        full_name="Security Test User",
    )


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_failed_attempt_counter(test_user):
    phone = test_user.phone_number

    clear_failed_logins(phone)

    assert is_account_locked(phone) is False

    for _ in range(MAX_FAILED_ATTEMPTS):
        record_failed_login(phone)

    assert is_account_locked(phone) is True


@pytest.mark.django_db
def test_clear_failed_attempts(test_user):
    phone = test_user.phone_number

    record_failed_login(phone)
    clear_failed_logins(phone)

    assert is_account_locked(phone) is False


@pytest.mark.django_db
def test_login_wrong_password_increments_counter(
    api_client,
    test_user,
):
    phone = test_user.phone_number

    response = api_client.post(
        reverse("auth-login"),
        {
            "phone_number": phone,
            "password": "WrongPassword123!",
        },
        format="json",
    )

    assert response.status_code == 401
    assert is_account_locked(phone) is False


@pytest.mark.django_db
def test_locked_account_rejects_login(
    api_client,
    test_user,
):
    phone = test_user.phone_number

    for _ in range(MAX_FAILED_ATTEMPTS):
        record_failed_login(phone)

    response = api_client.post(
        reverse("auth-login"),
        {
            "phone_number": phone,
            "password": "SecurePassword123!",
        },
        format="json",
    )

    assert response.status_code == 429


@pytest.mark.django_db
def test_successful_login_clears_counter(
    api_client,
    test_user,
):
    phone = test_user.phone_number

    record_failed_login(phone)

    response = api_client.post(
        reverse("auth-login"),
        {
            "phone_number": phone,
            "password": "SecurePassword123!",
        },
        format="json",
    )

    assert response.status_code == 200
    assert is_account_locked(phone) is False

@pytest.mark.django_db
def test_five_wrong_passwords_lock_account(
    api_client,
    test_user,
    monkeypatch,
):
    from apps.users.views import LoginView

    monkeypatch.setattr(LoginView, "throttle_classes", [])

    phone = test_user.phone_number
    clear_failed_logins(phone)

    for _ in range(MAX_FAILED_ATTEMPTS):
        response = api_client.post(
            reverse("auth-login"),
            {
                "phone_number": phone,
                "password": "WrongPassword123!",
            },
            format="json",
        )

        assert response.status_code == 401

    assert is_account_locked(phone) is True

    response = api_client.post(
        reverse("auth-login"),
        {
            "phone_number": phone,
            "password": "SecurePassword123!",
        },
        format="json",
    )

    assert response.status_code == 429