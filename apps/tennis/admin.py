
from django.contrib import admin

from .models import (
    TennisCourt,
    TennisCourtImage,
    TennisSubscription,
)


class TennisCourtImageInline(admin.TabularInline):
    model = TennisCourtImage
    extra = 1


@admin.register(TennisCourt)
class TennisCourtAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "monthly_price",
        "status",
        "created_at",
    )

    list_filter = ("status",)
    search_fields = ("name",)
    inlines = [TennisCourtImageInline]


@admin.register(TennisSubscription)
class TennisSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "court",
        "month",
        "price_snapshot",
        "status",
        "paid_at",
    )

    list_filter = (
        "status",
        "month",
        "court",
    )

    search_fields = (
        "user__username",
        "court__name",
    )

    readonly_fields = (
        "price_snapshot",
        "status",
        "paid_at",
        "payment_expires_at",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

