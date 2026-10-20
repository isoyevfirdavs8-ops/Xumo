from rest_framework.permissions import BasePermission


class IsAttendanceManager(BasePermission):
    message = "Davomatni ko'rish uchun ruxsat yo'q."

    def has_permission(self, request, view):
        user = request.user

        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and (
                user.is_superuser
                or (
                    user.is_staff
                    and user.role in ("admin", "manager")
                )
            )
        )




class IsAttendanceStaff(BasePermission):
    message = "Davomat bo'limiga kirish huquqingiz yo'q."

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated or not user.is_active:
            return False

        if user.is_superuser:
            return True

        if user.is_staff and user.role in ("admin", "manager"):
            return True

        return user.role == "coach"