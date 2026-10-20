import pytest

from django.db import connection


@pytest.mark.django_db
def test_postgresql_connection():
    assert connection.vendor == "postgresql"

    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        result = cursor.fetchone()

    assert result == (1,)


@pytest.mark.django_db
def test_database_transaction_rollback():
    from django.db import transaction
    from django.contrib.auth.models import Group

    group_name = "rollback-test-group"

    with pytest.raises(RuntimeError):
        with transaction.atomic():
            Group.objects.create(name=group_name)
            raise RuntimeError("Force rollback")

    assert not Group.objects.filter(name=group_name).exists()
