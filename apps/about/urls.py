from django.urls import path
from .views import AboutListCreateView, AboutDetailView

urlpatterns = [
    path('', AboutListCreateView.as_view(), name='about-list'),
    path('<int:pk>/', AboutDetailView.as_view(), name='about-detail'),
]
