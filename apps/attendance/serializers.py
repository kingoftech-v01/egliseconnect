"""Serializers for attendance models."""
from rest_framework import serializers
from .models import (
    MemberQRCode, AttendanceSession, AttendanceRecord, AbsenceAlert,
    ChildCheckIn, KioskConfig, NFCTag, AttendanceStreak,
    GeoFence, VisitorInfo,
)


class MemberQRCodeSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.full_name', read_only=True)
    is_valid = serializers.ReadOnlyField()

    class Meta:
        model = MemberQRCode
        fields = ['id', 'member', 'member_name', 'code', 'qr_image',
                  'generated_at', 'expires_at', 'is_valid']


class AttendanceRecordSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.full_name', read_only=True)
    duration_minutes = serializers.ReadOnlyField()

    class Meta:
        model = AttendanceRecord
        fields = ['id', 'session', 'member', 'member_name',
                  'checked_in_at', 'checked_out_at', 'method',
                  'duration_minutes', 'notes']


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
                  'last_attendance_date', 'alert_sent', 'acknowledged_by',
                  'acknowledged_at', 'notes']


class CheckInSerializer(serializers.Serializer):
    qr_code = serializers.CharField()
    session_id = serializers.UUIDField()


class ChildCheckInSerializer(serializers.ModelSerializer):
    child_name = serializers.CharField(source='child.full_name', read_only=True)
    parent_name = serializers.CharField(source='parent_member.full_name', read_only=True)
    is_checked_out = serializers.ReadOnlyField()

    class Meta:
        model = ChildCheckIn
        fields = ['id', 'child', 'child_name', 'parent_member', 'parent_name',
                  'session', 'check_in_time', 'check_out_time',
                  'security_code', 'is_checked_out', 'checked_out_by']
        read_only_fields = ['security_code', 'check_in_time']


class ChildCheckOutSerializer(serializers.Serializer):
    security_code = serializers.CharField(max_length=6, min_length=6)


class KioskConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = KioskConfig
        fields = ['id', 'name', 'location', 'auto_timeout_seconds',
                  'session', 'is_active']
        # admin_pin is deliberately excluded from API for security


class KioskCheckinSerializer(serializers.Serializer):
    """Serializer for kiosk-based check-in (by member name search or QR)."""
    member_id = serializers.UUIDField(required=False)
    qr_code = serializers.CharField(required=False)
    session_id = serializers.UUIDField()
    kiosk_id = serializers.UUIDField(required=False)


class NFCTagSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.full_name', read_only=True)

    class Meta:
        model = NFCTag
        fields = ['id', 'member', 'member_name', 'tag_id',
                  'registered_at', 'is_active']


class NFCCheckinSerializer(serializers.Serializer):
    """Serializer for NFC-based check-in."""
    tag_id = serializers.CharField()
    session_id = serializers.UUIDField()


class AttendanceStreakSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.full_name', read_only=True)

    class Meta:
        model = AttendanceStreak
        fields = ['id', 'member', 'member_name', 'current_streak',
                  'longest_streak', 'last_attendance_date']


class GeoFenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeoFence
        fields = ['id', 'name', 'latitude', 'longitude',
                  'radius_meters', 'is_active']


class GeoCheckinSerializer(serializers.Serializer):
    """Serializer for GPS-based check-in."""
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    session_id = serializers.UUIDField()


class VisitorInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = VisitorInfo
        fields = ['id', 'name', 'email', 'phone', 'source', 'session',
                  'notes', 'follow_up_assigned_to', 'follow_up_completed',
                  'follow_up_completed_at', 'welcome_sent', 'created_at']


class MemberSearchSerializer(serializers.Serializer):
    """Serializer for member name search results."""
    id = serializers.UUIDField()
    full_name = serializers.CharField()
    member_number = serializers.CharField()
    photo_url = serializers.SerializerMethodField()

    def get_photo_url(self, obj):
        if obj.photo:
            return obj.photo.url
        return None


class AttendanceTrendSerializer(serializers.Serializer):
    """Serializer for attendance trend data points."""
    period = serializers.DateField()
    count = serializers.IntegerField()


class CheckOutSerializer(serializers.Serializer):
    """Serializer for member check-out."""
    record_id = serializers.UUIDField()


class FamilyCheckinSerializer(serializers.Serializer):
    """Serializer for family check-in."""
    family_id = serializers.UUIDField()
    session_id = serializers.UUIDField()
    member_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        help_text='Optional subset of family member IDs to check in'
    )
