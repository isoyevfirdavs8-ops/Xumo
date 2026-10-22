
from datetime import date
from rest_framework import serializers

from .models import BoxingSubscription, BoxingPayment


class BoxingSubscriptionCreateSerializer(serializers.Serializer):
    academy_id = serializers.IntegerField(min_value=1)
    month = serializers.DateField()

    def validate_month(self, value):
        today = date.today()
        current_month = today.replace(day=1)

        if value.day != 1:
            raise serializers.ValidationError(
                "Oy YYYY-MM-01 shaklida yuborilishi kerak."
            )

        if value < current_month:
            raise serializers.ValidationError(
                "O'tgan oy uchun obuna yaratib bo'lmaydi."
            )

        return value


class BoxingSubscriptionSerializer(serializers.ModelSerializer):
    academy_name = serializers.CharField(
        source="academy.name",
        read_only=True,
    )

    class Meta:
        model = BoxingSubscription
        fields = (
            "id",
            "academy",
            "academy_name",
            "month",
            "price_snapshot",
            "status",
            "payment_expires_at",
            "paid_at",
            "created_at",
        )
        read_only_fields = fields


class BoxingPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoxingPayment
        fields = (
            "id",
            "subscription",
            "provider",
            "amount",
            "status",
            "is_demo",
            "paid_at",
            "created_at",
        )
        read_only_fields = fields
