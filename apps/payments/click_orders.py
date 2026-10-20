
from dataclasses import dataclass
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import DataError

from apps.football.models import HourlyBooking
from apps.restaurant_orders.models import RestaurantOrder
from apps.competitions.models import TicketOrder

from .security import PaymentVerificationError


@dataclass(frozen=True)
class ClickOrderInfo:
    category: str
    order_id: str
    amount: Decimal
    status: str
    provider: str


def find_click_order(model, order_id):
    """
    Buyurtmani ID bo'yicha xavfsiz qidiradi.

    Noto'g'ri PK formati sababli yuzaga keladigan
    xatolarni PaymentVerificationError ga aylantiradi.

    Haqiqiy database nosozliklarini yashirmaydi.
    """
    try:
        return model.objects.filter(
            pk=order_id
        ).first()

    except (
        ValueError,
        TypeError,
        ValidationError,
        DataError,
    ) as exc:
        raise PaymentVerificationError(
            "Buyurtma ID formati noto'g'ri."
        ) from exc


def get_click_order(merchant_trans_id):
    """
    Click merchant_trans_id formatini tekshiradi
    va tegishli buyurtma ma'lumotlarini qaytaradi.

    Formatlar:
        restaurant:<order_id>
        competition:<order_id>
        football:<booking_id>
    """

    if not isinstance(merchant_trans_id, str):
        raise PaymentVerificationError(
            "merchant_trans_id noto'g'ri."
        )

    try:
        category, order_id = merchant_trans_id.split(
            ":",
            1,
        )
    except ValueError as exc:
        raise PaymentVerificationError(
            "merchant_trans_id noto'g'ri."
        ) from exc

    if not order_id:
        raise PaymentVerificationError(
            "Buyurtma ID kiritilmagan."
        )

    if category == "restaurant":
        order = find_click_order(
            RestaurantOrder,
            order_id,
        )

        if order is None:
            raise PaymentVerificationError(
                "Restoran buyurtmasi topilmadi."
            )

        return ClickOrderInfo(
            category=category,
            order_id=str(order.pk),
            amount=order.total_amount,
            status=order.status,
            provider=order.provider,
        )

    if category == "competition":
        order = find_click_order(
            TicketOrder,
            order_id,
        )

        if order is None:
            raise PaymentVerificationError(
                "Chipta buyurtmasi topilmadi."
            )

        return ClickOrderInfo(
            category=category,
            order_id=str(order.pk),
            amount=order.total_amount,
            status=order.status,
            provider=order.provider,
        )

    if category == "football":
        booking = find_click_order(
            HourlyBooking,
            order_id,
        )

        if booking is None:
            raise PaymentVerificationError(
                "Futbol broni topilmadi."
            )

        return ClickOrderInfo(
            category=category,
            order_id=str(booking.pk),
            amount=booking.price_snapshot,
            status=booking.status,
            provider="click",
        )

    raise PaymentVerificationError(
        "Noma'lum to'lov kategoriyasi."
    )
