from django.db import migrations


FORWARD_SQL = """
CREATE FUNCTION competitions_protect_payment_metadata()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    -- Provider checkout yaratilgandan keyin
    -- o'zgartirilmasligi kerak.
    IF NEW.provider IS DISTINCT FROM OLD.provider THEN
        RAISE EXCEPTION
            'Ticket order provider is immutable'
            USING ERRCODE = '23514';
    END IF;

    -- PENDING -> PAID o'tishida
    -- to'lov metadata majburiy.
    IF OLD.status = 'pending'
       AND NEW.status = 'paid'
    THEN
        IF NEW.paid_at IS NULL
           OR NEW.provider_transaction_id IS NULL
           OR BTRIM(NEW.provider_transaction_id) = ''
        THEN
            RAISE EXCEPTION
                'Paid ticket order requires payment metadata'
                USING ERRCODE = '23514';
        END IF;
    END IF;

    -- PAID / REFUNDED orderning
    -- to'lov metadata qiymatlari immutable.
    IF OLD.status IN ('paid', 'refunded') THEN
        IF
            NEW.paid_at IS DISTINCT FROM OLD.paid_at
            OR NEW.provider_transaction_id
               IS DISTINCT FROM OLD.provider_transaction_id
        THEN
            RAISE EXCEPTION
                'Paid ticket order metadata is immutable'
                USING ERRCODE = '23514';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER competitions_ticket_order_payment_metadata
BEFORE UPDATE ON competitions_ticketorder
FOR EACH ROW
EXECUTE FUNCTION competitions_protect_payment_metadata();
"""


REVERSE_SQL = """
DROP TRIGGER IF EXISTS
    competitions_ticket_order_payment_metadata
ON competitions_ticketorder;

DROP FUNCTION IF EXISTS
    competitions_protect_payment_metadata();
"""


class Migration(migrations.Migration):
    dependencies = [
        (
            "competitions",
            "0005_ticket_order_state_protection",
        ),
    ]

    operations = [
        migrations.RunSQL(
            sql=FORWARD_SQL,
            reverse_sql=REVERSE_SQL,
        ),
    ]