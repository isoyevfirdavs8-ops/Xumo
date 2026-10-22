
from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action


from .models import FootballField, FieldPriceHistory
from .permissions import IsFootballAdminOrReadOnly
from .serializers import FootballFieldSerializer

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import HourlyBooking, FieldClosure
from .serializers import (
    HourlyBookingSerializer,
    CreateHourlyBookingSerializer,
)
from .booking_services import (
    create_hourly_booking,
    expire_old_holds,
)

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import FootballFieldImage
from .serializers import FootballFieldImageSerializer


class FootballFieldViewSet(viewsets.ModelViewSet):
    serializer_class = FootballFieldSerializer
    permission_classes = [IsFootballAdminOrReadOnly]
    http_method_names = [
        "get",
        "post",
        "put",
        "patch",
        "head",
        "options",
    ]


    def get_queryset(self):
        queryset = FootballField.objects.prefetch_related(
            "images"
        ).order_by("id")

        user = self.request.user

        is_admin = (
            user.is_authenticated
            and (
                user.is_superuser
                or (
                    user.is_staff
                    and getattr(user, "role", None) == "admin"
                )
            )
        )

        if is_admin:
            return queryset

        return queryset.filter(status="active")


    @transaction.atomic
    def perform_update(self, serializer):
        instance = FootballField.objects.select_for_update().get(
            pk=serializer.instance.pk
        )

        old_price = instance.hourly_price

        serializer.instance = instance
        updated = serializer.save()

        if old_price != updated.hourly_price:
            FieldPriceHistory.objects.create(
                field=updated,
                old_price=old_price,
                new_price=updated.hourly_price,
                changed_by=self.request.user,
            )
    @action(
        detail=True,
        methods=["post"],
        url_path="images",
        parser_classes=[MultiPartParser, FormParser],
    )
    def upload_image(self, request, pk=None):
        field = self.get_object()

        if not self._is_admin(request.user):
            return Response(
                {"detail": "Ruxsat berilmagan."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = FootballFieldImageSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        image = serializer.save(field=field)

        return Response(
            FootballFieldImageSerializer(
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
    def delete_image(self, request, pk=None, image_id=None):
        field = self.get_object()

        if not self._is_admin(request.user):
            return Response(
                {"detail": "Ruxsat berilmagan."},
                status=status.HTTP_403_FORBIDDEN,
            )

        image = get_object_or_404(
            FootballFieldImage,
            pk=image_id,
            field=field,
        )

        image.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=["post"],
        url_path="archive",
    )
    def archive(self, request, pk=None):
        field = self.get_object()

        if not (
            request.user.is_authenticated
            and (
                request.user.is_superuser
                or (
                    request.user.is_staff
                    and getattr(request.user, "role", None) == "admin"
                )
            )
        ):
            return Response(
                {"detail": "Ruxsat berilmagan."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Kelajakda bu yerda faol bronlarni ham
        # tekshiramiz.
        field.status = FootballField.Status.ARCHIVED
        field.save(update_fields=["status", "updated_at"])

        return Response(
            {"detail": "Stadion arxivlandi."}
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="activate",
    )
    def activate(self, request, pk=None):
        field = self.get_object()

        if field.status != "archived":
            return Response(
                {
                    "detail": "Faqat arxivlangan stadionni qayta faollashtirish mumkin."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        field.status = "active"
        field.save(update_fields=["status", "updated_at"])

        return Response(
            {
                "detail": "Stadion muvaffaqiyatli faollashtirildi.",
                "id": field.id,
                "status": field.status,
            },
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def _is_admin(user):
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




class CreateHourlyBookingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateHourlyBookingSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        try:
            booking = create_hourly_booking(
                user=request.user,
                **serializer.validated_data,
            )
        except DjangoValidationError as exc:
            messages = (
                exc.messages
                if hasattr(exc, "messages")
                else [str(exc)]
            )

            conflict = any(
                "band qilingan" in message
                for message in messages
            )

            return Response(
                {"detail": messages},
                status=(
                    status.HTTP_409_CONFLICT
                    if conflict
                    else status.HTTP_400_BAD_REQUEST
                ),
            )

        return Response(
            HourlyBookingSerializer(booking).data,
            status=status.HTTP_201_CREATED,
        )


class MyHourlyBookingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        expire_old_holds()

        bookings = HourlyBooking.objects.filter(
            user=request.user
        ).select_related("field")

        serializer = HourlyBookingSerializer(
            bookings,
            many=True,
        )

        return Response(serializer.data)


class FootballAvailabilityView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        field_id = request.query_params.get("field_id")
        date_str = request.query_params.get("date")

        if not field_id or not date_str:
            return Response(
                {"detail": "field_id va date majburiy."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            field = FootballField.objects.get(
                pk=field_id,
                status=FootballField.Status.ACTIVE,
            )

            selected_date = datetime.strptime(
                date_str,
                "%Y-%m-%d",
            ).date()

        except (FootballField.DoesNotExist, ValueError):
            return Response(
                {"detail": "Stadion yoki sana noto'g'ri."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tz = ZoneInfo("Asia/Tashkent")

        day_start = datetime.combine(
            selected_date,
            datetime.min.time(),
            tzinfo=tz,
        )

        day_end = day_start + timedelta(days=1)

        expire_old_holds(field_id=field.id)

        bookings = list(
            HourlyBooking.objects.filter(
                field=field,
                status__in=[
                    HourlyBooking.Status.PENDING_PAYMENT,
                    HourlyBooking.Status.CONFIRMED,
                ],
                start_at__lt=day_end,
                end_at__gt=day_start,
            ).values("start_at", "end_at")
        )

        closures = list(
            FieldClosure.objects.filter(
                field=field,
                start_at__lt=day_end,
                end_at__gt=day_start,
            ).values("start_at", "end_at")
        )

        slots = []

        for hour in range(24):
            slot_start = day_start + timedelta(hours=hour)
            slot_end = slot_start + timedelta(hours=1)

            if 16 <= hour < 20:
                slot_status = "closed"

            elif any(
                item["start_at"] < slot_end
                and item["end_at"] > slot_start
                for item in closures
            ):
                slot_status = "closed"

            elif any(
                item["start_at"] < slot_end
                and item["end_at"] > slot_start
                for item in bookings
            ):
                slot_status = "booked"

            elif slot_start <= timezone.now():
                slot_status = "past"

            else:
                slot_status = "available"

            slots.append({
                "start": slot_start.isoformat(),
                "end": slot_end.isoformat(),
                "status": slot_status,
            })

        return Response({
            "field_id": field.id,
            "field_name": field.name,
            "date": selected_date.isoformat(),
            "hourly_price": str(field.hourly_price),
            "slots": slots,
        })