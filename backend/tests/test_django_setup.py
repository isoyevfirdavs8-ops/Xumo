from django.conf import settings
from django.apps import apps
from django.contrib.auth import get_user_model


def test_django_configuration():
    print("\nAUTH_USER_MODEL:", settings.AUTH_USER_MODEL)
    print("Auth installed:", apps.is_installed("django.contrib.auth"))
    print("Apps ready:", apps.ready)

    assert settings.AUTH_USER_MODEL == "users.CustomUser"
    assert apps.is_installed("django.contrib.auth")
    assert get_user_model()._meta.label == "users.CustomUser"