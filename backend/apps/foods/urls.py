
from django.urls import path

from .views import (
    PublicSubCategoryListView,
    PublicFoodListView,
    DashboardSubCategoryListCreateView,
    DashboardSubCategoryDetailView,
    DashboardFoodListCreateView,
    DashboardFoodDetailView,
)

urlpatterns = [
    # PUBLIC
    path(
        "subcategories/",
        PublicSubCategoryListView.as_view(),
        name="public-subcategories",
    ),
    path(
        "foods/",
        PublicFoodListView.as_view(),
        name="public-foods",
    ),

    # DASHBOARD SUBCATEGORIES
    path(
        "dashboard/subcategories/",
        DashboardSubCategoryListCreateView.as_view(),
        name="dashboard-subcategories",
    ),
    path(
        "dashboard/subcategories/<int:pk>/",
        DashboardSubCategoryDetailView.as_view(),
        name="dashboard-subcategory-detail",
    ),

    # DASHBOARD FOODS
    path(
        "dashboard/foods/",
        DashboardFoodListCreateView.as_view(),
        name="dashboard-foods",
    ),
    path(
        "dashboard/foods/<int:pk>/",
        DashboardFoodDetailView.as_view(),
        name="dashboard-food-detail",
    ),
]
