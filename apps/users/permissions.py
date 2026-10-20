from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    message = "Faqat administrator uchun."

    def has_permission(self, request, view):
        user = request.user

        return bool(
            user.is_authenticated
            and user.is_active
            and user.is_staff
            and user.role == "admin"
        )


class IsManager(BasePermission):
    message = "Faqat menejer uchun."

    def has_permission(self, request, view):
        user = request.user

        return bool(
            user.is_authenticated
            and user.is_active
            and user.role == "manager"
        )


class IsCoach(BasePermission):
    message = "Faqat murabbiy uchun."

    def has_permission(self, request, view):
        user = request.user

        return bool(
            user.is_authenticated
            and user.is_active
            and user.role == "coach"
        )


class IsAdminOrManager(BasePermission):
    message = "Faqat administrator yoki menejer uchun."

    def has_permission(self, request, view):
        user = request.user

        return bool(
            user.is_authenticated
            and user.is_active
            and (
                (user.is_staff and user.role == "admin")
                or user.role == "manager"
            )
        )