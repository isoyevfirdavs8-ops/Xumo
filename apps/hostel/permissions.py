
from rest_framework.permissions import BasePermission


class IsHostelStaff(BasePermission):
    message = "Bu amal uchun administrator huquqi kerak."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_staff
        )
