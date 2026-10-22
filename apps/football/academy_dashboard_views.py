from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.dashboard.permissions import IsDashboardAdmin

from .models import FootballAcademy, FootballAcademyImage
from .academy_serializers import (
    FootballAcademySerializer,
    DashboardFootballAcademyWriteSerializer,
    DashboardFootballAcademyImageUploadSerializer,
)


class DashboardFootballAcademyListCreateView(
    generics.ListCreateAPIView
):
    permission_classes = [IsDashboardAdmin]
    pagination_class = None

    def get_queryset(self):
        return (
            FootballAcademy.objects
            .prefetch_related("images")
            .order_by("id")
        )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return DashboardFootballAcademyWriteSerializer

        return FootballAcademySerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        academy = serializer.save()

        output = FootballAcademySerializer(
            academy,
            context={"request": request},
        )

        return Response(
            output.data,
            status=status.HTTP_201_CREATED,
        )


class DashboardFootballAcademyDetailView(
    generics.RetrieveUpdateAPIView
):
    permission_classes = [IsDashboardAdmin]
    http_method_names = ["get", "patch", "head", "options"]

    def get_queryset(self):
        return (
            FootballAcademy.objects
            .prefetch_related("images")
        )

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return DashboardFootballAcademyWriteSerializer

        return FootballAcademySerializer


class DashboardFootballAcademyStatusView(APIView):
    permission_classes = [IsDashboardAdmin]

    def post(self, request, pk, action):
        if action not in ("archive", "activate"):
            return Response(
                {"detail": "Noto'g'ri amal."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            academy = get_object_or_404(
                FootballAcademy.objects.select_for_update(),
                pk=pk,
            )

            academy.status = (
                FootballAcademy.Status.ARCHIVED
                if action == "archive"
                else FootballAcademy.Status.ACTIVE
            )

            academy.save(
                update_fields=["status", "updated_at"]
            )

        return Response({
            "detail": "Akademiya holati yangilandi.",
            "status": academy.status,
        })


class DashboardFootballAcademyImageUploadView(APIView):
    permission_classes = [IsDashboardAdmin]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, pk):
        serializer = DashboardFootballAcademyImageUploadSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            academy = get_object_or_404(
                FootballAcademy.objects.select_for_update(),
                pk=pk,
            )

            has_images = FootballAcademyImage.objects.filter(
                academy=academy
            ).exists()

            image = FootballAcademyImage.objects.create(
                academy=academy,
                image=serializer.validated_data["image"],
                is_primary=not has_images,
            )

        return Response(
            FootballAcademySerializer(
                academy,
                context={"request": request},
            ).data,
            status=status.HTTP_201_CREATED,
        )


class DashboardFootballAcademyImageDeleteView(APIView):
    permission_classes = [IsDashboardAdmin]

    def delete(self, request, pk, image_id):
        with transaction.atomic():
            academy = get_object_or_404(
                FootballAcademy.objects.select_for_update(),
                pk=pk,
            )

            image = get_object_or_404(
                FootballAcademyImage,
                pk=image_id,
                academy=academy,
            )

            was_primary = image.is_primary
            image.delete()

            if was_primary:
                next_image = (
                    FootballAcademyImage.objects
                    .filter(academy=academy)
                    .order_by("sort_order", "id")
                    .first()
                )

                if next_image:
                    next_image.is_primary = True
                    next_image.save(
                        update_fields=["is_primary"]
                    )

        return Response(status=status.HTTP_204_NO_CONTENT)


class DashboardFootballAcademyImagePrimaryView(APIView):
    permission_classes = [IsDashboardAdmin]

    def post(self, request, pk, image_id):
        with transaction.atomic():
            academy = get_object_or_404(
                FootballAcademy.objects.select_for_update(),
                pk=pk,
            )

            image = get_object_or_404(
                FootballAcademyImage,
                pk=image_id,
                academy=academy,
            )

            FootballAcademyImage.objects.filter(
                academy=academy,
                is_primary=True,
            ).update(is_primary=False)

            image.is_primary = True
            image.save(update_fields=["is_primary"])

        return Response({
            "detail": "Asosiy rasm yangilandi."
        })