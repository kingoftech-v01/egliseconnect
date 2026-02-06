"""Serializers for attendance models."""
from rest_framework import serializers
from .models import MemberQRCode, AttendanceSession, AttendanceRecord, AbsenceAlert


class MemberQRCodeSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.full_name', read_only=True)
    is_valid = serializers.ReadOnlyField()

    class Meta:
        model = MemberQRCode
        fields = ['id', 'member', 'member_name', 'code', 'qr_image',
                  'generated_at', 'expires_at', 'is_valid']


class AttendanceRecordSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.full_name', read_only=True)

    class Meta:
        model = AttendanceRecord
        fields = ['id', 'session', 'member', 'member_name',
                  'checked_in_at', 'method', 'notes']


class AttendanceSessionSerializer(serializers.ModelSerializer):
    attendee_count = serializers.ReadOnlyField()
    records = AttendanceRecordSerializer(many=True, read_only=True)

    class Meta:
        model = AttendanceSession
        fields = ['id', 'name', 'session_type', 'date', 'start_time',
                  'end_time', 'is_open', 'attendee_count', 'records']


class AbsenceAlertSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.full_name', read_only=True)

    class Meta:
        model = AbsenceAlert
        fields = ['id', 'member', 'member_name', 'consecutive_absences',
                  'last_attendance_date', 'alert_sent', 'notes']


class CheckInSerializer(serializers.Serializer):
    qr_code = serializers.CharField()
    session_id = serializers.UUIDField()
