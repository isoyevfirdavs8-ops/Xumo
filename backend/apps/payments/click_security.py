
import hashlib
import hmac

from datetime import datetime
from decimal import Decimal, InvalidOperation

from .security import (
    PaymentVerificationError,
    get_provider_credentials,
)


MAX_CLICK_ID_LENGTH = 100
MAX_MERCHANT_ID_LENGTH = 150
MAX_AMOUNT_LENGTH = 32


def validate_click_sign_time(value):
    """
    Click sign_time sintaktik validatsiyasi.

    Callback yoshini yoki timezone'ini
    tekshirmaydi.
    """
    if not isinstance(value, str):
        raise PaymentVerificationError(
            "Click sign_time string bo'lishi kerak."
        )

    try:
        parsed = datetime.strptime(
            value,
            "%Y-%m-%d %H:%M:%S",
        )
    except ValueError as exc:
        raise PaymentVerificationError(
            "Click sign_time formati noto'g'ri."
        ) from exc

    if parsed.strftime("%Y-%m-%d %H:%M:%S") != value:
        raise PaymentVerificationError(
            "Click sign_time formati noto'g'ri."
        )

    return parsed



def validate_click_identifier(
    value,
    *,
    field_name,
    max_length,
):
    """
    Click callback identifikatorini tekshiradi.

    Bo'sh qiymatlar, bool, noto'g'ri tiplar,
    whitespace va uzun identifikatorlar
    rad etiladi.
    """

    if isinstance(value, bool):
        raise PaymentVerificationError(
            f"{field_name} noto'g'ri."
        )

    if not isinstance(value, (str, int)):
        raise PaymentVerificationError(
            f"{field_name} noto'g'ri."
        )

    value = str(value)

    if (
        not value
        or value != value.strip()
        or len(value) > max_length
        or any(char.isspace() for char in value)
        or not value.isprintable()
    ):
        raise PaymentVerificationError(
            f"{field_name} noto'g'ri."
        )

    return value



def validate_click_prepare_id(value):
    """
    merchant_prepare_id musbat butun son
    bo'lishini tekshiradi.
    """
    if isinstance(value, bool):
        raise PaymentVerificationError(
            "merchant_prepare_id noto'g'ri."
        )

    value = str(value)

    if (
        not value
        or not value.isascii()
        or not value.isdecimal()
        or len(value) > 19
        or int(value) <= 0
        or int(value) > 9223372036854775807
    ):
        raise PaymentVerificationError(
            "merchant_prepare_id noto'g'ri."
        )

    return value


def validate_click_amount(value):
    """
    Click callback summasini tekshiradi.

    Moliyaviy qiymatlar Decimal yordamida
    validatsiya qilinadi.
    """
    if isinstance(value, (bool, float)):
        raise PaymentVerificationError(
            "Click amount noto'g'ri."
        )

    value = str(value)

    if (
        not value
        or len(value) > MAX_AMOUNT_LENGTH
        or value != value.strip()
    ):
        raise PaymentVerificationError(
            "Click amount noto'g'ri."
        )

    try:
        amount = Decimal(value)
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise PaymentVerificationError(
            "Click amount noto'g'ri."
        ) from exc

    if (
        not amount.is_finite()
        or amount <= 0
        or amount.as_tuple().exponent < -2
        or amount > Decimal("999999999999.99")
    ):
        raise PaymentVerificationError(
            "Click amount noto'g'ri."
        )

    return amount


def validate_click_error(value):
    """
    Click Complete error qiymati butun son
    ko'rinishida bo'lishini tekshiradi.

    Bu tekshiruv error qiymatining
    kriptografik haqiqiyligini kafolatlamaydi.
    """
    if isinstance(value, bool):
        raise PaymentVerificationError(
            "Click error noto'g'ri."
        )

    value = str(value)

    if (
        not value
        or len(value) > 12
        or value != value.strip()
    ):
        raise PaymentVerificationError(
            "Click error noto'g'ri."
        )

    digits = value[1:] if value.startswith("-") else value

    if (
        not digits
        or not digits.isascii()
        or not digits.isdecimal()
    ):
        raise PaymentVerificationError(
            "Click error noto'g'ri."
        )

    return value


def verify_click_signature(data):
    """
    Click callback:
    1. Credential validation
    2. Required fields
    3. Input validation
    4. MD5 signature verification
    """
    credentials = get_provider_credentials("click")

    required = [
        "click_trans_id",
        "service_id",
        "merchant_trans_id",
        "amount",
        "action",
        "sign_time",
        "sign_string",
    ]

    for field in required:
        if field not in data:
            raise PaymentVerificationError(
                f"{field} majburiy."
            )

    click_trans_id = validate_click_identifier(
        data["click_trans_id"],
        field_name="click_trans_id",
        max_length=MAX_CLICK_ID_LENGTH,
    )

    merchant_trans_id = validate_click_identifier(
        data["merchant_trans_id"],
        field_name="merchant_trans_id",
        max_length=MAX_MERCHANT_ID_LENGTH,
    )

    if str(data["service_id"]) != str(
        credentials["service_id"]
    ):
        raise PaymentVerificationError(
            "Click service_id mos emas."
        )

    validate_click_sign_time(data["sign_time"])
    validate_click_amount(data["amount"])

    action = str(data["action"])

    if action not in {"0", "1"}:
        raise PaymentVerificationError(
            "Click action noto'g'ri."
        )

    if action == "1":
        if "merchant_prepare_id" not in data:
            raise PaymentVerificationError(
                "merchant_prepare_id majburiy."
            )

        if "error" not in data:
            raise PaymentVerificationError(
                "Click Complete uchun error maydoni majburiy."
            )

        validate_click_prepare_id(
            data["merchant_prepare_id"]
        )
        validate_click_error(data["error"])

    # Mavjud Click SHOP API MD5 formulasi
    # o'zgartirilmaydi.
    parts = [
        click_trans_id,
        str(data["service_id"]),
        credentials["secret_key"],
        merchant_trans_id,
    ]

    if action == "1":
        parts.append(
            str(data["merchant_prepare_id"])
        )

    parts.extend([
        str(data["amount"]),
        action,
        str(data["sign_time"]),
    ])

    expected = hashlib.md5(
        "".join(parts).encode("utf-8")
    ).hexdigest()

    if not hmac.compare_digest(
        str(data["sign_string"]).lower(),
        expected.lower(),
    ):
        raise PaymentVerificationError(
            "Click imzosi noto'g'ri."
        )

    return True
