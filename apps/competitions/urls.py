from .order_views import (
    TicketOrderCreateView,
    MyTicketOrdersView,
)
from django.urls import path

from .views import (
    PublicCompetitionListView,
    PublicCompetitionDetailView,
    DashboardCompetitionListCreateView,
    DashboardCompetitionDetailView,
)

urlpatterns = [
    path(
        "competitions/",
        PublicCompetitionListView.as_view(),
        name="public-competition-list",
    ),
    path(
        "competitions/<int:pk>/",
        PublicCompetitionDetailView.as_view(),
        name="public-competition-detail",
    ),
    path(
        "dashboard/competitions/",
        DashboardCompetitionListCreateView.as_view(),
        name="dashboard-competition-list",
    ),
    path(
        "dashboard/competitions/<int:pk>/",
        DashboardCompetitionDetailView.as_view(),
        name="dashboard-competition-detail",
    ),
path(
    "ticket-orders/",
    TicketOrderCreateView.as_view(),
    name="ticket-order-create",
),
path(
    "ticket-orders/my/",
    MyTicketOrdersView.as_view(),
    name="my-ticket-orders",
),
]
