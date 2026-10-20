from rest_framework import serializers

from .models import FooterSettings


class FooterSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = FooterSettings
        fields = [
            "id",
            "brand_name",
            "description",
            "phone",
            "phone_2",
            "phone_3",
            "phone_4",
            "email",
            "address",
            "working_hours",
            "telegram_url",
            "facebook_url",
            "instagram_url",
            "copyright_text",
            "updated_at",
        ]
        read_only_fields = ["id", "updated_at"]

    def validate_brand_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Brend nomi bo‘sh bo‘lishi mumkin emas."
            )

        return value