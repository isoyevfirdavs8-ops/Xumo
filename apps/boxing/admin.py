
from django.contrib import admin

from .models import (
    BoxingAcademy,
    BoxingAcademyImage,
    BoxingSubscription,
    BoxingPayment,
)


class BoxingAcademyImageInline(admin.TabularInline):
    model = BoxingAcademyImage
    extra = 1


@admin.register(BoxingAcademy)
class BoxingAcademyAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "monthly_price",
        "status",
        "created_at",
    )

    list_filter = ("status",)
    search_fields = ("name",)
    inlines = [BoxingAcademyImageInline]


@admin.register(BoxingSubscription)
class BoxingSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "academy",
        "month",
        "price_snapshot",
        "status",
        "paid_at",
    )

    list_filter = (
        "status",
        "month",
        "academy",
    )

    search_fields = (
        "academy__name",
        "user__username",
    )

    readonly_fields = (
        "user",
        "academy",
        "month",
        "price_snapshot",
        "status",
        "payment_expires_at",
        "paid_at",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(BoxingPayment)
class BoxingPaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "subscription",
        "provider",
        "amount",
        "status",
        "is_demo",
        "paid_at",
    )

    list_filter = (
        "provider",
        "status",
        "is_demo",
    )

    readonly_fields = (
        "id",
        "subscription",
        "provider",
        "amount",
        "status",
        "is_demo",
        "paid_at",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
