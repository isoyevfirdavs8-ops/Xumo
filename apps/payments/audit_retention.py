
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.payments.models import PaymentReconciliationAudit


def cleanup_old_payment_audits(
    *,
    retention_days=180,
    dry_run=True,
):
    """
    Eski monitoring auditlarini tozalash.

    dry_run=True:
        faqat sonini hisoblaydi.

    dry_run=False:
        eski STALE_PREPARED auditlarni o'chiradi.

    Payment transactionlarga tegmaydi.
    """
    if (
        type(retention_days) is not int
        or retention_days < 30
    ):
        raise ValueError(
            "retention_days must be >= 30"
        )

    cutoff = timezone.now() - timedelta(
        days=retention_days
    )

    queryset = PaymentReconciliationAudit.objects.filter(
        result=(
            PaymentReconciliationAudit.Result.STALE_PREPARED
        ),
        created_at__lt=cutoff,
    )

    if dry_run:
        return {
            "deleted": 0,
            "eligible": queryset.count(),
            "dry_run": True,
        }

    with transaction.atomic():
        deleted_count, _ = queryset.delete()

    return {
        "deleted": deleted_count,
        "eligible": deleted_count,
        "dry_run": False,
    }
