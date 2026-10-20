from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from rest_framework.exceptions import PermissionDenied, ValidationError as DRFValidationError

from apps.attendance.access import can_access_subscription
from apps.attendance.models import Attendance
from apps.attendance.services import mark_attendance
from apps.boxing.models import BoxingAcademy, BoxingSubscription
from apps.tennis.models import TennisCourt, TennisSubscription
from apps.coaches.models import Coach
from apps.categories.models import Category
from apps.users.models import CustomUser


pytestmark = pytest.mark.django_db


@pytest.fixture
def attendance_data():
    admin = CustomUser.objects.create_user(
        phone_number="+998901111111",
        password="TestPass123!",
        full_name="Admin",
        role="admin",
        is_staff=True,
    )

    coach_user = CustomUser.objects.create_user(
        phone_number="+998902222222",
        password="TestPass123!",
        full_name="Coach",
        role="coach",
    )

    student = CustomUser.objects.create_user(
        phone_number="+998903333333",
        password="TestPass123!",
        full_name="Student",
    )

    academy = BoxingAcademy.objects.create(
        name="Test Boxing Academy",
        monthly_price=Decimal("300000.00"),
    )

    other_academy = BoxingAcademy.objects.create(
        name="Other Boxing Academy",
        monthly_price=Decimal("300000.00"),
    )

    court = TennisCourt.objects.create(
        name="Test Tennis Court",
        monthly_price=Decimal("400000.00"),
    )

    # Category modelining majburiy maydonlariga qarab
    # ushbu yaratish qismi moslashtirilishi mumkin.
    category = Category.objects.create(
        name="Test Boxing Category",
    )

    coach = Coach.objects.create(
        user=coach_user,
        category=category,
        full_name="Test Coach",
        specialization="Boxing",
        image="coaches/test.jpg",
    )

    coach.boxing_academies.add(academy)

    boxing_subscription = BoxingSubscription.objects.create(
        user=student,
        academy=academy,
        month=date(2026, 10, 1),
        price_snapshot=Decimal("300000.00"),
        status=BoxingSubscription.Status.PAID,
    )

    other_subscription = BoxingSubscription.objects.create(
        user=student,
        academy=other_academy,
        month=date(2026, 10, 1),
        price_snapshot=Decimal("300000.00"),
        status=BoxingSubscription.Status.PAID,
    )

    tennis_subscription = TennisSubscription.objects.create(
        user=student,
        court=court,
        month=date(2026, 10, 1),
        price_snapshot=Decimal("400000.00"),
        status=TennisSubscription.Status.PAID,
    )

    return {
        "admin": admin,
        "coach_user": coach_user,
        "student": student,
        "academy": academy,
        "other_academy": other_academy,
        "court": court,
        "coach": coach,
        "boxing_subscription": boxing_subscription,
        "other_subscription": other_subscription,
        "tennis_subscription": tennis_subscription,
    }


def test_coach_can_access_assigned_academy(attendance_data):
    assert can_access_subscription(
        attendance_data["coach_user"],
        attendance_data["boxing_subscription"],
        "boxing",
    ) is True


def test_coach_cannot_access_other_academy(attendance_data):
    assert can_access_subscription(
        attendance_data["coach_user"],
        attendance_data["other_subscription"],
        "boxing",
    ) is False


def test_coach_cannot_access_unassigned_tennis_court(attendance_data):
    assert can_access_subscription(
        attendance_data["coach_user"],
        attendance_data["tennis_subscription"],
        "tennis",
    ) is False


def test_admin_can_access_all_subscriptions(attendance_data):
    assert can_access_subscription(
        attendance_data["admin"],
        attendance_data["other_subscription"],
        "boxing",
    ) is True


def test_coach_cannot_mark_other_academy(attendance_data):
    with pytest.raises(PermissionDenied):
        mark_attendance(
            sport="boxing",
            subscription_id=attendance_data["other_subscription"].id,
            date=date(2026, 10, 1),
            status="present",
            user=attendance_data["coach_user"],
        )


def test_unpaid_subscription_is_rejected(attendance_data):
    subscription = attendance_data["boxing_subscription"]
    subscription.status = BoxingSubscription.Status.PENDING_PAYMENT
    subscription.save(update_fields=["status"])

    with pytest.raises(DRFValidationError):
        mark_attendance(
            sport="boxing",
            subscription_id=subscription.id,
            date=date(2026, 10, 1),
            status="present",
            user=attendance_data["admin"],
        )


def test_attendance_create_and_update(attendance_data):
    subscription = attendance_data["boxing_subscription"]
    admin = attendance_data["admin"]

    first, created = mark_attendance(
        sport="boxing",
        subscription_id=subscription.id,
        date=date(2026, 10, 1),
        status="present",
        user=admin,
    )

    assert created is True
    assert first.status == "present"

    second, created = mark_attendance(
        sport="boxing",
        subscription_id=subscription.id,
        date=date(2026, 10, 1),
        status="absent",
        user=admin,
    )

    assert created is False
    assert second.pk == first.pk
    assert second.status == "absent"

    assert Attendance.objects.filter(
        boxing_subscription=subscription,
        date=date(2026, 10, 1),
    ).count() == 1


def test_attendance_rejects_wrong_month(attendance_data):
    with pytest.raises(DRFValidationError):
        mark_attendance(
            sport="boxing",
            subscription_id=attendance_data["boxing_subscription"].id,
            date=date(2026, 9, 30),
            status="present",
            user=attendance_data["admin"],
        )


def test_attendance_database_unique_constraint(attendance_data):
    subscription = attendance_data["boxing_subscription"]
    admin = attendance_data["admin"]

    Attendance.objects.create(
        boxing_subscription=subscription,
        date=date(2026, 10, 1),
        status="present",
        marked_by=admin,
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Attendance.objects.create(
                boxing_subscription=subscription,
                date=date(2026, 10, 1),
                status="absent",
                marked_by=admin,
            )