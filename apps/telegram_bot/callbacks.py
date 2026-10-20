import logging
import uuid

import requests

from django.conf import settings
from django.db import transaction

from apps.restaurant_orders.models import RestaurantOrder
from apps.telegram_bot.services import order_keyboard


logger = logging.getLogger(__name__)

TRANSITIONS = {
    "new": "accepted",
    "accepted": "preparing",
    "preparing": "delivered",
}


def telegram_api(method, payload):
    response = requests.post(
        f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/{method}",
        json=payload,
        timeout=10,
    )
    response.raise_for_status()

    result = response.json()
    if not result.get("ok"):
        raise RuntimeError(
            f"Telegram API error: {result.get('description', 'Unknown')}"
        )

    return result


def process_order_callback(callback):
    callback_id = callback.get("id")
    manager_id = callback.get("from", {}).get("id")
    message = callback.get("message") or {}
    chat = message.get("chat") or {}

    chat_id = chat.get("id")
    message_id = message.get("message_id")

    def answer(text):
        if callback_id:
            telegram_api(
                "answerCallbackQuery",
                {
                    "callback_query_id": callback_id,
                    "text": text,
                },
            )

    if (
        manager_id not in settings.TELEGRAM_MANAGER_CHAT_IDS
        or chat.get("type") != "private"
        or chat_id != manager_id
    ):
        answer("Sizda ruxsat yo'q.")
        return

    data = callback.get("data", "")
    parts = data.split(":")

    if len(parts) != 3 or parts[0] != "restaurant":
        answer("Noto'g'ri buyruq.")
        return

    try:
        order_id = uuid.UUID(parts[1])
    except (ValueError, AttributeError):
        answer("Buyurtma ID noto'g'ri.")
        return

    requested_status = parts[2]

    if requested_status not in TRANSITIONS.values():
        answer("Noto'g'ri holat.")
        return

    with transaction.atomic():
        try:
            order = (
                RestaurantOrder.objects
                .select_for_update()
                .get(pk=order_id)
            )
        except RestaurantOrder.DoesNotExist:
            result_text = "Buyurtma topilmadi."
            order = None
        else:
            if order.status != RestaurantOrder.Status.PAID:
                result_text = "Buyurtma to'lanmagan."
            elif TRANSITIONS.get(order.fulfillment_status) != requested_status:
                result_text = "Buyurtma holati allaqachon o'zgargan."
            else:
                order.fulfillment_status = requested_status
                order.save(update_fields=["fulfillment_status"])
                result_text = "Buyurtma holati yangilandi."

    answer(result_text)

    if order is not None and order.status == RestaurantOrder.Status.PAID:
        telegram_api(
            "editMessageReplyMarkup",
            {
                "chat_id": chat_id,
                "message_id": message_id,
                "reply_markup": order_keyboard(order),
            },
        )