from django.db import transaction

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from apps.dashboard.permissions import IsDashboardAdmin

from .models import FooterSettings
from .serializers import FooterSettingsSerializer


class PublicFooterSettingsView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request):
        settings, _ = FooterSettings.objects.get_or_create(pk=1)

        serializer = FooterSettingsSerializer(settings)

        return Response(serializer.data)


class DashboardFooterSettingsView(APIView):
    permission_classes = [IsAuthenticated, IsDashboardAdmin]

    def get(self, request):
        settings, _ = FooterSettings.objects.get_or_create(pk=1)

        serializer = FooterSettingsSerializer(settings)

        return Response(serializer.data)

    @transaction.atomic
    def put(self, request):
        settings, _ = FooterSettings.objects.select_for_update().get_or_create(
            pk=1
        )

        serializer = FooterSettingsSerializer(
            settings,
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    @transaction.atomic
    def patch(self, request):
        settings, _ = FooterSettings.objects.select_for_update().get_or_create(
            pk=1
        )

        serializer = FooterSettingsSerializer(
            settings,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)
