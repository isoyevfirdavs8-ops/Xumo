
from PIL import Image, UnidentifiedImageError
from rest_framework import serializers

from .models import BoxingAcademy, BoxingAcademyImage


class BoxingAcademyImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=True)

    class Meta:
        model = BoxingAcademyImage
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
                "Rasm hajmi 5 MB dan oshmasligi kerak."
            )

        try:
            value.seek(0)
            with Image.open(value) as picture:
                image_format = picture.format
                picture.verify()
            value.seek(0)
        except (UnidentifiedImageError, OSError, ValueError):
            raise serializers.ValidationError(
                "Yaroqli rasm yuklang."
            )

        if image_format not in {"JPEG", "PNG", "WEBP"}:
            raise serializers.ValidationError(
                "Faqat JPG, PNG va WEBP rasmlar qabul qilinadi."
            )

        return value


class BoxingAcademySerializer(serializers.ModelSerializer):
    images = BoxingAcademyImageSerializer(
        many=True,
        read_only=True,
    )

    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )

    class Meta:
        model = BoxingAcademy
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
            "status_display",
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
