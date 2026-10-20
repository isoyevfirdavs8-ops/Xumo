
class PaymentSettlementError(Exception):
    """
    Settlement jarayonidagi kutilgan biznes xatosi.
    """

    def __init__(
        self,
        message="Payment settlement failed",
        *,
        retryable=False,
    ):
        self.retryable = retryable
        super().__init__(message)


class PaymentOrderUnavailable(PaymentSettlementError):
    """
    Order to'lov uchun yaroqsiz:
    expired, cancelled yoki noto'g'ri status.
    """

    def __init__(self):
        super().__init__(
            "Order unavailable for payment",
            retryable=False,
        )


class PaymentTransactionConflict(PaymentSettlementError):
    """
    Boshqa tranzaksiya bilan to'langan
    yoki provider transaction ID mos emas.
    """

    def __init__(self):
        super().__init__(
            "Payment transaction conflict",
            retryable=False,
        )


class PaymentTemporaryFailure(PaymentSettlementError):
    """
    Vaqtinchalik ichki muammo.
    Keyinchalik retry mumkin.
    """

    def __init__(self):
        super().__init__(
            "Temporary payment processing failure",
            retryable=True,
        )
