
from dataclasses import dataclass
from decimal import Decimal


class ClickVerificationError(Exception):
    """Provider verification bajarilmadi."""


class ClickVerificationUnavailable(ClickVerificationError):
    """Provider verification sozlanmagan yoki mavjud emas."""


@dataclass(frozen=True)
class ClickVerificationResult:
    verified: bool
    click_trans_id: str
    merchant_trans_id: str
    amount: Decimal


def verify_click_payment_with_provider(
    *,
    click_trans_id: str,
    merchant_trans_id: str,
    amount: Decimal,
) -> ClickVerificationResult:
    """
    Click Merchant API orqali to'lovni tasdiqlash.

    Hozircha rasmiy API spetsifikatsiyasi
    tasdiqlanmagan.

    Xavfsizlik uchun fail-closed:
    hech qachon verified=True qaytarmaydi.
    """
    raise ClickVerificationUnavailable(
        "Click provider verification is not configured."
    )

from decimal import Decimal, InvalidOperation


def validate_click_verification_result(
    *,
    result: ClickVerificationResult,
    click_trans_id: str,
    merchant_trans_id: str,
    amount: Decimal,
) -> None:
    """
    Provider verification natijasini
    kutilayotgan tranzaksiya bilan solishtiradi.

    Mos kelmasa settlement bloklanadi.
    """

    if not isinstance(result, ClickVerificationResult):
        raise ClickVerificationError(
            "Invalid verification result type"
        )

    if result.verified is not True:
        raise ClickVerificationError(
            "Payment is not verified"
        )

    if (
        type(result.click_trans_id) is not str
        or result.click_trans_id != click_trans_id
    ):
        raise ClickVerificationError(
            "Click transaction ID mismatch"
        )

    if (
        type(result.merchant_trans_id) is not str
        or result.merchant_trans_id != merchant_trans_id
    ):
        raise ClickVerificationError(
            "Merchant transaction ID mismatch"
        )

    try:
        if (
            isinstance(result.amount, bool)
            or isinstance(result.amount, float)
        ):
            raise ClickVerificationError(
                "Invalid provider amount type"
            )

        verified_amount = Decimal(str(result.amount))
        expected_amount = Decimal(str(amount))

    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ClickVerificationError(
            "Invalid provider amount"
        ) from exc

    if (
        not verified_amount.is_finite()
        or not expected_amount.is_finite()
        or verified_amount != expected_amount
    ):
        raise ClickVerificationError(
            "Payment amount mismatch"
        )
