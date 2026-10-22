
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import TennisSubscriptionViewSet
from .views import TennisCourtViewSet
from .payment_views import (
    DemoPaymentStartView,
    DemoPaymentCompleteView,
    MyTennisPaymentsView,
)

router = DefaultRouter()
router.register(
    "courts",
    TennisCourtViewSet,
    basename="tennis-court",
)
router.register(
    "subscriptions",
    TennisSubscriptionViewSet,
    basename="tennis-subscription",
)

urlpatterns = [
    path("", include(router.urls)),
]

urlpatterns = [
    path("", include(router.urls)),

    path(
        "payments/demo/start/",
        DemoPaymentStartView.as_view(),
        name="tennis-demo-payment-start",
    ),

    path(
        "payments/demo/<uuid:payment_id>/complete/",
        DemoPaymentCompleteView.as_view(),
        name="tennis-demo-payment-complete",
    ),

    path(
        "payments/my/",
        MyTennisPaymentsView.as_view(),
        name="tennis-my-payments",
    ),
]
