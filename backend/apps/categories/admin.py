from django.contrib import admin
from .models import SubCategory


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "category",
        "is_active",
        "sort_order",
    )
    list_filter = ("category", "is_active")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}