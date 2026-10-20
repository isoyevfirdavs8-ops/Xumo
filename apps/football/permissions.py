from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsFootballAdminOrReadOnly(BasePermission):
    message = "Bu amalni faqat administrator bajarishi mumkin."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        user = request.user

        return bool(
            user
            and user.is_authenticated
            and (
                user.is_superuser
                or (
                    user.is_staff
                    and getattr(user, "role", None) == "admin"
                )
            )
        )