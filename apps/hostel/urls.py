
from django.urls import path
from .availability import HostelAvailabilityView
from .views import (
    HostelRoomDashboardListCreateView,
    HostelRoomDashboardDetailView,
    HostelRoomImageUploadView,
    HostelRoomImageDeleteView,
    HostelRoomImagePrimaryView,
)
from .booking_views import (
    HostelBookingCreateView,
    MyHostelReservationsView,
    HostelReservationDetailView,
)

urlpatterns = [
    path(
        "dashboard/rooms/",
        HostelRoomDashboardListCreateView.as_view(),
        name="hostel-dashboard-rooms",
    ),
    path(
        "dashboard/rooms/<int:pk>/",
        HostelRoomDashboardDetailView.as_view(),
        name="hostel-dashboard-room-detail",
    ),
    path(
        "dashboard/rooms/<int:pk>/images/",
        HostelRoomImageUploadView.as_view(),
        name="hostel-dashboard-room-image-upload",
    ),
    path(
        "dashboard/rooms/<int:pk>/images/<int:image_id>/",
        HostelRoomImageDeleteView.as_view(),
        name="hostel-dashboard-room-image-delete",
    ),
    path(
        "dashboard/rooms/<int:pk>/images/<int:image_id>/primary/",
        HostelRoomImagePrimaryView.as_view(),
        name="hostel-dashboard-room-image-primary",
    ),
path(
    "availability/",
    HostelAvailabilityView.as_view(),
    name="hostel-availability",
),
path(
    "bookings/",
    HostelBookingCreateView.as_view(),
    name="hostel-booking-create",
),
path(
    "my-bookings/",
    MyHostelReservationsView.as_view(),
    name="hostel-my-bookings",
),
path(
    "my-bookings/<int:pk>/",
    HostelReservationDetailView.as_view(),
    name="hostel-my-booking-detail",
),
]
