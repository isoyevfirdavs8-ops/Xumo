
from django.urls import path

from apps.dashboard.user_views import (
    DashboardUserListView,
    DashboardUserDetailView,
)

urlpatterns = [
    path(
        "users/",
        DashboardUserListView.as_view(),
        name="dashboard-users",
    ),
    path(
        "users/<int:pk>/",
        DashboardUserDetailView.as_view(),
        name="dashboard-user-detail",
    ),
]
