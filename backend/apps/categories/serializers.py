
from PIL import Image

from .models import Category
from rest_framework import serializers
from .models import SubCategory

class CategorySerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False)

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "image",
            "is_active",
            "sort_order",
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

        if len(value) < 2:
            raise serializers.ValidationError(
                "Kategoriya nomi kamida 2 ta belgidan iborat bo‘lishi kerak."
            )

        return value

    def validate_image(self, value):
        if not value:
            return value

        max_size = 5 * 1024 * 1024

        if value.size > max_size:
            raise serializers.ValidationError(
                "Rasm hajmi 5 MB dan oshmasligi kerak."
            )

        allowed_formats = {"JPEG", "PNG", "WEBP"}

        try:
            image = Image.open(value)
            image.verify()

            if image.format not in allowed_formats:
                raise serializers.ValidationError(
                    "Faqat JPG, PNG yoki WEBP rasmlar qabul qilinadi."
                )

        except (OSError, ValueError):
            raise serializers.ValidationError(
                "Yuklangan fayl haqiqiy rasm emas."
            )
        finally:
            value.seek(0)

        return value





class SubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategory
        fields = [
            "id",
            "category",
            "name",
            "slug",
            "description",
            "image",
            "is_active",
            "sort_order",
        ]
        read_only_fields = ["id"]

    def validate_name(self, value):
        value = value.strip()

        if len(value) < 2:
            raise serializers.ValidationError(
                "Nom kamida 2 ta belgidan iborat bo‘lsin."
            )

        return value