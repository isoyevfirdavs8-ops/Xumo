
from django.utils import timezone
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import HostelBooking, HostelRoom
from .serializers import HostelRoomSerializer


class HostelAvailabilityQuerySerializer(serializers.Serializer):
    check_in = serializers.DateField()
    check_out = serializers.DateField()
    capacity = serializers.ChoiceField(
        choices=[2, 3, 4],
        required=False,
    )

    def validate(self, attrs):
        check_in = attrs["check_in"]
        check_out = attrs["check_out"]

        if check_in < timezone.localdate():
            raise serializers.ValidationError({
                "check_in": "O'tgan sanaga bron qilish mumkin emas."
            })

        if check_out <= check_in:
            raise serializers.ValidationError({
                "check_out": "Ketish sanasi kelish sanasidan keyin bo'lishi kerak."
            })

        return attrs


class HostelAvailabilityView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        serializer = HostelAvailabilityQuerySerializer(
            data=request.query_params
        )
        serializer.is_valid(raise_exception=True)

        check_in = serializer.validated_data["check_in"]
        check_out = serializer.validated_data["check_out"]
        capacity = serializer.validated_data.get("capacity")

        # Faol bronlar tanlangan sanalar bilan kesishadimi?
        occupied_room_ids = HostelBooking.objects.filter(
            status__in=[
                HostelBooking.Status.PENDING_PAYMENT,
                HostelBooking.Status.PAID,
            ],
            stay_period__overlap=(check_in, check_out),
        ).values("room_id")

        rooms = HostelRoom.objects.filter(
            status=HostelRoom.Status.ACTIVE
        ).prefetch_related("images")

        if capacity is not None:
            rooms = rooms.filter(capacity=capacity)

        available_rooms = rooms.exclude(
            id__in=occupied_room_ids
        )

        capacities = [capacity] if capacity is not None else [2, 3, 4]

        summary = []

        for room_capacity in capacities:
            total = rooms.filter(
                capacity=room_capacity
            ).count()

            available = available_rooms.filter(
                capacity=room_capacity
            ).count()

            summary.append({
                "capacity": room_capacity,
                "total_rooms": total,
                "occupied_rooms": total - available,
                "available_rooms": available,
            })

        return Response({
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "nights": (check_out - check_in).days,
            "summary": summary,
            "rooms": HostelRoomSerializer(
                available_rooms,
                many=True,
                context={"request": request},
            ).data,
        })
