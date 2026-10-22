
from datetime import timedelta

from django.utils import timezone

from apps.payments.models import ClickTransaction


def get_stale_click_transactions(
    *,
    older_than_minutes=15,
    limit=100,
):
    """
    Eski PREPARED Click tranzaksiyalarini topadi.

    Faqat monitoring:
    - settlement qilmaydi
    - cancellation qilmaydi
    - providerga so'rov yubormaydi
    """
    if (
        type(older_than_minutes) is not int
        or older_than_minutes <= 0
    ):
        raise ValueError(
            "older_than_minutes must be a positive integer"
        )

    if (
        type(limit) is not int
        or not 1 <= limit <= 1000
    ):
        raise ValueError(
            "limit must be between 1 and 1000"
        )

    cutoff = timezone.now() - timedelta(
        minutes=older_than_minutes
    )

    return list(
        ClickTransaction.objects.filter(
            status=ClickTransaction.Status.PREPARED,
            created_at__lte=cutoff,
        )
        .order_by("created_at", "merchant_prepare_id")[:limit]
    )


def get_click_reconciliation_summary(
    *,
    older_than_minutes=15,
):
    """
    Eski PREPARED tranzaksiyalar sonini qaytaradi.
    """
    if (
        type(older_than_minutes) is not int
        or older_than_minutes <= 0
    ):
        raise ValueError(
            "older_than_minutes must be a positive integer"
        )

    cutoff = timezone.now() - timedelta(
        minutes=older_than_minutes
    )

    return {
        "stale_prepared_count": (
            ClickTransaction.objects.filter(
                status=ClickTransaction.Status.PREPARED,
                created_at__lte=cutoff,
            ).count()
        ),
        "older_than_minutes": older_than_minutes,
        "checked_at": timezone.now().isoformat(),
    }




def audit_stale_click_transactions(
    *,
    older_than_minutes=15,
    limit=100,
):
    from apps.payments.reconciliation_audit import (
        audit_stale_click_transaction,
    )

    stale_transactions = get_stale_click_transactions(
        older_than_minutes=older_than_minutes,
        limit=limit,
    )

    audit_ids = []

    for click_tx in stale_transactions:
        audit = audit_stale_click_transaction(
            click_tx.pk,
            older_than_minutes=older_than_minutes,
        )

        if audit is not None:
            audit_ids.append(audit.pk)

    return audit_ids
