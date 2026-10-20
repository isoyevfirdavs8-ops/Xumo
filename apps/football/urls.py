from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    FootballFieldViewSet,
    FootballAvailabilityView,
    CreateHourlyBookingView,
    MyHourlyBookingsView,
)


router = DefaultRouter()

router.register(
    "fields",
    FootballFieldViewSet,
    basename="football-field",
)


urlpatterns = [
    path(
        "availability/",
        FootballAvailabilityView.as_view(),
        name="football-availability",
    ),
    path(
        "bookings/",
        CreateHourlyBookingView.as_view(),
        name="football-booking-create",
    ),
    path(
        "my-bookings/",
        MyHourlyBookingsView.as_view(),
        name="football-my-bookings",
    ),
]

urlpatterns += router.urls