
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from apps.dashboard.permissions import IsDashboardAdmin

from .models import Category
from .serializers import CategorySerializer


class PublicCategoryListView(generics.ListAPIView):
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        return Category.objects.filter(
            is_active=True
        ).order_by("sort_order", "id")


class PublicCategoryDetailView(generics.RetrieveAPIView):
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        return Category.objects.filter(is_active=True)


class DashboardCategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsDashboardAdmin]
    parser_classes = [MultiPartParser, FormParser, JSONParser]


class DashboardCategoryDetailView(
    generics.RetrieveUpdateDestroyAPIView
):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsDashboardAdmin]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
