from rest_framework import serializers

from .models import (
    FootballAcademy,
    FootballAcademyImage,
    FootballSubscription,
)


class FootballAcademyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = FootballAcademyImage
        fields = [
            "id",
            "image",
            "is_primary",
            "sort_order",
        ]


class FootballAcademySerializer(serializers.ModelSerializer):
    images = FootballAcademyImageSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = FootballAcademy
        fields = [
            "id",
            "name",
            "description",
            "monthly_price",
            "status",
            "images",
        ]


class FootballSubscriptionSerializer(serializers.ModelSerializer):
    academy_name = serializers.CharField(
        source="academy.name",
        read_only=True,
    )

    class Meta:
        model = FootballSubscription
        fields = [
            "id",
            "academy",
            "academy_name",
            "month",
            "price_snapshot",
            "status",
            "payment_expires_at",
            "paid_at",
            "created_at",
        ]

        read_only_fields = fields

class FootballSubscriptionCreateInputSerializer(serializers.Serializer):
    academy = serializers.IntegerField(min_value=1)
    month = serializers.DateField()

class DashboardFootballSubscriptionSerializer(
    FootballSubscriptionSerializer
):
    user_id = serializers.IntegerField(
        source="user.pk",
        read_only=True,
    )

    phone_number = serializers.CharField(
        source="user.phone_number",
        read_only=True,
    )

    class Meta(FootballSubscriptionSerializer.Meta):
        fields = (
            FootballSubscriptionSerializer.Meta.fields
            + ["user_id", "phone_number"]
        )


class DashboardFootballAcademyWriteSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = FootballAcademy
        fields = [
            "id",
            "name",
            "description",
            "monthly_price",
            "status",
        ]
        read_only_fields = ["id"]

    def validate_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Akademiya nomi bo'sh bo'lishi mumkin emas."
            )

        return value


class DashboardFootballAcademyImageUploadSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = FootballAcademyImage
        fields = ["image"]

    def validate_image(self, value):
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError(
                "Rasm hajmi 5 MB dan oshmasligi kerak."
            )

        allowed_formats = {"JPEG", "PNG", "WEBP"}

        try:
            from PIL import Image

            value.seek(0)
            with Image.open(value) as image:
                image.verify()

            value.seek(0)

            with Image.open(value) as image:
                if image.format not in allowed_formats:
                    raise serializers.ValidationError(
                        "Faqat JPEG, PNG va WEBP rasmlar qabul qilinadi."
                    )

            value.seek(0)
        except serializers.ValidationError:
            raise
        except (OSError, ValueError):
            raise serializers.ValidationError(
                "Rasm fayli noto'g'ri yoki shikastlangan."
            )

        return value