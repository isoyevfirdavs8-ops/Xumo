
from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.exceptions import MethodNotAllowed
from .models import TennisCourt, TennisCourtImage
from .permissions import IsTennisAdminOrReadOnly
from .serializers import (
    TennisCourtSerializer,
    TennisCourtImageSerializer,
)

from datetime import timedelta

from django.db import IntegrityError
from django.utils import timezone

from rest_framework.permissions import IsAuthenticated

from .models import TennisSubscription
from .serializers import (
    TennisSubscriptionCreateSerializer,
    TennisSubscriptionSerializer,
)


def is_tennis_admin(user):
    return bool(
        user.is_authenticated
        and (
            user.is_superuser
            or (
                user.is_staff
                and getattr(user, "role", None) == "admin"
            )
        )
    )


class TennisCourtViewSet(viewsets.ModelViewSet):
    serializer_class = TennisCourtSerializer
    permission_classes = [IsTennisAdminOrReadOnly]

    http_method_names = [
        "get", "post", "put", "patch","delete",
        "head", "options",
    ]
    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed(
            "DELETE",
            detail="Tennis kortini o'chirish mumkin emas. Arxivlashdan foydalaning.",
        )


    def get_queryset(self):
        queryset = TennisCourt.objects.prefetch_related(
            "images"
        ).order_by("id")

        if is_tennis_admin(self.request.user):
            return queryset

        return queryset.filter(
            status=TennisCourt.Status.ACTIVE
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="archive",
    )

    def archive(self, request, pk=None):
        court = self.get_object()

        if court.status == TennisCourt.Status.ARCHIVED:
            return Response(
                {"detail": "Kort allaqachon arxivlangan."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        court.status = TennisCourt.Status.ARCHIVED
        court.save(update_fields=["status", "updated_at"])

        return Response({
            "detail": "Kort arxivlandi.",
            "status": court.status,
        })

    @action(
        detail=True,
        methods=["post"],
        url_path="activate",
    )
    def activate(self, request, pk=None):
        court = self.get_object()

        if court.status != TennisCourt.Status.ARCHIVED:
            return Response(
                {
                    "detail": "Faqat arxivlangan kortni "
                              "qayta faollashtirish mumkin."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        court.status = TennisCourt.Status.ACTIVE
        court.save(update_fields=["status", "updated_at"])

        return Response({
            "detail": "Kort qayta faollashtirildi.",
            "status": court.status,
        })

    @action(
        detail=True,
        methods=["post"],
        url_path="images",
        parser_classes=[MultiPartParser, FormParser],
    )
    @transaction.atomic
    def upload_image(self, request, pk=None):
        court = self.get_object()

        serializer = TennisCourtImageSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        image = serializer.save(court=court)

        # Birinchi rasm avtomatik asosiy bo'ladi.
        if not TennisCourtImage.objects.filter(
            court=court,
            is_primary=True,
        ).exclude(pk=image.pk).exists():
            image.is_primary = True
            image.save(update_fields=["is_primary"])

        return Response(
            TennisCourtImageSerializer(
                image,
                context={"request": request},
            ).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["delete"],
        url_path=r"images/(?P<image_id>[0-9]+)",
    )
    @transaction.atomic
    def delete_image(self, request, pk=None, image_id=None):
        court = self.get_object()

        image = get_object_or_404(
            TennisCourtImage,
            pk=image_id,
            court=court,
        )

        was_primary = image.is_primary
        image.delete()

        if was_primary:
            next_image = (
                TennisCourtImage.objects
                .filter(court=court)
                .order_by("sort_order", "id")
                .first()
            )

            if next_image:
                next_image.is_primary = True
                next_image.save(update_fields=["is_primary"])

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )




class TennisSubscriptionViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    http_method_names = [
        "get", "post", "head", "options"
    ]

    def get_queryset(self):
        return (
            TennisSubscription.objects
            .filter(user=self.request.user)
            .select_related("court")
            .order_by("-created_at")
        )

    def get_serializer_class(self):
        if self.action == "create":
            return TennisSubscriptionCreateSerializer
        return TennisSubscriptionSerializer

    def list(self, request):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = TennisSubscriptionSerializer(
                page, many=True
            )
            return self.get_paginated_response(
                serializer.data
            )

        serializer = TennisSubscriptionSerializer(
            queryset, many=True
        )
        return Response(serializer.data)

    def create(self, request):
        serializer = TennisSubscriptionCreateSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        court = serializer.validated_data["court"]
        month = serializer.validated_data["month"]

        # Bir user bir kort va bir oyga faqat
        # bitta subscription yozuviga ega bo'ladi.
        try:
            with transaction.atomic():
                subscription, created = (
                    TennisSubscription.objects.get_or_create(
                        user=request.user,
                        court=court,
                        month=month,
                        defaults={
                            "price_snapshot": court.monthly_price,
                            "status": (
                                TennisSubscription.Status
                                .PENDING_PAYMENT
                            ),
                            "payment_expires_at": (
                                timezone.now()
                                + timedelta(minutes=30)
                            ),
                        },
                    )
                )
        except IntegrityError:
            # Parallel so'rovda boshqa tranzaksiya
            # shu obunani yaratgan bo'lishi mumkin.
            subscription = (
                TennisSubscription.objects.get(
                    user=request.user,
                    court=court,
                    month=month,
                )
            )
            created = False

        if not created:
            if subscription.status == (
                TennisSubscription.Status.PAID
            ):
                return Response(
                    {
                        "detail": (
                            "Siz bu kort uchun ushbu "
                            "oyga allaqachon to'lov qilgansiz."
                        ),
                        "subscription_id": subscription.id,
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            return Response(
                {
                    "detail": (
                        "Bu oy uchun obuna yozuvi mavjud. "
                        "To'lov holatini tekshiring."
                    ),
                    "subscription": (
                        TennisSubscriptionSerializer(
                            subscription
                        ).data
                    ),
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            TennisSubscriptionSerializer(
                subscription
            ).data,
            status=status.HTTP_201_CREATED,
        )
