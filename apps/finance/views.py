
from datetime import date

from django.utils.dateparse import parse_date
from rest_framework.decorators import (
    api_view,
    permission_classes,
)
from rest_framework.exceptions import (
    PermissionDenied,
    ValidationError,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .services import get_revenue_statistics


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def revenue_dashboard(request):
    user = request.user

    if not (user.is_active and user.is_staff):
        raise PermissionDenied(
            "Moliyaviy statistika faqat administrator uchun."
        )

    start_raw = request.query_params.get("start")
    end_raw = request.query_params.get("end")

    start = parse_date(start_raw) if start_raw else None
    end = parse_date(end_raw) if end_raw else None

    if start_raw and start is None:
        raise ValidationError({
            "start": "YYYY-MM-DD formatida kiriting."
        })

    if end_raw and end is None:
        raise ValidationError({
            "end": "YYYY-MM-DD formatida kiriting."
        })

    if start and end and start > end:
        raise ValidationError({
            "end": "Tugash sanasi boshlanishdan oldin."
        })

    return Response(
        get_revenue_statistics(start=start, end=end)
    )
