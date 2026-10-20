from rest_framework.exceptions import PermissionDenied

from apps.coaches.models import Coach


def is_attendance_admin(user):
    return (
        user.is_superuser
        or (
            user.is_staff
            and user.role in ("admin", "manager")
        )
    )


def get_coach_profile(user):
    if user.role != "coach":
        return None

    return Coach.objects.filter(
        user=user,
        is_active=True,
    ).first()


def can_access_subscription(user, subscription, sport):
    if is_attendance_admin(user):
        return True

    coach = get_coach_profile(user)

    if coach is None:
        return False

    if sport == "boxing":
        return coach.boxing_academies.filter(
            pk=subscription.academy_id
        ).exists()

    if sport == "tennis":
        return coach.tennis_courts.filter(
            pk=subscription.court_id
        ).exists()

    return False


def require_subscription_access(user, subscription, sport):
    if not can_access_subscription(user, subscription, sport):
        raise PermissionDenied(
            "Siz ushbu o'quvchining davomatini boshqara olmaysiz."
        )