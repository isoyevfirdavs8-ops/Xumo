from rest_framework import serializers
from .models import Food


class FoodSerializer(serializers.ModelSerializer):
    subcategory_name = serializers.CharField(
        source="subcategory.name",
        read_only=True,
    )

    class Meta:
        model = Food
        fields = [
            "id",
            "subcategory",
            "subcategory_name",
            "name",
            "description",
            "image",
            "price",
            "stock",
            "is_active",
            "sort_order",
        ]
        read_only_fields = ["id", "subcategory_name"]