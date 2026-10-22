
from django.utils import timezone

from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import (
    MultiPartParser,
    FormParser,
    JSONParser,
)
from django.db.models.deletion import ProtectedError
from rest_framework.response import Response
from rest_framework import status

from apps.dashboard.permissions import IsDashboardAdmin

from .models import Competition
from .serializers import CompetitionSerializer


class PublicCompetitionListView(generics.ListAPIView):
    serializer_class = CompetitionSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        return Competition.objects.filter(
            is_active=True,
            start_time__gt=timezone.now(),
        ).order_by("start_time", "id")


class PublicCompetitionDetailView(generics.RetrieveAPIView):
    serializer_class = CompetitionSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Competition.objects.filter(
            is_active=True,
            start_time__gt=timezone.now(),
        )


class DashboardCompetitionListCreateView(
    generics.ListCreateAPIView
):
    queryset = Competition.objects.all().order_by(
        "-created_at"
    )

    serializer_class = CompetitionSerializer

    permission_classes = [
        IsAuthenticated,
        IsDashboardAdmin,
    ]

    parser_classes = [
        MultiPartParser,
        FormParser,
        JSONParser,
    ]


class DashboardCompetitionDetailView(
    generics.RetrieveUpdateDestroyAPIView
):
    queryset = Competition.objects.all()

    serializer_class = CompetitionSerializer

    permission_classes = [
        IsAuthenticated,
        IsDashboardAdmin,
    ]

    parser_classes = [
        MultiPartParser,
        FormParser,
        JSONParser,
    ]

    def destroy(self, request, *args, **kwargs):
        competition = self.get_object()

        if competition.ticket_orders.exists():
            return Response(
                {
                    "detail": (
                        "Bu musobaqaga chipta buyurtmalari "
                        "bog‘langan. Uni o‘chirish o‘rniga "
                        "nofaol holatga o‘tkazing."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        try:
            return super().destroy(request, *args, **kwargs)

        except ProtectedError:
            return Response(
                {
                    "detail": (
                        "Musobaqaga bog‘langan ma’lumotlar "
                        "mavjud. O‘chirish mumkin emas."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )


