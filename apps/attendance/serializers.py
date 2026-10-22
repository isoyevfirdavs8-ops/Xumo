from rest_framework import serializers
from apps.football.models import FootballSubscription
from apps.boxing.models import BoxingSubscription
from apps.tennis.models import TennisSubscription
from .models import Attendance


class AttendanceRecordSerializer(serializers.ModelSerializer):
    marked_by_name = serializers.CharField(
        source="marked_by.full_name",
        read_only=True,
    )

    class Meta:
        model = Attendance
        fields = [
            "id",
            "date",
            "status",
            "marked_by_name",
            "created_at",
            "updated_at",
        ]


class BoxingAttendanceStudentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(
        source="user.full_name",
        read_only=True,
    )
    phone_number = serializers.CharField(
        source="user.phone_number",
        read_only=True,
    )
    academy_name = serializers.CharField(
        source="academy.name",
        read_only=True,
    )

    class Meta:
        model = BoxingSubscription
        fields = [
            "id",
            "student_name",
            "phone_number",
            "academy_name",
            "month",
            "status",
            "paid_at",
        ]


class TennisAttendanceStudentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(
        source="user.full_name",
        read_only=True,
    )
    phone_number = serializers.CharField(
        source="user.phone_number",
        read_only=True,
    )
    court_name = serializers.CharField(
        source="court.name",
        read_only=True,
    )

    class Meta:
        model = TennisSubscription
        fields = [
            "id",
            "student_name",
            "phone_number",
            "court_name",
            "month",
            "status",
            "paid_at",
        ]




class AttendanceMarkSerializer(serializers.Serializer):
    sport = serializers.ChoiceField(
        choices=["boxing", "tennis", "football"]
    )
    subscription_id = serializers.IntegerField(min_value=1)
    date = serializers.DateField()
    status = serializers.ChoiceField(
        choices=["present", "absent"]
    )




class FootballAttendanceStudentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(
        source="user.full_name",
        read_only=True,
    )
    phone_number = serializers.CharField(
        source="user.phone_number",
        read_only=True,
    )
    academy_name = serializers.CharField(
        source="academy.name",
        read_only=True,
    )

    class Meta:
        model = FootballSubscription
        fields = [
            "id",
            "student_name",
            "phone_number",
            "academy_name",
            "month",
            "status",
            "paid_at",
        ]
