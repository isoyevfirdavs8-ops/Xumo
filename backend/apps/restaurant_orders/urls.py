
from django.urls import path

from .views import (
    RestaurantCheckoutView,
    RestaurantOrderDetailView,
    SandboxRestaurantPaymentView,
)

urlpatterns = [
    path(
        "restaurant/checkout/",
        RestaurantCheckoutView.as_view(),
        name="restaurant-checkout",
    ),
    path(
        "restaurant/orders/<uuid:pk>/",
        RestaurantOrderDetailView.as_view(),
        name="restaurant-order-detail",
    ),
    path(
        "restaurant/orders/<uuid:order_id>/sandbox-pay/",
        SandboxRestaurantPaymentView.as_view(),
        name="restaurant-sandbox-payment",
    ),
]
