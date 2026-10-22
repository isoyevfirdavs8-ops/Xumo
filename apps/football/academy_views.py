from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .academy_serializers import FootballSubscriptionCreateInputSerializer, DashboardFootballSubscriptionSerializer
from rest_framework.exceptions import ValidationError
from .academy_serializers import (
    FootballAcademySerializer,
    FootballSubscriptionSerializer,
)
from .academy_pagination import FootballAcademyDashboardPagination
from .academy_services import create_football_subscription
from .models import FootballAcademy, FootballSubscription
from rest_framework.exceptions import PermissionDenied
from apps.dashboard.permissions import IsDashboardAdmin
class FootballAcademyListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = FootballAcademySerializer

    def get_queryset(self):
        return (
            FootballAcademy.objects
            .filter(status=FootballAcademy.Status.ACTIVE)
            .prefetch_related("images")
            .order_by("id")
        )


class FootballAcademyDetailView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = FootballAcademySerializer

    def get_queryset(self):
        return (
            FootballAcademy.objects
            .filter(status=FootballAcademy.Status.ACTIVE)
            .prefetch_related("images")
        )


class FootballSubscriptionCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = FootballSubscriptionCreateInputSerializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)

        subscription, created = create_football_subscription(
            user=request.user,
            academy_id=serializer.validated_data["academy"],
            month=serializer.validated_data["month"],
        )

        output = FootballSubscriptionSerializer(
            subscription,
            context={"request": request},
        )

        return Response(
            output.data,
            status=(
                status.HTTP_201_CREATED
                if created
                else status.HTTP_200_OK
            ),
        )


class MyFootballSubscriptionsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FootballSubscriptionSerializer

    def get_queryset(self):
        return (
            FootballSubscription.objects
            .filter(user=self.request.user)
            .select_related("academy")
            .order_by("-created_at")
        )




class DashboardFootballSubscriptionsView(generics.ListAPIView):
    permission_classes = [IsDashboardAdmin]
    serializer_class = DashboardFootballSubscriptionSerializer
    pagination_class = FootballAcademyDashboardPagination

    def get_queryset(self):
        queryset = (
            FootballSubscription.objects
            .select_related("user", "academy")
            .order_by("-created_at", "-pk")
        )

        academy_id = self.request.query_params.get("academy")
        status_value = self.request.query_params.get("status")
        month = self.request.query_params.get("month")


        if academy_id:
            if not academy_id.isdecimal() or int(academy_id) < 1:
                raise ValidationError({
                    "academy": "Akademiya ID noto'g'ri."
                })

            queryset = queryset.filter(
                academy_id=int(academy_id)
            )

        if status_value:
            if status_value not in FootballSubscription.Status.values:
                raise ValidationError({
                    "status": "Noto'g'ri obuna holati."
                })

            queryset = queryset.filter(
                status=status_value
            )

        if month:
            from datetime import date

            try:
                parsed_month = date.fromisoformat(month)
            except ValueError:
                raise ValidationError({
                    "month": "Sana YYYY-MM-01 formatida bo'lishi kerak."
                })

            if parsed_month.day != 1:
                raise ValidationError({
                    "month": "Oyning birinchi sanasini kiriting."
                })

            queryset = queryset.filter(
                month=parsed_month
            )

        return queryset

class DashboardFootballSubscriptionDetailView(
    generics.RetrieveAPIView
):
    permission_classes = [IsDashboardAdmin]
    serializer_class = DashboardFootballSubscriptionSerializer

    queryset = (
        FootballSubscription.objects
        .select_related("user", "academy")
    )