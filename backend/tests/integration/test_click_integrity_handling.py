
from unittest.mock import patch

import pytest

from django.db import IntegrityError

from apps.payments.click_services import (
    ClickError,
    is_click_unique_conflict,
    prepare_click_payment,
)

from apps.payments.models import ClickTransaction

from tests.integration.test_competition_orders import (
    competition_user,
    competition,
    order_data,
)

from tests.integration.test_click_http_integration import (
    click_settings,
    click_order,
    make_payload,
)


class FakeDiagnostics:
    def __init__(self, constraint_name):
        self.constraint_name = constraint_name


class FakePostgresError(Exception):
    def __init__(self, sqlstate, constraint_name):
        self.sqlstate = sqlstate
        self.diag = FakeDiagnostics(constraint_name)
        super().__init__("Database error")


def make_integrity_error(sqlstate, constraint_name):
    error = IntegrityError("Database constraint error")
    error.__cause__ = FakePostgresError(
        sqlstate,
        constraint_name,
    )
    return error


def test_known_unique_constraint_is_recognized():
    error = make_integrity_error(
        "23505",
        "unique_prepared_click_order",
    )

    assert is_click_unique_conflict(error) is True


def test_unknown_unique_constraint_is_not_recognized():
    error = make_integrity_error(
        "23505",
        "some_other_constraint",
    )

    assert is_click_unique_conflict(error) is False


def test_non_unique_database_error_is_not_recognized():
    error = make_integrity_error(
        "23514",
        "click_transaction_positive_amount",
    )

    assert is_click_unique_conflict(error) is False


@pytest.mark.django_db
def test_prepare_known_integrity_error_returns_click_conflict(
    click_order,
):
    payload = make_payload(click_order)

    error = make_integrity_error(
        "23505",
        "unique_prepared_click_order",
    )

    with patch.object(
        ClickTransaction.objects,
        "create",
        side_effect=error,
    ):
        with pytest.raises(ClickError) as exc_info:
            prepare_click_payment(payload)

    assert exc_info.value.code == -4

    assert ClickTransaction.objects.count() == 0


@pytest.mark.django_db
def test_prepare_unknown_integrity_error_is_not_hidden(
    click_order,
):
    payload = make_payload(click_order)

    error = make_integrity_error(
        "23514",
        "click_transaction_positive_amount",
    )

    with patch.object(
        ClickTransaction.objects,
        "create",
        side_effect=error,
    ):
        with pytest.raises(IntegrityError):
            prepare_click_payment(payload)

    assert ClickTransaction.objects.count() == 0
