
from .base import *

DEBUG = False

ALLOWED_HOSTS = [
    "testserver",
    "localhost",
    "127.0.0.1",
]

# Test client HTTP so'rovlarini HTTPS'ga yo'naltirmaydi.
SECURE_SSL_REDIRECT = False

# Testlarda tashqi email yuborilmaydi.
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Redis production cache'idan foydalanmaymiz.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "xumo-pytest",
    }
}

# Celery vazifalari test jarayonida sinxron ishlaydi.
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True


DATABASES["default"]["CONN_MAX_AGE"] = 0

DATABASES["default"]["TEST"] = {
    "NAME": "test_xumo",
}
