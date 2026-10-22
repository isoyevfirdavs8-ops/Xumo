
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.football.booking_services import (
    validate_booking_time,
)


TASHKENT = ZoneInfo("Asia/Tashkent")


def future_date_at(hour, minute=0):
    today = timezone.now().astimezone(TASHKENT).date()

    return datetime.combine(
        today + timedelta(days=2),
        datetime.min.time(),
        tzinfo=TASHKENT,
    ).replace(hour=hour, minute=minute)


def test_valid_booking_time():
    start = future_date_at(10)
    end = future_date_at(12)

    validate_booking_time(start, end)


def test_booking_end_before_start():
    start = future_date_at(12)
    end = future_date_at(10)

    with pytest.raises(ValidationError):
        validate_booking_time(start, end)


def test_booking_in_past():
    start = timezone.now() - timedelta(hours=2)
    end = timezone.now() - timedelta(hours=1)

    with pytest.raises(ValidationError):
        validate_booking_time(start, end)


def test_booking_over_12_hours():
    start = future_date_at(20)
    end = start + timedelta(hours=13)

    with pytest.raises(ValidationError):
        validate_booking_time(start, end)


@pytest.mark.parametrize(
    "start_hour, end_hour",
    [
        (15, 17),
        (16, 18),
        (18, 21),
        (19, 20),
    ],
)
def test_booking_closed_hours(
    start_hour,
    end_hour,
):
    start = future_date_at(start_hour)
    end = future_date_at(end_hour)

    with pytest.raises(ValidationError):
        validate_booking_time(start, end)


def test_booking_before_closed_hours():
    start = future_date_at(14)
    end = future_date_at(16)

    validate_booking_time(start, end)


def test_booking_after_closed_hours():
    start = future_date_at(20)
    end = future_date_at(22)

    validate_booking_time(start, end)
