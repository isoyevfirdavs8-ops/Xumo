
from unittest.mock import patch

import pytest

from apps.competitions.models import Ticket, TicketOrder
from apps.finance.models import RevenueEntry
from apps.payments.models import ClickTransaction

from tests.integration.test_competition_orders import (
    competition_user,
    competition,
    order_data,
)
from apps.payments.exceptions import PaymentTemporaryFailure

from tests.integration.test_click_http_integration import (
    click_settings,
    click_order,
    make_payload,
    post_prepare,
    post_complete,
)


@pytest.fixture
def prepared_payment(client, click_order):
    """
    Click Prepare muvaffaqiyatli bajarilgan,
    lekin Complete hali kelmagan holat.
    """
    prepare_data = make_payload(click_order)

    response = post_prepare(client, prepare_data)

    assert response.status_code == 200
    assert response.json()["error"] == 0

    return {
        "order": click_order,
        "click_trans_id": prepare_data["click_trans_id"],
        "prepare_id": response.json()["merchant_prepare_id"],
    }


def complete_payload(prepared_payment):
    return make_payload(
        prepared_payment["order"],
        action="1",
        click_trans_id=prepared_payment["click_trans_id"],
        prepare_id=prepared_payment["prepare_id"],
        error="0",
    )


def assert_unpaid_state(prepared_payment):
    order = prepared_payment["order"]
    order.refresh_from_db()

    tx = ClickTransaction.objects.get(
        click_trans_id=prepared_payment["click_trans_id"]
    )

    assert order.status == TicketOrder.Status.PENDING
    assert tx.status == ClickTransaction.Status.PREPARED

    assert Ticket.objects.filter(
        order=order
    ).count() == 0

    assert RevenueEntry.objects.filter(
        source="competition_ticket_order",
        source_payment_id=str(order.pk),
    ).count() == 0


def assert_paid_once(prepared_payment):
    order = prepared_payment["order"]
    order.refresh_from_db()

    tx = ClickTransaction.objects.get(
        click_trans_id=prepared_payment["click_trans_id"]
    )

    assert order.status == TicketOrder.Status.PAID
    assert tx.status == ClickTransaction.Status.COMPLETED

    assert Ticket.objects.filter(
        order=order
    ).count() == order.quantity

    assert RevenueEntry.objects.filter(
        source="competition_ticket_order",
        source_payment_id=str(order.pk),
        entry_type=RevenueEntry.EntryType.PAYMENT,
    ).count() == 1


@pytest.mark.django_db
def test_recovery_after_settlement_validation_failure(
    client,
    prepared_payment,
    verified_click_provider,
):
    """
    Settlement ValueError chiqarsa:
    - Complete rad etiladi
    - DB rollback bo'ladi
    - keyingi retry muvaffaqiyatli ishlaydi
    """
    payload = complete_payload(prepared_payment)

    with patch(
        "apps.payments.click_services.settle_competition_payment",
        side_effect=PaymentTemporaryFailure(),
    ):
        failed = post_complete(client, payload)

    assert failed.status_code == 200
    assert failed.json()["error"] == -9

    assert_unpaid_state(prepared_payment)

    recovered = post_complete(client, payload)

    assert recovered.status_code == 200
    assert recovered.json()["error"] == 0

    assert_paid_once(prepared_payment)


@pytest.mark.django_db
def test_repeated_complete_after_recovery_is_idempotent(
    client,
    prepared_payment,
    verified_click_provider,
):
    """
    Recovery muvaffaqiyatli bo'lgandan keyin
    Complete qayta yuborilsa, settlement
    takrorlanmasligi kerak.
    """
    payload = complete_payload(prepared_payment)

    with patch(
        "apps.payments.click_services.settle_competition_payment",
        side_effect=PaymentTemporaryFailure(),
    ):
        failed = post_complete(client, payload)

    assert failed.json()["error"] == -9
    assert_unpaid_state(prepared_payment)

    first_success = post_complete(client, payload)
    second_success = post_complete(client, payload)

    assert first_success.json()["error"] == 0
    assert second_success.json()["error"] == 0

    assert (
            first_success.json()["merchant_confirm_id"]
            == second_success.json()["merchant_confirm_id"]
    )

    assert_paid_once(prepared_payment)


@pytest.mark.django_db
def test_recovery_after_transaction_rollback(
    client,
    prepared_payment,
    verified_click_provider,
):
    """
    Settlement davomida kutilmagan exception
    yuz bersa, barcha DB o'zgarishlari rollback
    bo'lishi kerak.

    RuntimeError hozirgi view tomonidan
    ushlanmaydi, shuning uchun test exceptionni
    kutadi. Keyingi retry esa ishlashi kerak.
    """
    payload = complete_payload(prepared_payment)

    with patch(
        "apps.payments.click_services.settle_competition_payment",
        side_effect=RuntimeError("Unexpected settlement error"),
    ):
        with pytest.raises(
            RuntimeError,
            match="Unexpected settlement error",
        ):
            post_complete(client, payload)

    assert_unpaid_state(prepared_payment)

    recovered = post_complete(client, payload)

    assert recovered.json()["error"] == 0

    assert_paid_once(prepared_payment)


@pytest.mark.django_db
def test_cancelled_transaction_cannot_be_recovered_as_paid(
    client,
    prepared_payment,
):
    """
    CANCELLED holatdagi Click tranzaksiyani
    oddiy success retry bilan PAID qilish mumkin emas.
    """
    cancelled_payload = make_payload(
        prepared_payment["order"],
        action="1",
        click_trans_id=prepared_payment["click_trans_id"],
        prepare_id=prepared_payment["prepare_id"],
        error="-1",
    )

    cancelled = post_complete(client, cancelled_payload)

    assert cancelled.status_code == 200

    tx = ClickTransaction.objects.get(
        click_trans_id=prepared_payment["click_trans_id"]
    )
    assert tx.status == ClickTransaction.Status.CANCELLED

    retry = post_complete(
        client,
        complete_payload(prepared_payment),
    )

    assert retry.json()["error"] == -9

    order = prepared_payment["order"]
    order.refresh_from_db()

    assert order.status == TicketOrder.Status.PENDING

    assert Ticket.objects.filter(
        order=order
    ).count() == 0


@pytest.mark.django_db
def test_recovery_does_not_create_new_click_transaction(
    client,
    prepared_payment,
    verified_click_provider,
):
    """
    Xatodan keyingi retry yangi ClickTransaction
    yaratmasligi kerak.
    """
    payload = complete_payload(prepared_payment)

    original_tx = ClickTransaction.objects.get(
        click_trans_id=prepared_payment["click_trans_id"]
    )

    with patch(
        "apps.payments.click_services.settle_competition_payment",
        side_effect=PaymentTemporaryFailure(),
    ):
        failed = post_complete(client, payload)

    assert failed.json()["error"] == -9

    recovered = post_complete(client, payload)

    assert recovered.json()["error"] == 0

    assert ClickTransaction.objects.count() == 1

    recovered_tx = ClickTransaction.objects.get(
        click_trans_id=prepared_payment["click_trans_id"]
    )

    assert (
        recovered_tx.merchant_prepare_id
        == original_tx.merchant_prepare_id
    )

    assert_paid_once(prepared_payment)
