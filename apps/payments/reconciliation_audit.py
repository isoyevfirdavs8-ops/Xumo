
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.payments.models import (
    ClickTransaction,
    PaymentReconciliationAudit,
)


def audit_stale_click_transaction(
    click_transaction_id,
    *,
    older_than_minutes=15,
):
    """
    Faqat haqiqatan eski PREPARED
    Click tranzaksiyalarini audit qiladi.

    Parallel chaqirilganda duplicate yaratmaydi.
    """
    if (
        type(older_than_minutes) is not int
        or older_than_minutes <= 0
    ):
        raise ValueError(
            "older_than_minutes must be a positive integer"
        )

    with transaction.atomic():
        click_tx = (
            ClickTransaction.objects
            .select_for_update()
            .filter(pk=click_transaction_id)
            .first()
        )

        if click_tx is None:
            return None

        if click_tx.status != ClickTransaction.Status.PREPARED:
            return None

        cutoff = timezone.now() - timedelta(
            minutes=older_than_minutes
        )

        if click_tx.created_at > cutoff:
            return None

        audit, _ = (
            PaymentReconciliationAudit.objects.get_or_create(
                provider="click",
                transaction_id=click_tx.click_trans_id,
                result=(
                    PaymentReconciliationAudit.Result.STALE_PREPARED
                ),
                defaults={
                    "category": click_tx.category,
                    "order_id": click_tx.order_id,
                    "details": {
                        "merchant_prepare_id": (
                            click_tx.merchant_prepare_id
                        ),
                        "transaction_status": click_tx.status,
                    },
                },
            )
        )

        return audit
