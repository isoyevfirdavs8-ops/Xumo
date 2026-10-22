import hashlib

from django.conf import settings
from django.core.cache import cache


MAX_FAILED_ATTEMPTS = 5
LOCKOUT_SECONDS = 15 * 60


def _cache_key(phone_number):
    normalized = phone_number.strip()
    digest = hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()

    return f"auth:failed:{digest}"


def is_account_locked(phone_number):
    key = _cache_key(phone_number)
    attempts = cache.get(key, 0)

    return attempts >= MAX_FAILED_ATTEMPTS


def record_failed_login(phone_number):
    key = _cache_key(phone_number)

    cache.add(key, 0, timeout=LOCKOUT_SECONDS)

    attempts = cache.incr(key)

    return attempts >= MAX_FAILED_ATTEMPTS


def clear_failed_logins(phone_number):
    cache.delete(_cache_key(phone_number))