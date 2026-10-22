
from django.contrib import admin

from .models import Competition, TicketOrder, Ticket


@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "start_time",
        "min_age",
        "max_age",
        "price",
        "capacity",
        "is_active",
    )

    list_filter = (
        "is_active",
        "start_time",
    )

    search_fields = ("name", "description")


@admin.register(TicketOrder)
class TicketOrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "competition",
        "full_name",
        "phone_number",
        "quantity",
        "total_amount",
        "provider",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "provider",
        "created_at",
    )

    search_fields = (
        "full_name",
        "phone_number",
    )

    readonly_fields = (
        "id",
        "created_at",
        "paid_at",
    )


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "ticket_number",
        "order",
        "is_used",
        "created_at",
    )

    list_filter = ("is_used",)

