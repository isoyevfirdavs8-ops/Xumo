import uuid
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from apps.restaurant_orders.models import RestaurantOrder
from apps.telegram_bot.callbacks import process_order_callback


ORDER_ID = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")


def make_callback(status="accepted", manager_id=123456789):
    return {
        "id": "callback-123",
        "from": {"id": manager_id},
        "message": {
            "message_id": 100,
            "chat": {
                "id": 123456789,
                "type": "private",
            },
        },
        "data": f"restaurant:{ORDER_ID}:{status}",
    }


def make_order(status="paid", fulfillment_status="new"):
    order = SimpleNamespace(
        id=ORDER_ID,
        status=status,
        fulfillment_status=fulfillment_status,
    )
    order.save = lambda **kwargs: None
    return order


@pytest.fixture
def telegram_settings(settings):
    settings.TELEGRAM_BOT_TOKEN = "test-token"
    settings.TELEGRAM_MANAGER_CHAT_IDS = [123456789]


@pytest.mark.django_db
@patch("apps.telegram_bot.callbacks.telegram_api")
def test_unauthorized_manager_is_rejected(
    mock_api,
    telegram_settings,
):
    process_order_callback(
        make_callback(manager_id=999999999)
    )

    mock_api.assert_called_once()
    assert mock_api.call_args.args[0] == "answerCallbackQuery"
    assert "ruxsat" in mock_api.call_args.args[1]["text"]


@pytest.mark.django_db
@patch("apps.telegram_bot.callbacks.RestaurantOrder.objects")
@patch("apps.telegram_bot.callbacks.telegram_api")
def test_unpaid_order_cannot_be_accepted(
    mock_api,
    mock_objects,
    telegram_settings,
):
    order = make_order(status="pending")

    mock_objects.select_for_update.return_value.get.return_value = order

    process_order_callback(make_callback())

    assert order.fulfillment_status == "new"
    assert "to'lanmagan" in mock_api.call_args_list[0].args[1]["text"]


@pytest.mark.django_db
@patch("apps.telegram_bot.callbacks.RestaurantOrder.objects")
@patch("apps.telegram_bot.callbacks.telegram_api")
def test_manager_accepts_paid_order(
    mock_api,
    mock_objects,
    telegram_settings,
):
    order = make_order()

    mock_objects.select_for_update.return_value.get.return_value = order

    process_order_callback(make_callback())

    assert order.fulfillment_status == "accepted"
    assert mock_api.call_count == 2


@pytest.mark.django_db
@patch("apps.telegram_bot.callbacks.RestaurantOrder.objects")
@patch("apps.telegram_bot.callbacks.telegram_api")
def test_invalid_transition_does_not_change_status(
    mock_api,
    mock_objects,
    telegram_settings,
):
    order = make_order(fulfillment_status="new")

    mock_objects.select_for_update.return_value.get.return_value = order

    process_order_callback(make_callback(status="delivered"))

    assert order.fulfillment_status == "new"
    assert "allaqachon" in mock_api.call_args_list[0].args[1]["text"]


@pytest.mark.django_db
@patch("apps.telegram_bot.callbacks.RestaurantOrder.objects")
@patch("apps.telegram_bot.callbacks.telegram_api")
def test_delivered_order_cannot_be_accepted_again(
    mock_api,
    mock_objects,
    telegram_settings,
):
    order = make_order(fulfillment_status="delivered")

    mock_objects.select_for_update.return_value.get.return_value = order

    process_order_callback(make_callback(status="accepted"))

    assert order.fulfillment_status == "delivered"
    assert "allaqachon" in mock_api.call_args_list[0].args[1]["text"]