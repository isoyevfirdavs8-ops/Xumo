
from datetime import datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.football.booking_services import (
    HOLD_MINUTES,
    create_hourly_booking,
    expire_old_holds,
)
from apps.football.models import (
    FootballField,
    HourlyBooking,
    FieldClosure,
)


TASHKENT = ZoneInfo("Asia/Tashkent")


@pytest.fixture
def booking_user(db):
    User = get_user_model()

    return User.objects.create_user(
        phone_number="+998901234567",
        password="TestPassword123!",
    )


@pytest.fixture
def football_field(db):
    return FootballField.objects.create(
        name="Integration Test Stadium",
        field_type=FootballField.FieldType.SUMMER,
        hourly_price=Decimal("150000.00"),
        status=FootballField.Status.ACTIVE,
    )


@pytest.fixture
def booking_times():
    local_now = timezone.localtime(
        timezone.now(),
        TASHKENT,
    )

    booking_date = local_now.date() + timedelta(days=2)

    start_at = datetime.combine(
        booking_date,
        time(10, 0),
        tzinfo=TASHKENT,
    )

    end_at = start_at + timedelta(hours=1)

    return start_at, end_at


@pytest.mark.django_db
def test_create_football_booking(
    booking_user,
    football_field,
    booking_times,
):
    start_at, end_at = booking_times

    before = timezone.now()

    booking = create_hourly_booking(
        user=booking_user,
        field_id=football_field.pk,
        start_at=start_at,
        end_at=end_at,
    )

    after = timezone.now()

    assert booking.pk is not None
    assert booking.user_id == booking_user.pk
    assert booking.field_id == football_field.pk
    assert booking.start_at == start_at
    assert booking.end_at == end_at

    assert (
        booking.status
        == HourlyBooking.Status.PENDING_PAYMENT
    )

    assert booking.price_snapshot == Decimal("150000.00")

    assert (
        before + timedelta(minutes=HOLD_MINUTES)
        <= booking.hold_expires_at
        <= after + timedelta(minutes=HOLD_MINUTES)
    )


@pytest.mark.django_db
def test_overlapping_booking_rejected(
    booking_user,
    football_field,
    booking_times,
):
    start_at, end_at = booking_times

    create_hourly_booking(
        user=booking_user,
        field_id=football_field.pk,
        start_at=start_at,
        end_at=end_at,
    )

    with pytest.raises(ValidationError):
        create_hourly_booking(
            user=booking_user,
            field_id=football_field.pk,
            start_at=start_at,
            end_at=end_at,
        )

    assert HourlyBooking.objects.count() == 1


@pytest.mark.django_db
def test_expired_booking_releases_slot(
    booking_user,
    football_field,
    booking_times,
):
    start_at, end_at = booking_times

    booking = create_hourly_booking(
        user=booking_user,
        field_id=football_field.pk,
        start_at=start_at,
        end_at=end_at,
    )

    HourlyBooking.objects.filter(pk=booking.pk).update(
        hold_expires_at=timezone.now() - timedelta(minutes=1)
    )

    expired_count = expire_old_holds(
        field_id=football_field.pk
    )

    booking.refresh_from_db()

    assert expired_count == 1
    assert booking.status == HourlyBooking.Status.EXPIRED

    new_booking = create_hourly_booking(
        user=booking_user,
        field_id=football_field.pk,
        start_at=start_at,
        end_at=end_at,
    )

    assert new_booking.pk != booking.pk
    assert (
        new_booking.status
        == HourlyBooking.Status.PENDING_PAYMENT
    )


@pytest.mark.django_db
def test_inactive_field_rejected(
    booking_user,
    football_field,
    booking_times,
):
    football_field.status = FootballField.Status.MAINTENANCE
    football_field.save(update_fields=["status"])

    start_at, end_at = booking_times

    with pytest.raises(ValidationError):
        create_hourly_booking(
            user=booking_user,
            field_id=football_field.pk,
            start_at=start_at,
            end_at=end_at,
        )

    assert HourlyBooking.objects.count() == 0


@pytest.mark.django_db
def test_field_closure_blocks_booking(
    booking_user,
    football_field,
    booking_times,
):
    start_at, end_at = booking_times

    FieldClosure.objects.create(
        field=football_field,
        start_at=start_at,
        end_at=end_at,
        reason="Texnik xizmat",
    )

    with pytest.raises(ValidationError):
        create_hourly_booking(
            user=booking_user,
            field_id=football_field.pk,
            start_at=start_at,
            end_at=end_at,
        )

    assert HourlyBooking.objects.count() == 0


@pytest.mark.django_db
def test_booking_price_snapshot(
    booking_user,
    football_field,
    booking_times,
):
    start_at, _ = booking_times
    end_at = start_at + timedelta(hours=2)

    booking = create_hourly_booking(
        user=booking_user,
        field_id=football_field.pk,
        start_at=start_at,
        end_at=end_at,
    )

    assert booking.price_snapshot == Decimal("300000.00")

    football_field.hourly_price = Decimal("200000.00")
    football_field.save(update_fields=["hourly_price"])

    booking.refresh_from_db()

    assert booking.price_snapshot == Decimal("300000.00")


@pytest.mark.django_db
def test_adjacent_bookings_allowed(
    booking_user,
    football_field,
    booking_times,
):
    start_at, end_at = booking_times

    first = create_hourly_booking(
        user=booking_user,
        field_id=football_field.pk,
        start_at=start_at,
        end_at=end_at,
    )

    second = create_hourly_booking(
        user=booking_user,
        field_id=football_field.pk,
        start_at=end_at,
        end_at=end_at + timedelta(hours=1),
    )

    assert first.pk != second.pk
    assert HourlyBooking.objects.count() == 2


@pytest.mark.django_db
def test_cancelled_booking_releases_slot(
    booking_user,
    football_field,
    booking_times,
):
    start_at, end_at = booking_times

    first = create_hourly_booking(
        user=booking_user,
        field_id=football_field.pk,
        start_at=start_at,
        end_at=end_at,
    )

    first.status = HourlyBooking.Status.CANCELLED
    first.save(update_fields=["status"])

    second = create_hourly_booking(
        user=booking_user,
        field_id=football_field.pk,
        start_at=start_at,
        end_at=end_at,
    )

    assert second.pk != first.pk


@pytest.mark.django_db
def test_confirmed_booking_blocks_slot(
    booking_user,
    football_field,
    booking_times,
):
    start_at, end_at = booking_times

    booking = create_hourly_booking(
        user=booking_user,
        field_id=football_field.pk,
        start_at=start_at,
        end_at=end_at,
    )

    booking.status = HourlyBooking.Status.CONFIRMED
    booking.save(update_fields=["status"])

    with pytest.raises(ValidationError):
        create_hourly_booking(
            user=booking_user,
            field_id=football_field.pk,
            start_at=start_at,
            end_at=end_at,
        )


@pytest.mark.django_db
def test_database_rejects_overlapping_bookings(
    booking_user,
    football_field,
    booking_times,
):
    start_at, end_at = booking_times

    create_hourly_booking(
        user=booking_user,
        field_id=football_field.pk,
        start_at=start_at,
        end_at=end_at,
    )

    # Servisni chetlab o'tib, bevosita ORM orqali
    # yozilganda ham PostgreSQL constraint ishlashi kerak.
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            HourlyBooking.objects.create(
                field=football_field,
                user=booking_user,
                start_at=start_at,
                end_at=end_at,
                price_snapshot=Decimal("150000.00"),
                status=HourlyBooking.Status.CONFIRMED,
            )

    assert HourlyBooking.objects.count() == 1
