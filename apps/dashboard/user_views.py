
from django.contrib.auth import get_user_model

from rest_framework import generics, permissions, serializers
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import PageNumberPagination

from apps.dashboard.permissions import IsDashboardAdmin


User = get_user_model()


# ==========================================
# DASHBOARD USER SERIALIZER
# ==========================================

class DashboardUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User

        fields = (
            "id",
            "phone_number",
            "full_name",
            "email",
            "role",
            "is_phone_verified",
            "is_active",
            "date_joined",
        )

        read_only_fields = fields


# ==========================================
# PAGINATION
# ==========================================

class DashboardUserPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


# ==========================================
# USERS LIST
# ==========================================

class DashboardUserListView(generics.ListAPIView):
    serializer_class = DashboardUserSerializer

    permission_classes = [
        permissions.IsAuthenticated,
        IsDashboardAdmin,
    ]

    pagination_class = DashboardUserPagination

    filter_backends = [
        SearchFilter,
        OrderingFilter,
    ]

    search_fields = [
        "full_name",
        "phone_number",
        "email",
    ]

    ordering_fields = [
        "date_joined",
        "full_name",
    ]

    ordering = [
        "-date_joined",
        "-pk",
    ]

    def get_queryset(self):
        queryset = User.objects.all()

        role = self.request.query_params.get("role")
        is_active = self.request.query_params.get("is_active")

        if role:
            queryset = queryset.filter(role=role)

        if is_active is not None:
            if is_active == "true":
                queryset = queryset.filter(is_active=True)
            elif is_active == "false":
                queryset = queryset.filter(is_active=False)

        return queryset.order_by("-date_joined", "-pk")


# ==========================================
# USER DETAIL
# ==========================================

class DashboardUserDetailView(generics.RetrieveAPIView):
    serializer_class = DashboardUserSerializer

    permission_classes = [
        permissions.IsAuthenticated,
        IsDashboardAdmin,
    ]

    queryset = User.objects.all()
