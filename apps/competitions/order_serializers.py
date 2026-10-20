
from rest_framework import serializers

from .models import TicketOrder


class TicketOrderCreateSerializer(serializers.Serializer):
    competition_id = serializers.IntegerField(min_value=1)
    full_name = serializers.CharField(max_length=200)
    phone_number = serializers.CharField(max_length=20)
    quantity = serializers.IntegerField(
        min_value=1,
        max_value=10,
    )
    provider = serializers.ChoiceField(
        choices=TicketOrder.Provider.choices
    )
    idempotency_key = serializers.UUIDField()


class TicketOrderDetailSerializer(
    serializers.ModelSerializer
):
    competition_name = serializers.CharField(
        source="competition.name",
        read_only=True,
    )

    tickets = serializers.SerializerMethodField()

    class Meta:
        model = TicketOrder
        fields = [
            "id",
            "competition",
            "competition_name",
            "full_name",
            "quantity",
            "unit_price",
            "total_amount",
            "provider",
            "status",
            "payment_expires_at",
            "paid_at",
            "tickets",
            "created_at",
        ]

    def get_tickets(self, obj):
        if obj.status != TicketOrder.Status.PAID:
            return []

        return [
            {
                "id": str(ticket.id),
                "ticket_number": str(
                    ticket.ticket_number
                ),
                "is_used": ticket.is_used,
            }
            for ticket in obj.tickets.all()
        ]
