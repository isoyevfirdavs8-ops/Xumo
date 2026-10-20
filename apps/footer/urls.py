from django.urls import path

from .views import (
    PublicFooterSettingsView,
    DashboardFooterSettingsView,
)

urlpatterns = [
    path(
        "site/footer/",
        PublicFooterSettingsView.as_view(),
        name="public-footer-settings",
    ),
    path(
        "dashboard/footer/",
        DashboardFooterSettingsView.as_view(),
        name="dashboard-footer-settings",
    ),
]