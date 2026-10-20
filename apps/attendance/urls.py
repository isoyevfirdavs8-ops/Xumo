from django.urls import path

from .views import (
    BoxingAttendanceListView,
    TennisAttendanceListView,
    BoxingAttendanceDetailView,
    TennisAttendanceDetailView,
    AttendanceHistoryView,
    AttendanceMarkView
)

urlpatterns = [
    path(
        "boxing/",
        BoxingAttendanceListView.as_view(),
        name="attendance-boxing-list",
    ),
    path(
        "tennis/",
        TennisAttendanceListView.as_view(),
        name="attendance-tennis-list",
    ),
    path(
        "boxing/<int:pk>/",
        BoxingAttendanceDetailView.as_view(),
        name="attendance-boxing-detail",
    ),
    path(
        "tennis/<int:pk>/",
        TennisAttendanceDetailView.as_view(),
        name="attendance-tennis-detail",
    ),
    path(
        "history/<str:sport>/<int:subscription_id>/",
        AttendanceHistoryView.as_view(),
        name="attendance-history",
    ),
path(
    "records/",
    AttendanceMarkView.as_view(),
    name="attendance-mark",
),
]