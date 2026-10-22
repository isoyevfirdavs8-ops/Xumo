
from django.urls import path

from .views import (
    PublicCoachListView,
    PublicCoachDetailView,
    DashboardCoachListCreateView,
    DashboardCoachDetailView,
)

urlpatterns = [
    path(
        "coaches/",
        PublicCoachListView.as_view(),
        name="public-coach-list",
    ),
    path(
        "coaches/<int:pk>/",
        PublicCoachDetailView.as_view(),
        name="public-coach-detail",
    ),
    path(
        "dashboard/coaches/",
        DashboardCoachListCreateView.as_view(),
        name="dashboard-coach-list",
    ),
    path(
        "dashboard/coaches/<int:pk>/",
        DashboardCoachDetailView.as_view(),
        name="dashboard-coach-detail",
    ),
]
