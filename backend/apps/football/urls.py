
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    FootballFieldViewSet,
    FootballAvailabilityView,
    CreateHourlyBookingView,
    MyHourlyBookingsView,
)

from .academy_dashboard_views import (
    DashboardFootballAcademyListCreateView,
    DashboardFootballAcademyDetailView,
    DashboardFootballAcademyStatusView,
    DashboardFootballAcademyImageUploadView,
    DashboardFootballAcademyImageDeleteView,
    DashboardFootballAcademyImagePrimaryView,
)

from .academy_views import (
    FootballAcademyListView,
    FootballAcademyDetailView,
    FootballSubscriptionCreateView,
    MyFootballSubscriptionsView,
    DashboardFootballSubscriptionsView,
    DashboardFootballSubscriptionDetailView,
)


router = DefaultRouter()

router.register(
    "fields",
    FootballFieldViewSet,
    basename="football-field",
)


urlpatterns = [
    # Stadionlar
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

    # Public Football Academy
    path(
        "academies/",
        FootballAcademyListView.as_view(),
        name="football-academy-list",
    ),
    path(
        "academies/<int:pk>/",
        FootballAcademyDetailView.as_view(),
        name="football-academy-detail",
    ),

    # Obunalar
    path(
        "subscriptions/",
        FootballSubscriptionCreateView.as_view(),
        name="football-subscription-create",
    ),
    path(
        "my-subscriptions/",
        MyFootballSubscriptionsView.as_view(),
        name="football-my-subscriptions",
    ),

    # Dashboard obunalari
    path(
        "dashboard/subscriptions/<int:pk>/",
        DashboardFootballSubscriptionDetailView.as_view(),
        name="football-dashboard-subscription-detail",
    ),
    path(
        "dashboard/subscriptions/",
        DashboardFootballSubscriptionsView.as_view(),
        name="football-dashboard-subscriptions",
    ),

    # Dashboard akademiyalar CRUD
    path(
        "dashboard/academies/",
        DashboardFootballAcademyListCreateView.as_view(),
        name="football-dashboard-academies",
    ),
    path(
        "dashboard/academies/<int:pk>/",
        DashboardFootballAcademyDetailView.as_view(),
        name="football-dashboard-academy-detail",
    ),

    # Rasmlar
    path(
        "dashboard/academies/<int:pk>/images/",
        DashboardFootballAcademyImageUploadView.as_view(),
        name="football-dashboard-academy-image-upload",
    ),
    path(
        "dashboard/academies/<int:pk>/images/<int:image_id>/primary/",
        DashboardFootballAcademyImagePrimaryView.as_view(),
        name="football-dashboard-academy-image-primary",
    ),
    path(
        "dashboard/academies/<int:pk>/images/<int:image_id>/",
        DashboardFootballAcademyImageDeleteView.as_view(),
        name="football-dashboard-academy-image-delete",
    ),

    # Arxivlash va qayta faollashtirish
    path(
        "dashboard/academies/<int:pk>/archive/",
        DashboardFootballAcademyStatusView.as_view(),
        {"action": "archive"},
        name="football-dashboard-academy-archive",
    ),
    path(
        "dashboard/academies/<int:pk>/activate/",
        DashboardFootballAcademyStatusView.as_view(),
        {"action": "activate"},
        name="football-dashboard-academy-activate",
    ),
]

urlpatterns += router.urls
