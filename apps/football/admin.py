
from django.contrib import admin

from .models import (
    FootballField,
    FootballFieldImage,
    FieldPriceHistory,
)


class FootballFieldImageInline(admin.TabularInline):
    model = FootballFieldImage
    extra = 1


@admin.register(FootballField)
class FootballFieldAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "field_type",
        "hourly_price",
        "status",
        "updated_at",
    ]

    list_filter = [
        "field_type",
        "status",
    ]

    search_fields = ["name", "description"]

    list_editable = ["hourly_price", "status"]

    inlines = [FootballFieldImageInline]


@admin.register(FieldPriceHistory)
class FieldPriceHistoryAdmin(admin.ModelAdmin):
    list_display = [
        "field",
        "old_price",
        "new_price",
        "changed_by",
        "changed_at",
    ]

    readonly_fields = [
        "field",
        "old_price",
        "new_price",
        "changed_by",
        "changed_at",
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
