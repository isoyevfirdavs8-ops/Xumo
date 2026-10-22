from django.db import migrations


FORWARD_SQL = """
CREATE OR REPLACE FUNCTION competitions_protect_order_financial_fields()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.status IN ('paid', 'refunded') THEN
        IF
            NEW.quantity IS DISTINCT FROM OLD.quantity
            OR NEW.unit_price IS DISTINCT FROM OLD.unit_price
            OR NEW.total_amount IS DISTINCT FROM OLD.total_amount
        THEN
            RAISE EXCEPTION
                'Paid or refunded ticket order financial fields are immutable'
                USING ERRCODE = '23514';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER competitions_ticket_order_financial_immutability
BEFORE UPDATE ON competitions_ticketorder
FOR EACH ROW
EXECUTE FUNCTION competitions_protect_order_financial_fields();
"""


REVERSE_SQL = """
DROP TRIGGER IF EXISTS
    competitions_ticket_order_financial_immutability
ON competitions_ticketorder;

DROP FUNCTION IF EXISTS
    competitions_protect_order_financial_fields();
"""


class Migration(migrations.Migration):

    dependencies = [
        (
            "competitions",
            "0003_ticketorder_idempotency_key_and_more",
        ),
    ]

    operations = [
        migrations.RunSQL(
            sql=FORWARD_SQL,
            reverse_sql=REVERSE_SQL,
        ),
    ]