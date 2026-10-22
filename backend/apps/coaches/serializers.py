
from PIL import Image
from rest_framework import serializers

from apps.categories.models import Category
from .models import Coach


class CoachSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(
        source="category.name",
        read_only=True,
    )

    class Meta:
        model = Coach
        fields = [
            "id",
            "category",
            "category_name",
            "full_name",
            "specialization",
            "experience_years",
            "bio",
            "image",
            "is_active",
            "sort_order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "category_name",
            "created_at",
            "updated_at",
        ]

    def validate_full_name(self, value):
        value = value.strip()

        if len(value) < 3:
            raise serializers.ValidationError(
                "Murabbiy ismi kamida 3 ta belgidan iborat bo‘lishi kerak."
            )

        return value

    def validate_category(self, value):
        if not value.is_active:
            raise serializers.ValidationError(
                "Nofaol kategoriyaga murabbiy biriktirib bo‘lmaydi."
            )

        return value

    def validate_image(self, value):
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError(
                "Rasm hajmi 5 MB dan oshmasligi kerak."
            )

        try:
            image = Image.open(value)
            image.verify()

            if image.format not in {"JPEG", "PNG", "WEBP"}:
                raise serializers.ValidationError(
                    "Faqat JPG, PNG yoki WEBP formatlari qabul qilinadi."
                )
        except (OSError, ValueError):
            raise serializers.ValidationError(
                "Yuklangan fayl haqiqiy rasm emas."
            )
        finally:
            value.seek(0)

        return value
