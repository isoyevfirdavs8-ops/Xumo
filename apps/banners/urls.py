
from django.urls import path

from .views import (
    PublicBannerListView,
    DashboardBannerListCreateView,
    DashboardBannerDetailView,
)

urlpatterns = [
    path(
        "banners/",
        PublicBannerListView.as_view(),
        name="public-banner-list",
    ),
    path(
        "dashboard/banners/",
        DashboardBannerListCreateView.as_view(),
        name="dashboard-banner-list",
    ),
    path(
        "dashboard/banners/<int:pk>/",
        DashboardBannerDetailView.as_view(),
        name="dashboard-banner-detail",
    ),
]
