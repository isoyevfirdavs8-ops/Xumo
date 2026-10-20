import pytest

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.competitions.models import TicketOrder

from tests.integration.test_competition_orders import (
    competition_user,
    competition,
    order_data,
)

from tests.integration.test_click_http_integration import (
    click_order,
    click_settings,
)


@pytest.mark.django_db
def test_ticket_order_provider_is_immutable(click_order):
    original_provider = click_order.provider

    other_provider = (
        TicketOrder.Provider.PAYME
        if original_provider == TicketOrder.Provider.CLICK
        else TicketOrder.Provider.CLICK
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            TicketOrder.objects.filter(
                pk=click_order.pk,
            ).update(provider=other_provider)

    click_order.refresh_from_db()

    assert click_order.provider == original_provider


@pytest.mark.django_db
def test_paid_order_requires_payment_metadata(click_order):
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            TicketOrder.objects.filter(
                pk=click_order.pk,
            ).update(status=TicketOrder.Status.PAID)

    click_order.refresh_from_db()

    assert click_order.status == TicketOrder.Status.PENDING


@pytest.mark.django_db
def test_paid_order_transaction_id_is_immutable(click_order):
    TicketOrder.objects.filter(pk=click_order.pk).update(
        status=TicketOrder.Status.PAID,
        paid_at=timezone.now(),
        provider_transaction_id="click-original-123",
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            TicketOrder.objects.filter(
                pk=click_order.pk,
            ).update(
                provider_transaction_id="click-modified-456",
            )

    click_order.refresh_from_db()

    assert (
        click_order.provider_transaction_id
        == "click-original-123"
    )


@pytest.mark.django_db
def test_paid_order_paid_at_is_immutable(click_order):
    original_paid_at = timezone.now()

    TicketOrder.objects.filter(pk=click_order.pk).update(
        status=TicketOrder.Status.PAID,
        paid_at=original_paid_at,
        provider_transaction_id="click-original-123",
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            TicketOrder.objects.filter(
                pk=click_order.pk,
            ).update(paid_at=timezone.now())

    click_order.refresh_from_db()

    assert click_order.paid_at == original_paid_at


@pytest.mark.django_db
def test_valid_payment_metadata_transition(click_order):
    paid_at = timezone.now()

    TicketOrder.objects.filter(pk=click_order.pk).update(
        status=TicketOrder.Status.PAID,
        paid_at=paid_at,
        provider_transaction_id="click-valid-123",
    )

    click_order.refresh_from_db()

    assert click_order.status == TicketOrder.Status.PAID
    assert click_order.paid_at == paid_at
    assert (
        click_order.provider_transaction_id
        == "click-valid-123"
    )