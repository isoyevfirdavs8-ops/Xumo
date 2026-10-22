
from django.utils import timezone
from rest_framework import serializers

from .models import HostelBooking, HostelReservation


class HostelBookingCreateSerializer(serializers.Serializer):
    check_in = serializers.DateField()
    check_out = serializers.DateField()

    capacity = serializers.ChoiceField(
        choices=[2, 3, 4],
    )

    room_count = serializers.IntegerField(
        min_value=1,
        max_value=20,
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


class HostelBookedRoomSerializer(serializers.ModelSerializer):
    room_id = serializers.IntegerField(read_only=True)
    room_number = serializers.CharField(
        source="room.number",
        read_only=True,
    )
    room_name = serializers.CharField(
        source="room.name",
        read_only=True,
    )
    capacity = serializers.IntegerField(
        source="room.capacity",
        read_only=True,
    )

    class Meta:
        model = HostelBooking
        fields = [
            "id",
            "room_id",
            "room_number",
            "room_name",
            "capacity",
            "daily_price_snapshot",
            "status",
        ]


class HostelReservationSerializer(serializers.ModelSerializer):
    bookings = HostelBookedRoomSerializer(
        many=True,
        read_only=True,
    )

    nights = serializers.IntegerField(read_only=True)

    class Meta:
        model = HostelReservation
        fields = [
            "id",
            "check_in",
            "check_out",
            "nights",
            "status",
            "total_price",
            "payment_expires_at",
            "paid_at",
            "bookings",
            "created_at",
        ]
        read_only_fields = fields
    