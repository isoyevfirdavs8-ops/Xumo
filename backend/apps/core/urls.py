from django.urls import path
from .views import SiteNavigationView

urlpatterns = [
    path("navigation/", SiteNavigationView.as_view(), name="site-navigation"),
]