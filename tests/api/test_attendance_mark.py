from datetime import date
from unittest.mock import patch

import pytest
from rest_framework.exceptions import ValidationError

from apps.attendance.services import mark_attendance


def test_invalid_sport():
    with pytest.raises(ValidationError):
        mark_attendance(
            sport="football",
            subscription_id=1,
            date=date(2026, 10, 19),
            status="present",
            user=None,
        )


@patch("apps.attendance.services.timezone.localdate")
def test_future_date_is_rejected(mock_today):
    mock_today.return_value = date(2026, 10, 19)

    with pytest.raises(ValidationError):
        mark_attendance(
            sport="boxing",
            subscription_id=1,
            date=date(2026, 10, 20),
            status="present",
            user=None,
        )