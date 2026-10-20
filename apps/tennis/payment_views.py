
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import TennisPayment, TennisSubscription
from .payment_services import (
    create_demo_payment,
    complete_demo_payment,
)


class PaymentStartSerializer(serializers.Serializer):
    subscription_id = serializers.IntegerField(min_value=1)
    provider = serializers.ChoiceField(
        choices=TennisPayment.Provider.choices
    )


class PaymentCompleteSerializer(serializers.Serializer):
    success = serializers.BooleanField()


def payment_data(payment):
    return {
        "id": str(payment.id),
        "provider": payment.provider,
        "amount": str(payment.amount),
        "status": payment.status,
        "is_demo": payment.is_demo,
        "subscription_id": payment.subscription_id,
    }


class DemoPaymentStartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PaymentStartSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        try:
            payment = create_demo_payment(
                user=request.user,
                **serializer.validated_data,
            )
        except TennisSubscription.DoesNotExist:
            return Response(
                {"detail": "Obuna topilmadi."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            payment_data(payment),
            status=status.HTTP_200_OK,
        )


class DemoPaymentCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, payment_id):
        serializer = PaymentCompleteSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        payment = complete_demo_payment(
            user=request.user,
            payment_id=payment_id,
            success=serializer.validated_data["success"],
        )

        return Response(payment_data(payment))


class MyTennisPaymentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payments = (
            TennisPayment.objects
            .filter(subscription__user=request.user)
            .order_by("-created_at")[:100]
        )

        return Response([
            payment_data(payment)
            for payment in payments
        ])
