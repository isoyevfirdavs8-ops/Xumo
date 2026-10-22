
from PIL import Image, UnidentifiedImageError
from rest_framework import serializers

from .models import TennisCourt, TennisCourtImage
from datetime import date

from django.utils import timezone

from .models import TennisSubscription

class TennisCourtImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=True)

    class Meta:
        model = TennisCourtImage
        fields = (
            "id",
            "image",
            "is_primary",
            "sort_order",
            "created_at",
        )
        read_only_fields = ("id", "created_at")

    def validate_image(self, value):
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError(
                "Rasm 5 MB dan oshmasligi kerak."
            )

        try:
            value.seek(0)
            with Image.open(value) as img:
                image_format = img.format
                img.verify()
            value.seek(0)
        except (UnidentifiedImageError, OSError, ValueError):
            raise serializers.ValidationError(
                "Yaroqli rasm yuklang."
            )

        if image_format not in {"JPEG", "PNG", "WEBP"}:
            raise serializers.ValidationError(
                "Faqat JPG, PNG va WEBP rasmlarga ruxsat."
            )

        return value


class TennisCourtSerializer(serializers.ModelSerializer):
    images = TennisCourtImageSerializer(
        many=True,
        read_only=True,
    )

    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )

    class Meta:
        model = TennisCourt
        fields = (
            "id",
            "name",
            "description",
            "monthly_price",
            "status",
            "status_display",
            "images",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "images",
            "created_at",
            "updated_at",
        )

    def validate_monthly_price(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Oylik narx 0 dan katta bo'lishi kerak."
            )
        return value






class TennisSubscriptionCreateSerializer(
    serializers.Serializer
):
    court_id = serializers.PrimaryKeyRelatedField(
        queryset=TennisCourt.objects.filter(
            status=TennisCourt.Status.ACTIVE
        ),
        source="court",
    )

    month = serializers.DateField(
        input_formats=["%Y-%m-%d"],
    )

    def validate_month(self, value):
        today = timezone.localdate()
        current_month = date(today.year, today.month, 1)

        if value.day != 1:
            raise serializers.ValidationError(
                "Oyning birinchi kunini yuboring."
            )

        if value < current_month:
            raise serializers.ValidationError(
                "O'tgan oyga obuna bo'lish mumkin emas."
            )

        return value


class TennisSubscriptionSerializer(
    serializers.ModelSerializer
):
    court_name = serializers.CharField(
        source="court.name",
        read_only=True,
    )

    class Meta:
        model = TennisSubscription
        fields = (
            "id",
            "court",
            "court_name",
            "month",
            "price_snapshot",
            "status",
            "payment_expires_at",
            "paid_at",
            "created_at",
        )
        read_only_fields = fields
