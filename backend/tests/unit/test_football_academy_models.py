from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.football.models import (
    FootballAcademy,
    FootballSubscription,
)


pytestmark = pytest.mark.django_db


def test_create_football_academy():
    academy = FootballAcademy.objects.create(
        name="FC Bukhara Junior Academy",
        monthly_price=Decimal("350000.00"),
    )

    assert academy.pk is not None
    assert academy.status == FootballAcademy.Status.ACTIVE


def test_football_academy_price_must_be_positive():
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            FootballAcademy.objects.create(
                name="Invalid Academy",
                monthly_price=Decimal("0.00"),
            )


def test_football_subscription_month_validation():
    subscription = FootballSubscription(
        month=date(2026, 11, 15),
    )

    with pytest.raises(ValidationError) as exc:
        subscription.clean()

    assert "month" in exc.value.message_dict


def test_football_subscription_default_status():
    subscription = FootballSubscription()

    assert (
        subscription.status
        == FootballSubscription.Status.PENDING_PAYMENT
    )