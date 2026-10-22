import re

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()

PHONE_PATTERN = re.compile(r"^\+998\d{9}$")


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
    )

    class Meta:
        model = User
        fields = (
            "id",
            "phone_number",
            "full_name",
            "password",
        )
        read_only_fields = ("id",)

    def validate_phone_number(self, value):
        if not PHONE_PATTERN.fullmatch(value):
            raise serializers.ValidationError(
                "Telefon raqami +998XXXXXXXXX formatida bo'lishi kerak."
            )
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "phone_number",
            "full_name",
            "email",
            "role",
            "is_phone_verified",
        )
        read_only_fields = fields



class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("full_name", "email")

    def validate_full_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Ism-familiya bo'sh bo'lishi mumkin emas."
            )

        if len(value) > 150:
            raise serializers.ValidationError(
                "Ism-familiya juda uzun."
            )

        return value
