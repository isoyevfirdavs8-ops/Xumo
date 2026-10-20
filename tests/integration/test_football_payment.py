
from datetime import datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest
from apps.payments.exceptions import (
    PaymentOrderUnavailable,
    PaymentTransactionConflict,
)
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.football.models import (
    FootballField,
    FootballPayment,
    HourlyBooking,
)
from apps.football.booking_services import create_hourly_booking
from apps.football.payment_services import confirm_football_payment
from apps.finance.models import RevenueEntry


TASHKENT = ZoneInfo("Asia/Tashkent")


@pytest.fixture
def payment_user(db):
    User = get_user_model()

    return User.objects.create_user(
        phone_number="+998901234568",
        password="TestPassword123!",
    )


@pytest.fixture
def payment_field(db):
    return FootballField.objects.create(
        name="Payment Integration Stadium",
        hourly_price=Decimal("150000.00"),
        status=FootballField.Status.ACTIVE,
    )


@pytest.fixture
def pending_booking(payment_user, payment_field):
    booking_date = (
        timezone.localtime(timezone.now(), TASHKENT).date()
        + timedelta(days=2)
    )

    start_at = datetime.combine(
        booking_date,
        time(10, 0),
        tzinfo=TASHKENT,
    )

    return create_hourly_booking(
        user=payment_user,
        field_id=payment_field.pk,
        start_at=start_at,
        end_at=start_at + timedelta(hours=1),
    )


@pytest.mark.django_db
def test_successful_payment_confirms_booking(pending_booking):
    booking = confirm_football_payment(
        booking_id=pending_booking.pk,
        provider="click",
        provider_transaction_id="click-test-001",
        verified_amount=Decimal("150000.00"),
    )

    booking.refresh_from_db()

    assert booking.status == HourlyBooking.Status.CONFIRMED

    payment = FootballPayment.objects.get(booking=booking)

    assert payment.provider == FootballPayment.Provider.CLICK
    assert payment.status == FootballPayment.Status.SUCCEEDED
    assert payment.amount == Decimal("150000.00")
    assert payment.is_demo is False
    assert payment.paid_at is not None


@pytest.mark.django_db
def test_successful_payment_creates_revenue(pending_booking):
    booking = confirm_football_payment(
        booking_id=pending_booking.pk,
        provider="click",
        provider_transaction_id="click-test-002",
        verified_amount=Decimal("150000.00"),
    )

    revenue = RevenueEntry.objects.get(
        source="football_booking",
        source_payment_id=str(booking.pk),
        entry_type=RevenueEntry.EntryType.PAYMENT,
    )

    assert revenue.category == RevenueEntry.Category.FOOTBALL
    assert revenue.amount == Decimal("150000.00")
    assert revenue.provider == "click"
    assert revenue.user_id == booking.user_id


@pytest.mark.django_db
def test_duplicate_callback_is_idempotent(pending_booking):
    kwargs = {
        "booking_id": pending_booking.pk,
        "provider": "click",
        "provider_transaction_id": "click-test-003",
        "verified_amount": Decimal("150000.00"),
    }

    first = confirm_football_payment(**kwargs)
    second = confirm_football_payment(**kwargs)

    assert first.pk == second.pk

    assert FootballPayment.objects.filter(
        booking=pending_booking,
        status=FootballPayment.Status.SUCCEEDED,
    ).count() == 1

    assert RevenueEntry.objects.filter(
        source="football_booking",
        source_payment_id=str(pending_booking.pk),
        entry_type=RevenueEntry.EntryType.PAYMENT,
    ).count() == 1


@pytest.mark.django_db
def test_wrong_payment_amount_rejected(pending_booking):
    with pytest.raises(PaymentTransactionConflict):
        confirm_football_payment(
            booking_id=pending_booking.pk,
            provider="click",
            provider_transaction_id="click-test-004",
            verified_amount=Decimal("100000.00"),
        )

    pending_booking.refresh_from_db()

    assert (
        pending_booking.status
        == HourlyBooking.Status.PENDING_PAYMENT
    )

    assert FootballPayment.objects.count() == 0
    assert RevenueEntry.objects.count() == 0


@pytest.mark.django_db
def test_expired_hold_cannot_be_confirmed(pending_booking):
    HourlyBooking.objects.filter(pk=pending_booking.pk).update(
        hold_expires_at=timezone.now() - timedelta(seconds=1)
    )

    with pytest.raises(PaymentOrderUnavailable):
        confirm_football_payment(
            booking_id=pending_booking.pk,
            provider="click",
            provider_transaction_id="click-test-005",
            verified_amount=Decimal("150000.00"),
        )

    assert FootballPayment.objects.count() == 0
    assert RevenueEntry.objects.count() == 0


@pytest.mark.django_db
def test_cancelled_booking_cannot_be_paid(pending_booking):
    pending_booking.status = HourlyBooking.Status.CANCELLED
    pending_booking.save(update_fields=["status"])

    with pytest.raises(PaymentOrderUnavailable):
        confirm_football_payment(
            booking_id=pending_booking.pk,
            provider="click",
            provider_transaction_id="click-test-006",
            verified_amount=Decimal("150000.00"),
        )

    assert FootballPayment.objects.count() == 0
    assert RevenueEntry.objects.count() == 0


@pytest.mark.django_db
def test_different_transaction_cannot_confirm_twice(pending_booking):
    confirm_football_payment(
        booking_id=pending_booking.pk,
        provider="click",
        provider_transaction_id="click-test-007",
        verified_amount=Decimal("150000.00"),
    )

    with pytest.raises(PaymentTransactionConflict):
        confirm_football_payment(
            booking_id=pending_booking.pk,
            provider="click",
            provider_transaction_id="click-test-008",
            verified_amount=Decimal("150000.00"),
        )

    assert FootballPayment.objects.filter(
        booking=pending_booking,
        status=FootballPayment.Status.SUCCEEDED,
    ).count() == 1

    assert RevenueEntry.objects.filter(
        source="football_booking",
        source_payment_id=str(pending_booking.pk),
    ).count() == 1


@pytest.mark.django_db
def test_payme_payment_supported(pending_booking):
    booking = confirm_football_payment(
        booking_id=pending_booking.pk,
        provider="payme",
        provider_transaction_id="payme-test-001",
        verified_amount=Decimal("150000.00"),
    )

    payment = FootballPayment.objects.get(booking=booking)

    assert payment.provider == FootballPayment.Provider.PAYME
    assert payment.status == FootballPayment.Status.SUCCEEDED

    assert RevenueEntry.objects.filter(
        category=RevenueEntry.Category.FOOTBALL,
        provider="payme",
        source_payment_id=str(booking.pk),
    ).exists()
