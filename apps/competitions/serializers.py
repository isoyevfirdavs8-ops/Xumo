
from django.utils import timezone
from PIL import Image
from rest_framework import serializers

from .models import Competition


class CompetitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Competition

        fields = [
            "id",
            "name",
            "description",
            "banner",
            "start_time",
            "min_age",
            "max_age",
            "price",
            "capacity",
            "is_active",
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

        if len(value) < 3:
            raise serializers.ValidationError(
                "Musobaqa nomi kamida 3 ta belgidan iborat bo‘lishi kerak."
            )

        return value

    def validate_banner(self, value):
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError(
                "Banner hajmi 5 MB dan oshmasligi kerak."
            )

        try:
            image = Image.open(value)
            image.verify()

            if image.format not in {"JPEG", "PNG", "WEBP"}:
                raise serializers.ValidationError(
                    "Faqat JPG, PNG yoki WEBP rasm yuklang."
                )

        except (OSError, ValueError):
            raise serializers.ValidationError(
                "Yuklangan fayl haqiqiy rasm emas."
            )

        finally:
            value.seek(0)

        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)

        # Yosh chegaralarini tekshirish
        min_age = attrs.get(
            "min_age",
            getattr(self.instance, "min_age", None)
        )

        max_age = attrs.get(
            "max_age",
            getattr(self.instance, "max_age", None)
        )

        if (
            min_age is not None
            and max_age is not None
            and min_age > max_age
        ):
            raise serializers.ValidationError({
                "max_age": (
                    "Maksimal yosh minimal yoshdan "
                    "kichik bo‘lmasligi kerak."
                )
            })

        # Musobaqa vaqtini tekshirish
        if (
            "start_time" in attrs
            and attrs["start_time"] <= timezone.now()
        ):
            raise serializers.ValidationError({
                "start_time": (
                    "Musobaqa boshlanish vaqti "
                    "kelajakda bo‘lishi kerak."
                )
            })

        return attrs
