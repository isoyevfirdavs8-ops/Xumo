from pathlib import Path

import environ

from decouple import config
BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = BASE_DIR.parent

env = environ.Env(
    DEBUG=(bool, False),
    SECRET_KEY=(str, ""),
    ALLOWED_HOSTS=(list, []),
)

environ.Env.read_env(PROJECT_ROOT / ".env")

TELEGRAM_BOT_TOKEN = env("TELEGRAM_BOT_TOKEN", default="")

TELEGRAM_MANAGER_CHAT_IDS = [
    int(chat_id.strip())
    for chat_id in env(
        "TELEGRAM_MANAGER_CHAT_IDS",
        default="",
    ).split(",")
    if chat_id.strip()
]

TELEGRAM_WEBHOOK_SECRET = env(
    "TELEGRAM_WEBHOOK_SECRET",
    default="",
)

SECRET_KEY = env("SECRET_KEY")

DEBUG = env.bool("DEBUG", default=False)

ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS",
    default=[],
)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "django_filters",
    "drf_spectacular",

"rest_framework_simplejwt.token_blacklist",
"apps.users.apps.UsersConfig",
"apps.core",
"apps.banners.apps.BannersConfig",
"apps.dashboard.apps.DashboardConfig",
"apps.categories.apps.CategoriesConfig",
"apps.coaches.apps.CoachesConfig",
"apps.competitions",
"apps.foods",
"apps.restaurant_orders",
"apps.footer.apps.FooterConfig",
"apps.football.apps.FootballConfig",
"apps.tennis.apps.TennisConfig",
"apps.boxing.apps.BoxingConfig",
"apps.finance.apps.FinanceConfig",
"apps.payments",
"apps.about",
"apps.attendance",

]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": config("DB_HOST", default="127.0.0.1"),
        "PORT": config("DB_PORT", default="5432"),
        "CONN_MAX_AGE": 60,
        "CONN_HEALTH_CHECKS": True,
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "uz"

TIME_ZONE = "Asia/Tashkent"

USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",

    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],

    "DEFAULT_PAGINATION_CLASS": (
        "rest_framework.pagination.PageNumberPagination"
    ),

    "PAGE_SIZE": 20,

    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],

    "DEFAULT_THROTTLE_RATES": {
        # Development muhitida ko‘proq so‘rovga ruxsat
        "anon": "5000/hour" if DEBUG else "300/hour",
        "user": "10000/hour" if DEBUG else "2000/hour",

        # Authentication endpointlari uchun alohida limitlar
        "login": "5/min",
        "register": "3/min",
    },

    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],

    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}


SPECTACULAR_SETTINGS = {
    "TITLE": "FC BUKHARA API",
    "DESCRIPTION": "FC Bukhara Sports Platform REST API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

from datetime import timedelta

AUTH_USER_MODEL = "users.CustomUser"




SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=12),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

REDIS_URL = env(
    "REDIS_URL",
    default="redis://127.0.0.1:6380/0",
)

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
        "KEY_PREFIX": "fcbukhara",
        "TIMEOUT": 300,
    }
}

CELERY_BROKER_URL = env(
    "CELERY_BROKER_URL",
    default="redis://127.0.0.1:6379/0",
)

CELERY_RESULT_BACKEND = env(
    "CELERY_RESULT_BACKEND",
    default="redis://127.0.0.1:6379/1",
)

CELERY_TASK_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Asia/Tashkent"


from decouple import config

# Restaurant payment configuration
RESTAURANT_PAYMENT_MODE = config(
    "RESTAURANT_PAYMENT_MODE",
    default="disabled",
)

if RESTAURANT_PAYMENT_MODE not in {
    "disabled",
    "sandbox",
    "live",
}:
    raise ValueError(
        "Invalid RESTAURANT_PAYMENT_MODE"
    )


# Main payment configuration
PAYMENT_MODE = config(
    "PAYMENT_MODE",
    default="disabled",
)

if PAYMENT_MODE not in {
    "disabled",
    "demo",
    "sandbox",
    "live",
}:
    raise ValueError(
        "Invalid PAYMENT_MODE"
    )

if PAYMENT_MODE == "demo" and not DEBUG:
    raise RuntimeError(
        "Demo to'lovlar faqat DEBUG=True holatida ishlaydi."
    )


# Click credentials
CLICK_MERCHANT_ID = config(
    "CLICK_MERCHANT_ID",
    default="",
)

CLICK_SERVICE_ID = config(
    "CLICK_SERVICE_ID",
    default="",
)

CLICK_SECRET_KEY = config(
    "CLICK_SECRET_KEY",
    default="",
)


# Payme credentials
PAYME_MERCHANT_ID = config(
    "PAYME_MERCHANT_ID",
    default="",
)


