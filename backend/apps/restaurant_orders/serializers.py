
from rest_framework import serializers

from .models import RestaurantOrder


class CheckoutItemSerializer(serializers.Serializer):
    food_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(
        min_value=1,
        max_value=100,
    )


class RestaurantCheckoutSerializer(serializers.Serializer):
    items = CheckoutItemSerializer(
        many=True,
        allow_empty=False,
    )

    provider = serializers.ChoiceField(
        choices=RestaurantOrder.Provider.choices,
    )

    idempotency_key = serializers.UUIDField()

    def validate_items(self, value):
        if len(value) > 100:
            raise serializers.ValidationError(
                "100 tadan ortiq turdagi taom yuborib bo‘lmaydi."
            )

        ids = [item["food_id"] for item in value]

        if len(ids) != len(set(ids)):
            raise serializers.ValidationError(
                "Bir xil taomni takroran yubormang."
            )

        return value


class RestaurantOrderSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()

    class Meta:
        model = RestaurantOrder
        fields = [
            "id",
            "status",
            "provider",
            "total_amount",
            "created_at",
            "expires_at",
            "paid_at",
            "items",
        ]

    def get_items(self, obj):
        return [
            {
                "food_id": item.food_id,
                "name": item.name,
                "quantity": item.quantity,
                "unit_price": str(item.unit_price),
                "subtotal": str(item.subtotal),
            }
            for item in obj.items.all()
        ]
