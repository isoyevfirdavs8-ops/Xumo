from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from apps.restaurant_orders.models import RestaurantOrder
from apps.telegram_bot.services import (
    build_order_message,
    send_paid_order_to_managers,
)


def make_order(status=RestaurantOrder.Status.PAID):
    user = SimpleNamespace(
        full_name="Ali Valiyev",
        phone_number="+998901234567",

    )

    items = [
        SimpleNamespace(
            name="Burger",
            quantity=2,
            unit_price=Decimal("35000.00"),
            subtotal=Decimal("70000.00"),
        ),
        SimpleNamespace(
            name="Lavash",
            quantity=1,
            unit_price=Decimal("30000.00"),
            subtotal=Decimal("30000.00"),
        ),
    ]

    order = SimpleNamespace(
        id="550e8400-e29b-41d4-a716-446655440000",
        user=user,
        items=SimpleNamespace(all=lambda: items),
        total_amount=Decimal("100000.00"),
        status=status,
        fulfillment_status=RestaurantOrder.FulfillmentStatus.NEW,

    )

    return order


def test_order_message_contains_customer_information():
    order = make_order()

    message = build_order_message(order)

    assert "Ali Valiyev" in message
    assert "+998901234567" in message
    assert str(order.id) in message


def test_order_message_contains_foods_and_total():
    order = make_order()

    message = build_order_message(order)

    assert "Burger" in message
    assert "Lavash" in message
    assert "70000" in message.replace(",", "")
    assert "30000" in message.replace(",", "")
    assert "100000" in message.replace(",", "")


@patch("apps.telegram_bot.services.RestaurantOrder.objects")
@patch("apps.telegram_bot.services.requests.post")
def test_paid_order_is_sent_to_manager(
    mock_post,
    mock_objects,
    settings,
):
    settings.TELEGRAM_BOT_TOKEN = "test-token"
    settings.TELEGRAM_MANAGER_CHAT_IDS = [123456789]

    order = make_order()

    mock_objects.select_related.return_value.prefetch_related.return_value.get.return_value = order

    response = Mock()
    response.status_code = 200
    response.raise_for_status.return_value = None
    mock_post.return_value = response

    send_paid_order_to_managers(order.id)

    mock_post.assert_called_once()

    kwargs = mock_post.call_args.kwargs

    assert kwargs["json"]["chat_id"] == 123456789
    assert "Ali Valiyev" in kwargs["json"]["text"]
    assert kwargs["json"]["parse_mode"] == "HTML"


@patch("apps.telegram_bot.services.RestaurantOrder.objects")
@patch("apps.telegram_bot.services.requests.post")
def test_pending_order_is_not_sent(
    mock_post,
    mock_objects,
    settings,
):
    settings.TELEGRAM_BOT_TOKEN = "test-token"
    settings.TELEGRAM_MANAGER_CHAT_IDS = [123456789]

    order = make_order(
        status=RestaurantOrder.Status.PENDING
    )

    mock_objects.select_related.return_value.prefetch_related.return_value.get.return_value = order

    send_paid_order_to_managers(order.id)

    mock_post.assert_not_called()


@patch("apps.telegram_bot.services.RestaurantOrder.objects")
@patch("apps.telegram_bot.services.requests.post")
def test_telegram_api_error_is_raised(
    mock_post,
    mock_objects,
    settings,
):
    settings.TELEGRAM_BOT_TOKEN = "test-token"
    settings.TELEGRAM_MANAGER_CHAT_IDS = [123456789]

    order = make_order()

    mock_objects.select_related.return_value.prefetch_related.return_value.get.return_value = order

    mock_post.return_value.raise_for_status.side_effect = (
        RuntimeError("Telegram API error")
    )

    with pytest.raises(RuntimeError, match="Telegram API error"):
        send_paid_order_to_managers(order.id)