from datetime import date
from calendar import monthrange
from .access import (
    is_attendance_admin,
    get_coach_profile,
    require_subscription_access,
)
from .permissions import IsAttendanceStaff
from django.db.models import Count, Q
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from .permissions import IsAttendanceStaff
from .access import is_attendance_admin, get_coach_profile
from apps.boxing.models import BoxingSubscription
from apps.tennis.models import TennisSubscription
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import mark_attendance
from .serializers import AttendanceMarkSerializer
from .models import Attendance
from .permissions import IsAttendanceManager
from .serializers import (
    AttendanceRecordSerializer,
    BoxingAttendanceStudentSerializer,
    TennisAttendanceStudentSerializer,
)


def get_selected_month(request):
    value = request.query_params.get("month")

    if not value:
        today = date.today()
        return today.replace(day=1)

    try:
        selected = date.fromisoformat(value)
    except ValueError:
        raise ValidationError({
            "month": "Sana YYYY-MM-01 formatida bo'lishi kerak."
        })

    if selected.day != 1:
        raise ValidationError({
            "month": "Oyning birinchi kunini kiriting."
        })

    return selected


class BoxingAttendanceListView(generics.ListAPIView):
    permission_classes = [IsAttendanceStaff]
    serializer_class = BoxingAttendanceStudentSerializer

    def get_queryset(self):
        month = get_selected_month(self.request)
        user = self.request.user

        queryset = (
            BoxingSubscription.objects
            .filter(
                month=month,
                status=BoxingSubscription.Status.PAID,
            )
            .select_related("user", "academy")
        )

        # Admin va manager barcha o'quvchilarni ko'radi
        if is_attendance_admin(user):
            return queryset.order_by("user__full_name", "id")

        # Coach profilini tekshiramiz
        coach = get_coach_profile(user)

        if coach is None:
            return queryset.none()

        # Coach faqat o'z akademiyasidagi o'quvchilarni ko'radi
        queryset = queryset.filter(
            academy__assigned_coaches=coach
        )

        return queryset.distinct().order_by(
            "user__full_name",
            "id",
        )


class TennisAttendanceListView(generics.ListAPIView):
    permission_classes = [IsAttendanceStaff]
    serializer_class = TennisAttendanceStudentSerializer

    def get_queryset(self):
        month = get_selected_month(self.request)
        user = self.request.user

        queryset = (
            TennisSubscription.objects
            .filter(
                month=month,
                status=TennisSubscription.Status.PAID,
            )
            .select_related("user", "court")
        )


        if is_attendance_admin(user):
            return queryset.order_by("user__full_name", "id")


        coach = get_coach_profile(user)

        if coach is None:
            return queryset.none()


        queryset = queryset.filter(
            court__assigned_coaches=coach
        )

        return queryset.distinct().order_by(
            "user__full_name",
            "id",
        )

class BoxingAttendanceDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAttendanceStaff]
    serializer_class = BoxingAttendanceStudentSerializer

    def get_queryset(self):
        queryset = (
            BoxingSubscription.objects
            .filter(status=BoxingSubscription.Status.PAID)
            .select_related("user", "academy")
        )

        user = self.request.user

        if is_attendance_admin(user):
            return queryset

        coach = get_coach_profile(user)

        if coach is None:
            return queryset.none()

        return queryset.filter(
            academy__assigned_coaches=coach
        ).distinct()


class TennisAttendanceDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAttendanceStaff]
    serializer_class = TennisAttendanceStudentSerializer

    def get_queryset(self):
        queryset = (
            TennisSubscription.objects
            .filter(status=TennisSubscription.Status.PAID)
            .select_related("user", "court")
        )

        user = self.request.user

        if is_attendance_admin(user):
            return queryset

        coach = get_coach_profile(user)

        if coach is None:
            return queryset.none()

        return queryset.filter(
            court__assigned_coaches=coach
        ).distinct()

from django.shortcuts import get_object_or_404


class AttendanceHistoryView(generics.ListAPIView):
    permission_classes = [IsAttendanceStaff]
    serializer_class = AttendanceRecordSerializer

    def get_queryset(self):
        sport = self.kwargs["sport"]
        subscription_id = self.kwargs["subscription_id"]

        if sport == "boxing":
            subscription = get_object_or_404(
                BoxingSubscription.objects.select_related(
                    "user", "academy"
                ),
                pk=subscription_id,
                status=BoxingSubscription.Status.PAID,
            )

            require_subscription_access(
                user=self.request.user,
                subscription=subscription,
                sport="boxing",
            )

            return (
                Attendance.objects
                .filter(boxing_subscription=subscription)
                .select_related("marked_by")
                .order_by("date")
            )

        if sport == "tennis":
            subscription = get_object_or_404(
                TennisSubscription.objects.select_related(
                    "user", "court"
                ),
                pk=subscription_id,
                status=TennisSubscription.Status.PAID,
            )

            require_subscription_access(
                user=self.request.user,
                subscription=subscription,
                sport="tennis",
            )

            return (
                Attendance.objects
                .filter(tennis_subscription=subscription)
                .select_related("marked_by")
                .order_by("date")
            )

        raise ValidationError({
            "sport": "Sport turi boxing yoki tennis bo'lishi kerak."
        })

class AttendanceMarkView(APIView):
    permission_classes = [IsAttendanceStaff]

    def put(self, request):
        serializer = AttendanceMarkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        attendance, created = mark_attendance(
            **serializer.validated_data,
            user=request.user,
        )

        return Response(
            {
                "id": attendance.id,
                "sport": serializer.validated_data["sport"],
                "subscription_id": serializer.validated_data[
                    "subscription_id"
                ],
                "date": attendance.date.isoformat(),
                "status": attendance.status,
                "marked_by": request.user.full_name,
                "created": created,
            },
            status=(
                status.HTTP_201_CREATED
                if created
                else status.HTTP_200_OK
            ),
        )