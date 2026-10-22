
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import BoxingAcademyViewSet
from .subscription_views import (
    BoxingSubscriptionViewSet,
    demo_payment_start,
    demo_payment_complete,
    my_boxing_payments,
)

router = DefaultRouter()
router.register(
    "academies",
    BoxingAcademyViewSet,
    basename="boxing-academy",
)
router.register(
    "subscriptions",
    BoxingSubscriptionViewSet,
    basename="boxing-subscription",
)

urlpatterns = [
    path(
        "payments/demo/start/",
        demo_payment_start,
        name="boxing-demo-start",
    ),
    path(
        "payments/demo/<uuid:payment_id>/complete/",
        demo_payment_complete,
        name="boxing-demo-complete",
    ),
    path(
        "payments/my/",
        my_boxing_payments,
        name="boxing-my-payments",
    ),
    path("", include(router.urls)),
]
