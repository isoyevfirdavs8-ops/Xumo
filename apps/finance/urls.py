from django.urls import path
from .views import revenue_dashboard

urlpatterns = [
    path(
        "revenue/",
        revenue_dashboard,
        name="finance-revenue",
    ),
]