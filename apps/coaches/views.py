
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import (
    MultiPartParser,
    FormParser,
    JSONParser,
)

from apps.dashboard.permissions import IsDashboardAdmin

from .models import Coach
from .serializers import CoachSerializer


class PublicCoachListView(generics.ListAPIView):
    serializer_class = CoachSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        queryset = Coach.objects.select_related("category").filter(
            is_active=True,
            category__is_active=True,
        )

        category_slug = self.request.query_params.get("category")

        if category_slug:
            queryset = queryset.filter(
                category__slug=category_slug
            )

        return queryset.order_by("sort_order", "id")


class PublicCoachDetailView(generics.RetrieveAPIView):
    serializer_class = CoachSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Coach.objects.select_related("category").filter(
            is_active=True,
            category__is_active=True,
        )


class DashboardCoachListCreateView(generics.ListCreateAPIView):
    queryset = Coach.objects.select_related("category").all()
    serializer_class = CoachSerializer
    permission_classes = [IsAuthenticated, IsDashboardAdmin]
    parser_classes = [MultiPartParser, FormParser, JSONParser]


class DashboardCoachDetailView(
    generics.RetrieveUpdateDestroyAPIView
):
    queryset = Coach.objects.select_related("category").all()
    serializer_class = CoachSerializer
    permission_classes = [IsAuthenticated, IsDashboardAdmin]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
