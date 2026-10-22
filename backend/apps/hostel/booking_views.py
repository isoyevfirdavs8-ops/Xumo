
import uuid

from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .booking_serializers import (
    HostelBookingCreateSerializer,
    HostelReservationSerializer,
)
from .models import HostelReservation
from .services import create_hostel_reservation


class HostelBookingCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = HostelBookingCreateSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        # Har bir yangi bron uchun UUID kalit.
        # Takroriy so'rovda aynan shu kalit yuboriladi.
        raw_key = request.headers.get("Idempotency-Key")

        if not raw_key:
            raise ValidationError({
                "idempotency_key": (
                    "Idempotency-Key header majburiy."
                )
            })

        try:
            idempotency_key = uuid.UUID(raw_key)
        except (ValueError, AttributeError, TypeError):
            raise ValidationError({
                "idempotency_key": (
                    "Idempotency-Key yaroqli UUID bo'lishi kerak."
                )
            })

        reservation = create_hostel_reservation(
            user=request.user,
            idempotency_key=idempotency_key,
            **serializer.validated_data,
        )

        reservation = (
            HostelReservation.objects
            .prefetch_related("bookings__room")
            .get(pk=reservation.pk)
        )

        return Response(
            HostelReservationSerializer(
                reservation,
                context={"request": request},
            ).data,
            status=status.HTTP_201_CREATED,
        )


class MyHostelReservationsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = HostelReservationSerializer

    def get_queryset(self):
        return (
            HostelReservation.objects
            .filter(user=self.request.user)
            .prefetch_related("bookings__room")
            .order_by("-created_at")
        )


class HostelReservationDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = HostelReservationSerializer

    def get_queryset(self):
        return (
            HostelReservation.objects
            .filter(user=self.request.user)
            .prefetch_related("bookings__room")
        )
