from django.db import migrations


FORWARD_SQL = """
CREATE OR REPLACE FUNCTION
competitions_protect_ticket_order_state()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    -- Buyurtma yaratilgandan keyin
    -- moliyaviy qiymatlar o'zgarmaydi.
    IF
        NEW.quantity IS DISTINCT FROM OLD.quantity
        OR NEW.unit_price IS DISTINCT FROM OLD.unit_price
        OR NEW.total_amount IS DISTINCT FROM OLD.total_amount
    THEN
        RAISE EXCEPTION
            'Ticket order financial fields are immutable'
            USING ERRCODE = '23514';
    END IF;

    -- Status o'zgarmasa, ruxsat.
    IF NEW.status IS NOT DISTINCT FROM OLD.status THEN
        RETURN NEW;
    END IF;

    -- PENDING -> PAID / FAILED / CANCELLED
    IF OLD.status = 'pending'
       AND NEW.status IN (
           'paid',
           'failed',
           'cancelled'
       )
    THEN
        RETURN NEW;
    END IF;

    -- PAID -> REFUNDED
    IF OLD.status = 'paid'
       AND NEW.status = 'refunded'
    THEN
        RETURN NEW;
    END IF;

    RAISE EXCEPTION
        'Invalid ticket order status transition: % -> %',
        OLD.status,
        NEW.status
        USING ERRCODE = '23514';
END;
$$;

CREATE TRIGGER competitions_ticket_order_state_protection
BEFORE UPDATE ON competitions_ticketorder
FOR EACH ROW
EXECUTE FUNCTION competitions_protect_ticket_order_state();
"""


REVERSE_SQL = """
DROP TRIGGER IF EXISTS
    competitions_ticket_order_state_protection
ON competitions_ticketorder;

DROP FUNCTION IF EXISTS
    competitions_protect_ticket_order_state();
"""


class Migration(migrations.Migration):

    dependencies = [
        (
            "competitions",
            "0004_ticket_order_immutability",
        ),
    ]

    operations = [
        migrations.RunSQL(
            sql=FORWARD_SQL,
            reverse_sql=REVERSE_SQL,
        ),
    ]