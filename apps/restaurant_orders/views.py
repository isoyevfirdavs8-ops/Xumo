
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from .tasks import notify_restaurant_managers
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics


from .serializers import (
    RestaurantCheckoutSerializer,
    RestaurantOrderSerializer,
)
from .services import create_restaurant_order
from .models import RestaurantOrder


class SandboxRestaurantPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        if (
            settings.RESTAURANT_PAYMENT_MODE != "sandbox"
            or not settings.DEBUG
        ):
            return Response(
                {"detail": "Test to‘lov mavjud emas."},
                status=status.HTTP_403_FORBIDDEN,
            )

        with transaction.atomic():
            try:
                order = (
                    RestaurantOrder.objects
                    .select_for_update()
                    .get(
                        pk=order_id,
                        user=request.user,
                    )
                )
            except RestaurantOrder.DoesNotExist:
                return Response(
                    {"detail": "Buyurtma topilmadi."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            if order.status == RestaurantOrder.Status.PAID:
                return Response({
                    "order_id": str(order.id),
                    "status": "paid",
                    "message": "Buyurtma avval tasdiqlangan.",
                })

            if order.status != RestaurantOrder.Status.PENDING:
                return Response(
                    {"detail": "Bu buyurtmani to‘lab bo‘lmaydi."},
                    status=status.HTTP_409_CONFLICT,
                )

            if order.expires_at <= timezone.now():
                return Response(
                    {"detail": "Buyurtma muddati tugagan."},
                    status=status.HTTP_409_CONFLICT,
                )

            order.status = RestaurantOrder.Status.PAID
            order.paid_at = timezone.now()
            order.save(update_fields=["status", "paid_at"])

            payment = order.payment
            payment.provider_state = "sandbox_paid"
            payment.save(
                update_fields=["provider_state", "updated_at"]
            )
            transaction.on_commit(
                lambda order_id=str(order.id):
                notify_restaurant_managers.delay(order_id)
            )

        return Response({
            "order_id": str(order.id),
            "provider": order.provider,
            "status": "paid",
            "message": "Test to‘lov muvaffaqiyatli.",
        })






class RestaurantCheckoutView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RestaurantCheckoutSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        order = create_restaurant_order(
            user=request.user,
            items=data["items"],
            provider=data["provider"],
            key=data["idempotency_key"],
        )

        order = (
            RestaurantOrder.objects
            .prefetch_related("items")
            .get(pk=order.pk)
        )

        return Response(
            RestaurantOrderSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )


class RestaurantOrderDetailView(generics.RetrieveAPIView):
    serializer_class = RestaurantOrderSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "pk"

    def get_queryset(self):
        return (
            RestaurantOrder.objects
            .filter(user=self.request.user)
            .prefetch_related("items")
        )

