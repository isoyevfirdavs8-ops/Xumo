
import pytest

from apps.payments.models import ClickTransaction

from tests.integration.test_competition_orders import (
    order_data,
    competition_user,
    competition,
)
from apps.competitions.models import TicketOrder
from apps.finance.models import RevenueEntry
from apps.payments.exceptions import PaymentSettlementError
from tests.integration.test_click_http_integration import (
    click_order,
    click_settings,
    make_payload,
    post_prepare,
    post_complete,
)


@pytest.mark.django_db
def test_prepare_rejects_invalid_signature(client, click_order):
    payload = make_payload(click_order)
    payload["sign_string"] = "invalid-signature"

    response = post_prepare(client, payload)

    assert response.status_code == 200
    assert response.json()["error"] == -1

    assert not ClickTransaction.objects.filter(
        click_trans_id=payload["click_trans_id"],
    ).exists()


@pytest.mark.django_db
def test_prepare_rejects_wrong_service_id(client, click_order):
    payload = make_payload(click_order)
    payload["service_id"] = "wrong-service"

    response = post_prepare(client, payload)

    assert response.json()["error"] == -1

    assert not ClickTransaction.objects.filter(
        click_trans_id=payload["click_trans_id"],
    ).exists()


@pytest.mark.django_db
def test_complete_rejects_invalid_signature_without_settlement(
    client,
    click_order,
):
    prepare_data = make_payload(click_order)
    prepared = post_prepare(client, prepare_data)

    assert prepared.json()["error"] == 0

    payload = make_payload(
        click_order,
        action="1",
        click_trans_id=prepare_data["click_trans_id"],
        prepare_id=prepared.json()["merchant_prepare_id"],
    )

    payload["sign_string"] = "tampered-signature"

    response = post_complete(client, payload)

    assert response.json()["error"] == -1

    tx = ClickTransaction.objects.get(
        click_trans_id=prepare_data["click_trans_id"],
    )

    assert tx.status == ClickTransaction.Status.PREPARED


@pytest.mark.django_db
def test_complete_rejects_wrong_prepare_id(
    client,
    click_order,
):
    prepare_data = make_payload(click_order)
    prepared = post_prepare(client, prepare_data)

    assert prepared.json()["error"] == 0

    wrong_prepare_id = (
        int(prepared.json()["merchant_prepare_id"]) + 999
    )

    payload = make_payload(
        click_order,
        action="1",
        click_trans_id=prepare_data["click_trans_id"],
        prepare_id=wrong_prepare_id,
    )

    response = post_complete(client, payload)

    assert response.json()["error"] == -4

    tx = ClickTransaction.objects.get(
        click_trans_id=prepare_data["click_trans_id"],
    )

    assert tx.status == ClickTransaction.Status.PREPARED


@pytest.mark.django_db
def test_complete_rejects_modified_amount(
    client,
    click_order,
):
    prepare_data = make_payload(click_order)
    prepared = post_prepare(client, prepare_data)

    assert prepared.json()["error"] == 0

    modified_amount = click_order.total_amount + 100

    payload = make_payload(
        click_order,
        action="1",
        click_trans_id=prepare_data["click_trans_id"],
        prepare_id=prepared.json()["merchant_prepare_id"],
        amount=modified_amount,
    )

    response = post_complete(client, payload)

    assert response.json()["error"] == -2

    tx = ClickTransaction.objects.get(
        click_trans_id=prepare_data["click_trans_id"],
    )

    assert tx.status == ClickTransaction.Status.PREPARED



@pytest.mark.django_db
def test_duplicate_complete_does_not_duplicate_revenue(
    client,
    click_order,
    verified_click_provider,
):
    prepare_data = make_payload(click_order)
    prepared = post_prepare(client, prepare_data)

    assert prepared.json()["error"] == 0

    payload = make_payload(
        click_order,
        action="1",
        click_trans_id=prepare_data["click_trans_id"],
        prepare_id=prepared.json()["merchant_prepare_id"],
    )

    first = post_complete(client, payload)
    second = post_complete(client, payload)

    assert first.json()["error"] == 0
    assert second.json()["error"] == 0

    click_order.refresh_from_db()

    assert click_order.status == TicketOrder.Status.PAID

    assert RevenueEntry.objects.filter(
        source="competition_ticket_order",
        source_payment_id=str(click_order.pk),
    ).count() == 1

    assert ClickTransaction.objects.filter(
        click_trans_id=prepare_data["click_trans_id"],
        status=ClickTransaction.Status.COMPLETED,
    ).count() == 1


@pytest.mark.django_db
def test_settlement_failure_rolls_back(
    client,
    click_order,
    monkeypatch,
):
    prepare_data = make_payload(click_order)
    prepared = post_prepare(client, prepare_data)

    assert prepared.json()["error"] == 0

    payload = make_payload(
        click_order,
        action="1",
        click_trans_id=prepare_data["click_trans_id"],
        prepare_id=prepared.json()["merchant_prepare_id"],
    )

    def fail_settlement(**kwargs):
        raise PaymentSettlementError()

    monkeypatch.setattr(
        "apps.payments.click_services.settle_competition_payment",
        fail_settlement,
    )

    response = post_complete(client, payload)

    assert response.json()["error"] == -9

    click_order.refresh_from_db()

    assert click_order.status == TicketOrder.Status.PENDING

    tx = ClickTransaction.objects.get(
        click_trans_id=prepare_data["click_trans_id"],
    )

    assert tx.status == ClickTransaction.Status.PREPARED

    assert not RevenueEntry.objects.filter(
        source="competition_ticket_order",
        source_payment_id=str(click_order.pk),
    ).exists()


@pytest.mark.django_db
def test_tampered_error_rejected_by_provider(
    client,
    click_order,
):
    from unittest.mock import patch
    from decimal import Decimal

    from apps.payments.click_verification import (
        ClickVerificationResult,
    )

    prepare_data = make_payload(click_order)
    prepared = post_prepare(client, prepare_data)

    assert prepared.json()["error"] == 0

    payload = make_payload(
        click_order,
        action="1",
        click_trans_id=prepare_data["click_trans_id"],
        prepare_id=prepared.json()["merchant_prepare_id"],
        error="-1",
    )

    payload["error"] = "0"

    with patch(
        "apps.payments.click_services.verify_click_payment_with_provider",
        return_value=ClickVerificationResult(
            verified=False,
            click_trans_id=payload["click_trans_id"],
            merchant_trans_id=payload["merchant_trans_id"],
            amount=Decimal(str(payload["amount"])),
        ),
    ) as provider_mock:
        response = post_complete(client, payload)

    assert response.status_code == 200
    assert response.json()["error"] == -9
    provider_mock.assert_called_once()

    click_order.refresh_from_db()
    assert click_order.status != TicketOrder.Status.PAID


@pytest.mark.django_db
def test_tampered_error_must_not_mark_order_paid(
    client,
    click_order,
):
    prepare_data = make_payload(click_order)
    prepared = post_prepare(client, prepare_data)

    assert prepared.json()["error"] == 0

    payload = make_payload(
        click_order,
        action="1",
        click_trans_id=prepare_data["click_trans_id"],
        prepare_id=prepared.json()["merchant_prepare_id"],
        error="-1",
    )

    # Hujum simulyatsiyasi:
    # MD5 imzoni qayta hisoblamasdan
    # error=-1 qiymatini error=0 ga o'zgartiramiz.
    payload["error"] = "0"

    response = post_complete(client, payload)

    assert response.status_code == 200

    # Provider verification sozlanmagan.
    # Shuning uchun to'lov rad etilishi shart.
    assert response.json()["error"] == -9

    click_order.refresh_from_db()

    assert click_order.status == TicketOrder.Status.PENDING

    tx = ClickTransaction.objects.get(
        click_trans_id=prepare_data["click_trans_id"],
    )

    assert tx.status == ClickTransaction.Status.PREPARED

    # Moliyaviy yozuv yaratilmasligi kerak.
    assert not RevenueEntry.objects.filter(
        source="competition_ticket_order",
        source_payment_id=str(click_order.pk),
    ).exists()