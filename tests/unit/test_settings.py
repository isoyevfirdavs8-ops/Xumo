from django.conf import settings
from config.settings import development

def test_secret_key_configured():
    assert bool(settings.SECRET_KEY)


def test_auth_app_installed():
    assert "django.contrib.auth" in settings.INSTALLED_APPS


def test_timezone_configured():
    assert settings.USE_TZ is True


def test_rest_framework_installed():
    assert "rest_framework" in settings.INSTALLED_APPS


def test_django_filter_installed():
    assert "django_filters" in settings.INSTALLED_APPS


def test_spectacular_installed():
    assert "drf_spectacular" in settings.INSTALLED_APPS


def test_language():
    assert settings.LANGUAGE_CODE == "uz"


def test_timezone():
    assert settings.TIME_ZONE == "Asia/Tashkent"


def test_api_pagination():
    assert settings.REST_FRAMEWORK["PAGE_SIZE"] == 20


def test_development_debug():
    assert development.DEBUG is True