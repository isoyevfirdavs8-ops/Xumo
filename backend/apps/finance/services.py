
from datetime import timedelta
from decimal import Decimal

from django.db.models import (
    Case,
    Count,
    DecimalField,
    F,
    Q,
    Sum,
    Value,
    When,
)
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.boxing.models import BoxingPayment
from apps.tennis.models import TennisPayment
from apps.football.models import HourlyBooking
from apps.restaurant_orders.models import RestaurantOrder
from apps.competitions.models import TicketOrder

from .models import RevenueEntry


ZERO = Decimal("0.00")
MONEY = DecimalField(max_digits=18, decimal_places=2)

CATEGORY_LABELS = {
    "football": "Futbol",
    "tennis": "Tennis",
    "boxing": "Boks",
    "restaurant": "Restoran",
    "tournament": "Musobaqalar",
}


def money(value):
    return str(value if value is not None else ZERO)


def sum_amount(queryset, field):
    result = queryset.aggregate(
        total=Coalesce(
            Sum(field),
            Value(ZERO),
            output_field=MONEY,
        )
    )
    return result["total"]


def date_filter(queryset, field, start=None, end=None):
    if start:
        queryset = queryset.filter(
            **{f"{field}__date__gte": start}
        )

    if end:
        queryset = queryset.filter(
            **{f"{field}__date__lte": end}
        )

    return queryset


def get_revenue_statistics(start=None, end=None):
    # Moliyaviy reyestr — asosiy hisob manbasi.
    entries = date_filter(
        RevenueEntry.objects.all(),
        "occurred_at",
        start,
        end,
    )

    entries = entries.annotate(
        signed_amount=Case(
            When(
                entry_type=RevenueEntry.EntryType.REFUND,
                then=-F("amount"),
            ),
            default=F("amount"),
            output_field=MONEY,
        )
    )

    grouped = (
        entries.values("category")
        .annotate(
            total=Coalesce(
                Sum("signed_amount"),
                Value(ZERO),
                output_field=MONEY,
            )
        )
    )

    category_totals = {
        key: ZERO for key in CATEGORY_LABELS
    }

    for row in grouped:
        category_totals[row["category"]] = row["total"]

    total_revenue = sum(category_totals.values(), ZERO)

    payment_count = entries.filter(
        entry_type=RevenueEntry.EntryType.PAYMENT
    ).count()

    refund_count = entries.filter(
        entry_type=RevenueEntry.EntryType.REFUND
    ).count()

    # Mavjud modellardagi ma'lumotlarni nazorat qilish.
    # Bu summalar RevenueEntry bilan qo'shilmaydi.
    tennis_payments = date_filter(
        TennisPayment.objects.filter(
            status=TennisPayment.Status.SUCCEEDED,
            is_demo=False,
            paid_at__isnull=False,
        ),
        "paid_at",
        start,
        end,
    )

    boxing_payments = date_filter(
        BoxingPayment.objects.filter(
            status=BoxingPayment.Status.SUCCEEDED,
            is_demo=False,
            paid_at__isnull=False,
        ),
        "paid_at",
        start,
        end,
    )

    football_bookings = date_filter(
        HourlyBooking.objects.filter(
            status=HourlyBooking.Status.CONFIRMED
        ),
        "created_at",
        start,
        end,
    )

    restaurant_orders = date_filter(
        RestaurantOrder.objects.filter(
            status=RestaurantOrder.Status.PAID,
            paid_at__isnull=False,
        ),
        "paid_at",
        start,
        end,
    )

    competition_orders = date_filter(
        TicketOrder.objects.filter(
            status=TicketOrder.Status.PAID,
            paid_at__isnull=False,
        ),
        "paid_at",
        start,
        end,
    )

    return {
        "total_revenue": money(total_revenue),
        "payment_count": payment_count,
        "refund_count": refund_count,
        "categories": [
            {
                "key": key,
                "name": label,
                "revenue": money(category_totals[key]),
            }
            for key, label in CATEGORY_LABELS.items()
        ],
        "source_overview": {
            "football": {
                "count": football_bookings.count(),
                "amount": money(
                    sum_amount(
                        football_bookings,
                        "price_snapshot",
                    )
                ),
                "description": (
                    "Tasdiqlangan bronlar qiymati; "
                    "to'lov tasdig'i emas."
                ),
            },
            "tennis": {
                "count": tennis_payments.count(),
                "amount": money(
                    sum_amount(tennis_payments, "amount")
                ),
                "description": (
                    "Demo bo'lmagan muvaffaqiyatli "
                    "to'lovlar."
                ),
            },
            "boxing": {
                "count": boxing_payments.count(),
                "amount": money(
                    sum_amount(boxing_payments, "amount")
                ),
                "description": (
                    "Demo bo'lmagan muvaffaqiyatli "
                    "to'lovlar."
                ),
            },
            "restaurant": {
                "count": restaurant_orders.count(),
                "amount": money(
                    sum_amount(
                        restaurant_orders,
                        "total_amount",
                    )
                ),
                "description": (
                    "Paid buyurtmalar; haqiqiy "
                    "callback tekshiruvi talab etiladi."
                ),
            },
            "tournament": {
                "count": competition_orders.count(),
                "amount": money(
                    sum_amount(
                        competition_orders,
                        "total_amount",
                    )
                ),
                "description": (
                    "Paid chiptalar; haqiqiy "
                    "callback tekshiruvi talab etiladi."
                ),
            },
        },
    }
