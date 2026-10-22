
from rest_framework import generics
from rest_framework.permissions import AllowAny

from apps.categories.models import SubCategory
from apps.categories.serializers import SubCategorySerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from apps.dashboard.permissions import IsDashboardAdmin
from .models import Food
from .serializers import FoodSerializer


class PublicSubCategoryListView(generics.ListAPIView):
    serializer_class = SubCategorySerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        return SubCategory.objects.filter(
            is_active=True,
            category__is_active=True,
        ).select_related("category")


class PublicFoodListView(generics.ListAPIView):
    serializer_class = FoodSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        queryset = Food.objects.filter(
            is_active=True,
            subcategory__is_active=True,
            subcategory__category__is_active=True,
        ).select_related("subcategory")

        subcategory_id = self.request.query_params.get(
            "subcategory"
        )

        if subcategory_id:
            queryset = queryset.filter(
                subcategory_id=subcategory_id
            )

        return queryset


class DashboardSubCategoryListCreateView(
    generics.ListCreateAPIView
):
    serializer_class = SubCategorySerializer
    permission_classes = [
        IsAuthenticated,
        IsDashboardAdmin,
    ]
    parser_classes = [
        MultiPartParser,
        FormParser,
        JSONParser,
    ]
    pagination_class = None

    def get_queryset(self):
        return SubCategory.objects.select_related(
            "category"
        ).order_by("sort_order", "name")


class DashboardSubCategoryDetailView(
    generics.RetrieveUpdateDestroyAPIView
):
    queryset = SubCategory.objects.select_related(
        "category"
    )
    serializer_class = SubCategorySerializer
    permission_classes = [
        IsAuthenticated,
        IsDashboardAdmin,
    ]
    parser_classes = [
        MultiPartParser,
        FormParser,
        JSONParser,
    ]


class DashboardFoodListCreateView(
    generics.ListCreateAPIView
):
    serializer_class = FoodSerializer
    permission_classes = [
        IsAuthenticated,
        IsDashboardAdmin,
    ]
    parser_classes = [
        MultiPartParser,
        FormParser,
        JSONParser,
    ]
    pagination_class = None

    def get_queryset(self):
        return Food.objects.select_related(
            "subcategory",
            "subcategory__category",
        ).order_by("sort_order", "name")


class DashboardFoodDetailView(
    generics.RetrieveUpdateDestroyAPIView
):
    queryset = Food.objects.select_related(
        "subcategory"
    )
    serializer_class = FoodSerializer
    permission_classes = [
        IsAuthenticated,
        IsDashboardAdmin,
    ]
    parser_classes = [
        MultiPartParser,
        FormParser,
        JSONParser,
    ]
