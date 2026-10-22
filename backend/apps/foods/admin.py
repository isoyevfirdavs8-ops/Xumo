from django.contrib import admin
from .models import Food


@admin.register(Food)
class FoodAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "subcategory",
        "price",
        "stock",
        "is_active",
    )
    list_filter = ("subcategory", "is_active")
    search_fields = ("name",)
