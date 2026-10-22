
from rest_framework import serializers

from .models import HostelRoom, HostelRoomImage


class HostelRoomImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = HostelRoomImage
        fields = ["id", "image", "is_primary", "created_at"]
        read_only_fields = fields


class HostelRoomSerializer(serializers.ModelSerializer):
    images = HostelRoomImageSerializer(many=True, read_only=True)

    class Meta:
        model = HostelRoom
        fields = [
            "id",
            "number",
            "name",
            "description",
            "capacity",
            "daily_price",
            "status",
            "images",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "images", "created_at", "updated_at"]

    def validate_daily_price(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Kunlik narx 0 dan katta bo'lishi kerak."
            )
        return value


class HostelRoomImageUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = HostelRoomImage
        fields = ["image", "is_primary"]
