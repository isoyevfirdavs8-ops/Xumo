
from django.urls import path

from .views import (
    PublicCategoryListView,
    PublicCategoryDetailView,
    DashboardCategoryListCreateView,
    DashboardCategoryDetailView,
)

urlpatterns = [
    path(
        "categories/",
        PublicCategoryListView.as_view(),
        name="public-category-list",
    ),
    path(
        "categories/<slug:slug>/",
        PublicCategoryDetailView.as_view(),
        name="public-category-detail",
    ),
    path(
        "dashboard/categories/",
        DashboardCategoryListCreateView.as_view(),
        name="dashboard-category-list",
    ),
    path(
        "dashboard/categories/<int:pk>/",
        DashboardCategoryDetailView.as_view(),
        name="dashboard-category-detail",
    ),
]
