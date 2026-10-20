
import logging

from django.utils import timezone

from apps.payments.models import ClickTransaction
from apps.payments.click_reconciliation import (
    get_click_reconciliation_summary,
)


logger = logging.getLogger("payments.reconciliation")


def check_click_reconciliation_health(
    *,
    older_than_minutes=15,
    warning_threshold=10,
    critical_threshold=50,
):
    """
    Click reconciliation monitoring.

    Faqat kuzatadi:
    - payment status o'zgarmaydi
    - settlement bajarilmaydi
    - provider API chaqirilmaydi
    """
    if (
        type(warning_threshold) is not int
        or warning_threshold < 1
    ):
        raise ValueError(
            "warning_threshold must be positive"
        )

    if (
        type(critical_threshold) is not int
        or critical_threshold <= warning_threshold
    ):
        raise ValueError(
            "critical_threshold must exceed warning_threshold"
        )

    summary = get_click_reconciliation_summary(
        older_than_minutes=older_than_minutes
    )

    count = summary["stale_prepared_count"]

    if count >= critical_threshold:
        status = "critical"
        logger.error(
            "Click reconciliation CRITICAL: %s stale transactions",
            count,
        )
    elif count >= warning_threshold:
        status = "warning"
        logger.warning(
            "Click reconciliation WARNING: %s stale transactions",
            count,
        )
    else:
        status = "healthy"
        logger.info(
            "Click reconciliation healthy: %s stale transactions",
            count,
        )

    return {
        "status": status,
        "stale_prepared_count": count,
        "warning_threshold": warning_threshold,
        "critical_threshold": critical_threshold,
        "checked_at": timezone.now().isoformat(),
    }
