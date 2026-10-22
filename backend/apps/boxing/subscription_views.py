
from datetime import date, timedelta

from django.db import transaction
from django.utils import timezone

from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import BoxingAcademy, BoxingSubscription, BoxingPayment
from .subscription_serializers import (
    BoxingSubscriptionCreateSerializer,
    BoxingSubscriptionSerializer,
    BoxingPaymentSerializer,
)
from .payment_services import (
    ensure_demo_mode,
    start_demo_payment,
    complete_demo_payment,
)


class BoxingSubscriptionViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        subscriptions = (
            BoxingSubscription.objects
            .filter(user=request.user)
            .select_related("academy")
            .order_by("-created_at")
        )
        return Response(
            BoxingSubscriptionSerializer(
                subscriptions, many=True
            ).data
        )

    @transaction.atomic
    def create(self, request):
        serializer = BoxingSubscriptionCreateSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        academy_id = serializer.validated_data["academy_id"]
        month = serializer.validated_data["month"]

        try:
            academy = (
                BoxingAcademy.objects
                .select_for_update()
                .get(
                    pk=academy_id,
                    status=BoxingAcademy.Status.ACTIVE,
                )
            )
        except BoxingAcademy.DoesNotExist:
            raise ValidationError({
                "academy_id": "Faol akademiya topilmadi."
            })

        subscription, created = (
            BoxingSubscription.objects.get_or_create(
                user=request.user,
                academy=academy,
                month=month,
                defaults={
                    "price_snapshot": academy.monthly_price,
                    "status": BoxingSubscription.Status.PENDING_PAYMENT,
                    "payment_expires_at": (
                        timezone.now() + timedelta(minutes=30)
                    ),
                },
            )
        )

        if subscription.status in (
            BoxingSubscription.Status.CANCELLED,
            BoxingSubscription.Status.EXPIRED,
        ):
            raise ValidationError(
                "Ushbu oy uchun obuna bekor qilingan yoki "
                "muddati tugagan. Administratorga murojaat qiling."
            )

        return Response(
            BoxingSubscriptionSerializer(subscription).data,
            status=(
                status.HTTP_201_CREATED
                if created else status.HTTP_200_OK
            ),
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def demo_payment_start(request):
    ensure_demo_mode()

    provider = request.data.get("provider")
    subscription_id = request.data.get("subscription_id")

    if not isinstance(subscription_id, int) or isinstance(
        subscription_id, bool
    ) or subscription_id < 1:
        raise ValidationError({
            "subscription_id": "To'g'ri obuna ID kiriting."
        })

    payment = start_demo_payment(
        user=request.user,
        subscription_id=subscription_id,
        provider=provider,
    )

    return Response(
        BoxingPaymentSerializer(payment).data,
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def demo_payment_complete(request, payment_id):
    ensure_demo_mode()

    success = request.data.get("success")

    if not isinstance(success, bool):
        raise ValidationError({
            "success": "true yoki false yuboring."
        })

    payment = complete_demo_payment(
        user=request.user,
        payment_id=payment_id,
        success=success,
    )

    return Response(
        BoxingPaymentSerializer(payment).data
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_boxing_payments(request):
    payments = (
        BoxingPayment.objects
        .filter(subscription__user=request.user)
        .select_related("subscription")
        .order_by("-created_at")
    )

    return Response(
        BoxingPaymentSerializer(payments, many=True).data
    )
