
from rest_framework.permissions import BasePermission, SAFE_METHODS


def is_boxing_admin(user):
    return bool(
        user.is_authenticated
        and (
            user.is_superuser
            or (
                user.is_staff
                and getattr(user, "role", None) == "admin"
            )
        )
    )


class IsBoxingAdminOrReadOnly(BasePermission):
    message = "Bu amal faqat administrator uchun."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        return is_boxing_admin(request.user)
