import logging

import requests

from django.conf import settings
from django.utils.html import escape

from apps.restaurant_orders.models import RestaurantOrder


logger = logging.getLogger(__name__)


def build_order_message(order):
    user = order.user

    lines = [
        "🍽 <b>YANGI RESTORAN BUYURTMASI</b>",
        "",
        f"🆔 Buyurtma: <code>{order.id}</code>",
        f"👤 Mijoz: {escape(user.full_name)}",
        f"📞 Telefon: {escape(user.phone_number)}",
        "",
        "📋 <b>Buyurtmalar:</b>",
    ]

    for item in order.items.all():
        lines.append(
            f"• {escape(item.name)} × {item.quantity}"
            f" — {item.subtotal:,.0f} so'm"
        )

    lines.extend([
        "",
        f"💰 <b>Jami: {order.total_amount:,.0f} so'm</b>",
        "💳 To'lov: To'langan",
    ])

    return "\n".join(lines)


def send_paid_order_to_managers(order_id):
    token = settings.TELEGRAM_BOT_TOKEN
    manager_ids = settings.TELEGRAM_MANAGER_CHAT_IDS

    if not token or not manager_ids:
        logger.warning("Telegram bot sozlamalari to'liq emas.")
        return

    order = (
        RestaurantOrder.objects
        .select_related("user")
        .prefetch_related("items")
        .get(pk=order_id)
    )

    if order.status != RestaurantOrder.Status.PAID:
        return

    message = build_order_message(order)

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    for chat_id in manager_ids:
        response = requests.post(
            url,
            json={
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML",
                "reply_markup": order_keyboard(order),
            },
            timeout=10,
        )
        response.raise_for_status()


def order_keyboard(order):
    transitions = {
        "new": ("accepted", "✅ Qabul qilish"),
        "accepted": ("preparing", "👨‍🍳 Tayyorlanmoqda"),
        "preparing": ("delivered", "🚚 Yetkazib berildi"),
    }

    next_step = transitions.get(order.fulfillment_status)

    if not next_step:
        return {"inline_keyboard": []}

    next_status, label = next_step

    return {
        "inline_keyboard": [
            [
                {
                    "text": label,
                    "callback_data": (
                        f"restaurant:{order.id}:{next_status}"
                    ),
                }
            ]
        ]
    }