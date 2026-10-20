from .base import *


DEBUG = False

if not ALLOWED_HOSTS:
    raise ValueError(
        "ALLOWED_HOSTS must be configured in production."
    )

if DATABASES["default"]["ENGINE"] != "django.db.backends.postgresql":
    raise ValueError(
        "Production requires PostgreSQL."
    )

SECURE_SSL_REDIRECT = True

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

SECURE_CONTENT_TYPE_NOSNIFF = True

X_FRAME_OPTIONS = "DENY"