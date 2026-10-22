
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsTennisAdminOrReadOnly(BasePermission):
    message = "Bu amal faqat administrator uchun."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        user = request.user

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
