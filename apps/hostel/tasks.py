
import logging

from celery import shared_task

from .services import expire_hostel_reservations


logger = logging.getLogger(__name__)


@shared_task(
    name="hostel.expire_reservations",
    ignore_result=True,
)
def expire_hostel_reservations_task():
    """
    To'lov muddati tugagan hostel bronlarini bo'shatadi.
    Celery Beat tomonidan har daqiqada chaqiriladi.
    """
    count = expire_hostel_reservations()

    logger.info(
        "Hostel expiration completed: %s reservations expired",
        count,
    )

    return count
