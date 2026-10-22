
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone

from .models import RevenueEntry


@transaction.atomic
def record_successful_payment(
    *,
    category,
    source,
    source_payment_id,
    amount,
    provider,
    user=None,
    paid_at=None,
):
    """
    Haqiqiy tasdiqlangan to'lovni
    markaziy daromad reyestriga yozadi.

    Bir xil to'lov qayta yuborilsa,
    daromad ikkinchi marta yozilmaydi.
    """

    if category not in RevenueEntry.Category.values:
        raise ValueError(
            "Noto'g'ri daromad kategoriyasi."
        )

    if not source or not source_payment_id:
        raise ValueError(
            "To'lov manbasi va ID majburiy."
        )

    if not provider:
        raise ValueError(
            "To'lov provayderi majburiy."
        )

    try:
        if isinstance(amount, float):
            raise ValueError()

        amount = Decimal(str(amount))

    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(
            "To'lov summasi noto'g'ri."
        )

    if (
        not amount.is_finite()
        or amount <= 0
        or amount != amount.quantize(Decimal("0.01"))
    ):
        raise ValueError(
            "To'lov summasi musbat va 2 xonali bo'lishi kerak."
        )

    payment_id = str(source_payment_id)

    entry, created = RevenueEntry.objects.get_or_create(
        source=source,
        source_payment_id=payment_id,
        entry_type=RevenueEntry.EntryType.PAYMENT,
        defaults={
            "category": category,
            "amount": amount,
            "provider": provider,
            "user": user,
            "occurred_at": paid_at or timezone.now(),
        },
    )

    if not created:
        user_id = user.pk if user is not None else None

        if (
            entry.category != category
            or entry.amount != amount
            or entry.provider != provider
            or entry.user_id != user_id
        ):
            raise ValueError(
                "Takroriy to'lov ma'lumotlari mos emas."
            )

    return entry, created
