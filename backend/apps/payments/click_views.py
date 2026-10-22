
import logging


from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .click_security import verify_click_signature
from .click_services import (
    ClickError,
    prepare_click_payment,
    complete_click_payment,
)
from .exceptions import (
    PaymentSettlementError,
    PaymentOrderUnavailable,
    PaymentTransactionConflict,
    PaymentTemporaryFailure,
)
from .security import PaymentVerificationError


logger = logging.getLogger(__name__)



def click_response(
    *,
    click_trans_id,
    merchant_trans_id,
    error=0,
    error_note="Success",
    merchant_prepare_id=None,
    merchant_confirm_id=None,
):
    result = {
        "click_trans_id": click_trans_id,
        "merchant_trans_id": merchant_trans_id,
        "error": error,
        "error_note": error_note,
    }

    if merchant_prepare_id is not None:
        result["merchant_prepare_id"] = merchant_prepare_id

    if merchant_confirm_id is not None:
        result["merchant_confirm_id"] = merchant_confirm_id

    return Response(result, status=200)



class BaseClickCallbackView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    expected_action = None

    def post(self, request):
        data = request.data

        click_trans_id = str(
            data.get("click_trans_id", "")
        )
        merchant_trans_id = str(
            data.get("merchant_trans_id", "")
        )

        try:
            verify_click_signature(data)

            if str(data.get("action")) != self.expected_action:
                raise ClickError(-3, "Invalid action")

            tx = self.process(data)

            if self.expected_action == "0":
                return click_response(
                    click_trans_id=click_trans_id,
                    merchant_trans_id=merchant_trans_id,
                    merchant_prepare_id=tx.merchant_prepare_id,
                    error=0,
                    error_note="Success",
                )

            return click_response(
                click_trans_id=click_trans_id,
                merchant_trans_id=merchant_trans_id,
                merchant_confirm_id=tx.merchant_prepare_id,
                error=0,
                error_note="Success",
            )


        except PaymentVerificationError:
            return click_response(
                click_trans_id=click_trans_id,
                merchant_trans_id=merchant_trans_id,
                error=-1,
                error_note="Invalid signature or configuration",
            )

        except ClickError as exc:
            return click_response(
                click_trans_id=click_trans_id,
                merchant_trans_id=merchant_trans_id,
                error=exc.code,
                error_note=exc.message,
            )


        except PaymentOrderUnavailable:
            logger.warning(
                "Click payment order unavailable"
            )
            return click_response(
                click_trans_id=click_trans_id,
                merchant_trans_id=merchant_trans_id,
                error=-9,
                error_note="Order unavailable for payment",
            )

        except PaymentTransactionConflict:
            logger.warning(
                "Click payment transaction conflict"
            )
            return click_response(
                click_trans_id=click_trans_id,
                merchant_trans_id=merchant_trans_id,
                error=-4,
                error_note="Payment transaction conflict",
            )

        except PaymentTemporaryFailure:
            logger.error(
                "Temporary Click settlement failure",
                exc_info=True,
            )
            return click_response(
                click_trans_id=click_trans_id,
                merchant_trans_id=merchant_trans_id,
                error=-9,
                error_note="Payment processing temporarily unavailable",
            )

        except PaymentSettlementError:
            logger.error(
                "Click settlement error",
                exc_info=True,
            )
            return click_response(
                click_trans_id=click_trans_id,
                merchant_trans_id=merchant_trans_id,
                error=-9,
                error_note="Payment settlement failed",
            )


        




class ClickPrepareView(BaseClickCallbackView):
    expected_action = "0"

    def process(self, data):
        return prepare_click_payment(data)


class ClickCompleteView(BaseClickCallbackView):
    expected_action = "1"

    def process(self, data):
        return complete_click_payment(data)
