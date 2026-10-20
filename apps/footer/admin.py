from django.contrib import admin

from .models import FooterSettings


@admin.register(FooterSettings)
class FooterSettingsAdmin(admin.ModelAdmin):
    list_display = ("brand_name", "phone", "email", "updated_at")

    def has_add_permission(self, request):
        return (
            super().has_add_permission(request)
            and not FooterSettings.objects.exists()
        )

    def has_delete_permission(self, request, obj=None):
        return False
