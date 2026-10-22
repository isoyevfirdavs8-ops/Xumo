
from rest_framework import serializers

from .models import (
    FootballField,
    FootballFieldImage,
    FieldPriceHistory,
)


class FootballFieldImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = FootballFieldImage
        fields = [
            "id",
            "image",
            "is_primary",
            "sort_order",
        ]
        read_only_fields = ["id"]

    def validate_image(self, image):
        allowed_formats = {"JPEG", "PNG", "WEBP"}

        from PIL import Image
        from django.core.exceptions import ValidationError

        try:
            image.seek(0)
            picture = Image.open(image)
            picture.verify()
            image.seek(0)
        except Exception:
            raise serializers.ValidationError(
                "Yaroqli rasm yuklang."
            )

        if picture.format not in allowed_formats:
            raise serializers.ValidationError(
                "Faqat JPG, PNG yoki WEBP mumkin."
            )

        if image.size > 5 * 1024 * 1024:
            raise serializers.ValidationError(
                "Rasm hajmi 5 MB dan oshmasligi kerak."
            )

        return image


class FieldPriceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FieldPriceHistory
        fields = [
            "id",
            "old_price",
            "new_price",
            "changed_at",
        ]


class FootballFieldSerializer(serializers.ModelSerializer):
    images = FootballFieldImageSerializer(
        many=True,
        read_only=True,
    )

    field_type_display = serializers.CharField(
        source="get_field_type_display",
        read_only=True,
    )

    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )

    class Meta:
        model = FootballField

        fields = [
            "id",
            "name",
            "field_type",
            "field_type_display",
            "description",
            "hourly_price",
            "capacity",
            "length_m",
            "width_m",
            "has_lighting",
            "has_changing_room",
            "status",
            "status_display",
            "images",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]

    def validate_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Stadion nomi bo'sh bo'lishi mumkin emas."
            )

        return value


from rest_framework import serializers

from .models import HourlyBooking
from .booking_services import validate_booking_time


class HourlyBookingSerializer(serializers.ModelSerializer):
    field_name = serializers.CharField(
        source="field.name",
        read_only=True,
    )

    class Meta:
        model = HourlyBooking

        fields = [
            "id",
            "field",
            "field_name",
            "start_at",
            "end_at",
            "price_snapshot",
            "status",
            "hold_expires_at",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "field_name",
            "price_snapshot",
            "status",
            "hold_expires_at",
            "created_at",
        ]


class CreateHourlyBookingSerializer(serializers.Serializer):
    field_id = serializers.IntegerField(min_value=1)

    start_at = serializers.DateTimeField()
    end_at = serializers.DateTimeField()

    def validate(self, attrs):
        validate_booking_time(
            attrs["start_at"],
            attrs["end_at"],
        )

        return attrs