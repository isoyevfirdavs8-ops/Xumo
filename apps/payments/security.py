
import hmac
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


SUPPORTED_PROVIDERS = {"click", "payme"}
SUPPORTED_CATEGORIES = {
    "football",
    "restaurant",
    "competition",
}


class PaymentVerificationError(Exception):
    pass


def require_live_payments():
    """
    Real to'lovlar faqat aniq live rejimda
    va merchant sozlamalari mavjud bo'lsa ishlaydi.
    """
    if getattr(settings, "PAYMENT_MODE", "disabled") != "live":
        raise PaymentVerificationError(
            "Haqiqiy to'lovlar hozir yoqilmagan."
        )


def get_provider_credentials(provider):
    require_live_payments()

    if provider == "click":
        credentials = {
            "merchant_id": settings.CLICK_MERCHANT_ID,
            "service_id": settings.CLICK_SERVICE_ID,
            "secret_key": settings.CLICK_SECRET_KEY,
        }
    elif provider == "payme":
        credentials = {
            "merchant_id": settings.PAYME_MERCHANT_ID,
            "secret_key": settings.PAYME_SECRET_KEY,
        }
    else:
        raise PaymentVerificationError(
            "Noma'lum to'lov provayderi."
        )

    if not all(credentials.values()):
        raise ImproperlyConfigured(
            f"{provider} merchant sozlamalari to'liq emas."
        )

    return credentials


def secure_compare(received, expected):
    """
    Imzo yoki credential qiymatlarini
    timing-safe usulda solishtirish.
    """
    return hmac.compare_digest(
        str(received).encode("utf-8"),
        str(expected).encode("utf-8"),
    )


def normalize_amount(value):
    """
    Decimal orqali summani tekshiradi.
    Float bilan moliyaviy hisob-kitob qilmaymiz.
    """
    try:
        if isinstance(value, float):
            raise ValueError

        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise PaymentVerificationError(
            "To'lov summasi noto'g'ri."
        )

    if (
        not amount.is_finite()
        or amount <= 0
        or amount != amount.quantize(Decimal("0.01"))
    ):
        raise PaymentVerificationError(
            "To'lov summasi noto'g'ri."
        )

    return amount


def verify_order_amount(
    *,
    expected_amount,
    received_amount,
):
    expected = normalize_amount(expected_amount)
    received = normalize_amount(received_amount)

    if expected != received:
        raise PaymentVerificationError(
            "To'lov summasi buyurtmaga mos kelmadi."
        )

    return expected
