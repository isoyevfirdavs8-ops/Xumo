from django.urls import path

from .click_views import (
    ClickPrepareView,
    ClickCompleteView,
)
from .views import PaymentIntegrationPendingView


urlpatterns = [
    path(
        "click/prepare/",
        ClickPrepareView.as_view(),
        name="click-prepare",
    ),
    path(
        "click/complete/",
        ClickCompleteView.as_view(),
        name="click-complete",
    ),
    path(
        "payme/",
        PaymentIntegrationPendingView.as_view(),
        name="payme-callback",
    ),
]