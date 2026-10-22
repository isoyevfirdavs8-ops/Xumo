import pytest

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from apps.users.permissions import (
    IsAdmin,
    IsManager,
    IsCoach,
    IsAdminOrManager,
)

User = get_user_model()


@pytest.fixture
def client_api():
    return APIClient()


@pytest.fixture
def normal_user(db):
    return User.objects.create_user(
        phone_number="+998901112233",
        password="StrongPassword123!",
        full_name="Normal User",
    )


@pytest.mark.django_db
def test_register_invalid_phone(client_api, settings):
    settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["register"] = "1000/min"

    response = client_api.post(
        reverse("auth-register"),
        {
            "phone_number": "901234567",
            "full_name": "Test",
            "password": "StrongPassword123!",
        },
        format="json",
    )

    assert response.status_code == 400
    assert "phone_number" in response.data

@pytest.mark.django_db
def test_user_default_role(normal_user):
    assert normal_user.role == "user"


@pytest.mark.django_db
def test_password_is_hashed(normal_user):
    assert normal_user.password != "StrongPassword123!"
    assert normal_user.check_password("StrongPassword123!")


@pytest.mark.django_db
def test_inactive_user_cannot_login(client_api, normal_user):
    normal_user.is_active = False
    normal_user.save()

    response = client_api.post(
        reverse("auth-login"),
        {
            "phone_number": normal_user.phone_number,
            "password": "StrongPassword123!",
        },
        format="json",
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_normal_user_is_not_admin(normal_user):
    permission = IsAdmin()

    request = type("Request", (), {"user": normal_user})()

    assert permission.has_permission(request, None) is False


@pytest.mark.django_db
def test_manager_permission():
    manager = User(
        phone_number="+998901112244",
        role="manager",
    )

    request = type("Request", (), {"user": manager})()

    assert IsManager().has_permission(request, None) is True
    assert IsAdminOrManager().has_permission(request, None) is True


@pytest.mark.django_db
def test_coach_permission():
    coach = User(
        phone_number="+998901112255",
        role="coach",
    )

    request = type("Request", (), {"user": coach})()

    assert IsCoach().has_permission(request, None) is True
    assert IsAdminOrManager().has_permission(request, None) is False


@pytest.mark.django_db
def test_admin_requires_staff():
    user = User(
        phone_number="+998901112266",
        role="admin",
        is_staff=False,
    )

    request = type("Request", (), {"user": user})()

    assert IsAdmin().has_permission(request, None) is False


@pytest.mark.django_db
def test_staff_admin_allowed():
    admin = User(
        phone_number="+998901112277",
        role="admin",
        is_staff=True,
    )

    request = type("Request", (), {"user": admin})()

    assert IsAdmin().has_permission(request, None) is True


@pytest.mark.django_db
def test_user_cannot_modify_role_via_profile():
    User = get_user_model()

    user = User.objects.create_user(
        phone_number="+998901112233",
        password="StrongPassword123!",
        full_name="Oddiy foydalanuvchi",
    )

    client = APIClient()
    client.force_authenticate(user=user)

    original_role = user.role
    original_phone = user.phone_number

    response = client.patch(
        reverse("auth-me"),
        {
            "full_name": "Yangilangan foydalanuvchi",
            "role": "admin",
            "is_staff": True,
            "is_superuser": True,
            "is_phone_verified": True,
            "phone_number": "+998909999999",
        },
        format="json",
    )

    assert response.status_code == 200

    user.refresh_from_db()

    # Ruxsat berilgan maydon o'zgargan.
    assert user.full_name == "Yangilangan foydalanuvchi"

    # Muhim security maydonlari o'zgarmagan.
    assert user.role == original_role
    assert user.is_staff is False
    assert user.is_superuser is False
    assert user.is_phone_verified is False
    assert user.phone_number == original_phone
