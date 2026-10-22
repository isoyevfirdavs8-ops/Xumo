
from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.parsers import (
    JSONParser,
    MultiPartParser,
    FormParser,
)
from rest_framework.response import Response

from .models import BoxingAcademy, BoxingAcademyImage
from .permissions import (
    IsBoxingAdminOrReadOnly,
    is_boxing_admin,
)
from .serializers import (
    BoxingAcademySerializer,
    BoxingAcademyImageSerializer,
)


class BoxingAcademyViewSet(viewsets.ModelViewSet):
    serializer_class = BoxingAcademySerializer
    permission_classes = [IsBoxingAdminOrReadOnly]

    http_method_names = [
        "get",
        "post",
        "put",
        "patch",
        "delete",
        "head",
        "options",
    ]

    def get_queryset(self):
        queryset = (
            BoxingAcademy.objects
            .prefetch_related("images")
            .order_by("id")
        )

        if is_boxing_admin(self.request.user):
            return queryset

        return queryset.filter(
            status=BoxingAcademy.Status.ACTIVE
        )

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed(
            "DELETE",
            detail=(
                "Akademiyani o'chirish mumkin emas. "
                "Arxivlashdan foydalaning."
            ),
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="archive",
    )
    def archive(self, request, pk=None):
        academy = self.get_object()

        if academy.status == BoxingAcademy.Status.ARCHIVED:
            return Response(
                {"detail": "Akademiya allaqachon arxivlangan."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        academy.status = BoxingAcademy.Status.ARCHIVED
        academy.save(
            update_fields=["status", "updated_at"]
        )

        return Response({
            "detail": "Akademiya arxivlandi.",
            "status": academy.status,
        })

    @action(
        detail=True,
        methods=["post"],
        url_path="activate",
    )
    def activate(self, request, pk=None):
        academy = self.get_object()

        if academy.status != BoxingAcademy.Status.ARCHIVED:
            return Response(
                {
                    "detail": (
                        "Faqat arxivlangan akademiyani "
                        "qayta faollashtirish mumkin."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        academy.status = BoxingAcademy.Status.ACTIVE
        academy.save(
            update_fields=["status", "updated_at"]
        )

        return Response({
            "detail": "Akademiya qayta faollashtirildi.",
            "status": academy.status,
        })

    @action(
        detail=True,
        methods=["post"],
        url_path="images",
        parser_classes=[MultiPartParser, FormParser],
    )
    @transaction.atomic
    def upload_image(self, request, pk=None):
        academy = BoxingAcademy.objects.select_for_update().get(
            pk=self.get_object().pk
        )

        serializer = BoxingAcademyImageSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        # Faqat bitta asosiy rasm saqlaymiz.
        has_primary = BoxingAcademyImage.objects.filter(
            academy=academy,
            is_primary=True,
        ).exists()

        image = serializer.save(
            academy=academy,
            is_primary=not has_primary,
        )

        if image.is_primary:
            BoxingAcademyImage.objects.filter(
                academy=academy
            ).exclude(pk=image.pk).update(is_primary=False)

        return Response(
            BoxingAcademyImageSerializer(
                image,
                context={"request": request},
            ).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path=r"images/(?P<image_id>[0-9]+)/primary",
    )
    @transaction.atomic
    def set_primary_image(self, request, pk=None, image_id=None):
        academy = BoxingAcademy.objects.select_for_update().get(
            pk=self.get_object().pk
        )

        image = get_object_or_404(
            BoxingAcademyImage,
            pk=image_id,
            academy=academy,
        )

        BoxingAcademyImage.objects.filter(
            academy=academy
        ).update(is_primary=False)

        image.is_primary = True
        image.save(update_fields=["is_primary"])

        return Response({
            "detail": "Asosiy rasm o'zgartirildi.",
            "image_id": image.id,
        })

    @action(
        detail=True,
        methods=["delete"],
        url_path=r"images/(?P<image_id>[0-9]+)",
    )
    @transaction.atomic
    def delete_image(self, request, pk=None, image_id=None):
        academy = BoxingAcademy.objects.select_for_update().get(
            pk=self.get_object().pk
        )

        image = get_object_or_404(
            BoxingAcademyImage,
            pk=image_id,
            academy=academy,
        )

        was_primary = image.is_primary
        image.delete()

        if was_primary:
            next_image = (
                BoxingAcademyImage.objects
                .filter(academy=academy)
                .order_by("sort_order", "id")
                .first()
            )

            if next_image:
                next_image.is_primary = True
                next_image.save(
                    update_fields=["is_primary"]
                )

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )

