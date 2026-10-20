
from rest_framework.permissions import BasePermission


class IsDashboardAdmin(BasePermission):
    message = "Dashboard uchun admin huquqi talab qilinadi."

    def has_permission(self, request, view):
        user = request.user

        return bool(
            user
            and user.is_authenticated
            and (
                user.is_superuser
                or (
                    user.role == "admin"
                    and user.is_staff
                )
            )
        )
