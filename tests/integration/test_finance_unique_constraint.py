import pytest

from django.db import IntegrityError, transaction

from apps.finance.models import RevenueEntry

from tests.integration.test_competition_orders import (
    competition_user,
    competition,
    order_data,
)

from tests.integration.test_click_http_integration import (
    click_order,
    click_settings,
    make_payload,
    post_prepare,
    post_complete,
)


@pytest.mark.django_db
def test_duplicate_revenue_event_rejected_by_database(
    client,
    click_order,
    verified_click_provider,
):
    # 1. Haqiqiy Click settlementni test rejimida bajaramiz.
    prepare_data = make_payload(click_order)

    prepared = post_prepare(client, prepare_data)
    assert prepared.json()["error"] == 0

    payload = make_payload(
        click_order,
        action="1",
        click_trans_id=prepare_data["click_trans_id"],
        prepare_id=prepared.json()["merchant_prepare_id"],
    )

    completed = post_complete(client, payload)
    assert completed.json()["error"] == 0

    # 2. Settlement yaratgan revenue yozuvini olamiz.
    revenue = RevenueEntry.objects.get(
        source="competition_ticket_order",
        source_payment_id=str(click_order.pk),
    )

    # 3. Xuddi shu moliyaviy hodisani takroran yozamiz.
    duplicate_data = {}

    for field in RevenueEntry._meta.concrete_fields:
        if field.primary_key:
            continue

        if field.name in ("created_at", "updated_at"):
            continue

        duplicate_data[field.attname] = getattr(
            revenue,
            field.attname,
        )

    # 4. PostgreSQL dublikatni rad etishi kerak.
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            RevenueEntry.objects.create(**duplicate_data)

    # 5. Birinchi moliyaviy yozuv saqlanib qolgan.
    assert RevenueEntry.objects.filter(
        source=revenue.source,
        source_payment_id=revenue.source_payment_id,
        entry_type=revenue.entry_type,
    ).count() == 1