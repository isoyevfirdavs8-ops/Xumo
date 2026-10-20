
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class PaymentIntegrationPendingView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        # Provider autentifikatsiyasi va state machine
        # tayyor bo'lmaguncha to'lov tasdiqlanmaydi.
        return Response(
            {
                "detail": (
                    "Payment callback integratsiyasi "
                    "hali faollashtirilmagan."
                )
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
