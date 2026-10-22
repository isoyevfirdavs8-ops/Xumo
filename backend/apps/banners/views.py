
from rest_framework import generics
from rest_framework.permissions import AllowAny

from apps.dashboard.permissions import IsDashboardAdmin
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Banner
from .serializers import BannerSerializer


class PublicBannerListView(generics.ListAPIView):
    serializer_class = BannerSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        return Banner.objects.filter(is_active=True)


class DashboardBannerListCreateView(
    generics.ListCreateAPIView
):
    queryset = Banner.objects.all()
    serializer_class = BannerSerializer
    permission_classes = [IsDashboardAdmin]
    parser_classes = [MultiPartParser, FormParser]


class DashboardBannerDetailView(
    generics.RetrieveUpdateDestroyAPIView
):
    queryset = Banner.objects.all()
    serializer_class = BannerSerializer
    permission_classes = [IsDashboardAdmin]
    parser_classes = [MultiPartParser, FormParser]
