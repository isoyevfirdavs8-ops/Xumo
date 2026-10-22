
from django.db import IntegrityError
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from .models import TicketOrder
from .order_serializers import (
    TicketOrderCreateSerializer,
    TicketOrderDetailSerializer,
)
from .services import create_ticket_order


class TicketOrderCreateView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TicketOrderCreateSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            order = create_ticket_order(
                user=request.user,
                **serializer.validated_data,
            )
        except IntegrityError:
            raise ValidationError({
                "idempotency_key": (
                    "Bu checkout so'rovi boshqa "
                    "jarayonda qayta ishlanmoqda."
                )
            })

        order = (
            TicketOrder.objects
            .select_related("competition")
            .prefetch_related("tickets")
            .get(pk=order.pk)
        )

        return Response(
            TicketOrderDetailSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )


class MyTicketOrdersView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TicketOrderDetailSerializer

    def get_queryset(self):
        return (
            TicketOrder.objects
            .filter(user=self.request.user)
            .select_related("competition")
            .prefetch_related("tickets")
            .order_by("-created_at")
        )
