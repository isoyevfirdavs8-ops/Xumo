from rest_framework.exceptions import PermissionDenied

from apps.coaches.models import Coach


def is_attendance_admin(user):
    if not user or not user.is_authenticated or not user.is_active:
        return False

    return (
        user.is_superuser
        or (
            user.is_staff
            and user.role in ("admin", "manager")
        )
    )


def get_coach_profile(user):
    if (
        not user
        or not user.is_authenticated
        or not user.is_active
        or user.role != "coach"
    ):
        return None

    return (
        Coach.objects
        .filter(
            user=user,
            is_active=True,
        )
        .first()
    )


def can_access_subscription(user, subscription, sport):
    # 1. Admin va manager barcha sport obunalarini boshqaradi.
    if is_attendance_admin(user):
        return True

    # 2. Football Academy:
    # Hozircha akademiyaga murabbiy biriktirish mavjud emas.
    # Shuning uchun coach va oddiy userlarga ruxsat berilmaydi.
    if sport == "football":
        return False

    # 3. Murabbiy profilini tekshiramiz.
    coach = get_coach_profile(user)

    if coach is None:
        return False

    # 4. Boxing: murabbiy faqat o'z akademiyasidagi
    # o'quvchilar davomatini boshqaradi.
    if sport == "boxing":
        return coach.boxing_academies.filter(
            pk=subscription.academy_id
        ).exists()

    # 5. Tennis: murabbiy faqat o'ziga biriktirilgan
    # kortdagi o'quvchilar davomatini boshqaradi.
    if sport == "tennis":
        return coach.tennis_courts.filter(
            pk=subscription.court_id
        ).exists()

    # 6. Noma'lum sport turiga ruxsat yo'q.
    return False


def require_subscription_access(user, subscription, sport):
    if not can_access_subscription(
        user=user,
        subscription=subscription,
        sport=sport,
    ):
        raise PermissionDenied(
            "Siz ushbu o'quvchining davomatini boshqara olmaysiz."
        )