from types import SimpleNamespace

import pytest

from apps.telegram_bot.services import order_keyboard


@pytest.mark.parametrize(
    "current_status,expected_status",
    [
        ("new", "accepted"),
        ("accepted", "preparing"),
        ("preparing", "delivered"),
    ],
)
def test_order_keyboard_transitions(
    current_status,
    expected_status,
):
    order = SimpleNamespace(
        id="550e8400-e29b-41d4-a716-446655440000",
        fulfillment_status=current_status,
    )

    keyboard = order_keyboard(order)

    button = keyboard["inline_keyboard"][0][0]

    assert button["callback_data"] == (
        f"restaurant:{order.id}:{expected_status}"
    )


def test_delivered_order_has_no_buttons():
    order = SimpleNamespace(
        id="550e8400-e29b-41d4-a716-446655440000",
        fulfillment_status="delivered",
    )

    keyboard = order_keyboard(order)

    assert keyboard["inline_keyboard"] == []