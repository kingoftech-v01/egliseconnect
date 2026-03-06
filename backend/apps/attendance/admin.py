"""Admin configuration for attendance models."""
from django.contrib import admin
from .models import (
    MemberQRCode, AttendanceSession, AttendanceRecord, AbsenceAlert,
    ChildCheckIn, KioskConfig, NFCTag, AttendanceStreak,
    GeoFence, VisitorInfo,
)


@admin.register(MemberQRCode)
class MemberQRCodeAdmin(admin.ModelAdmin):
    list_display = ['member', 'code', 'generated_at', 'expires_at', 'is_valid']
    search_fields = ['member__first_name', 'member__last_name', 'code']
    readonly_fields = ['code', 'generated_at']


class AttendanceRecordInline(admin.TabularInline):
    model = AttendanceRecord
    extra = 0
    readonly_fields = ['checked_in_at']


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ['name', 'session_type', 'date', 'is_open', 'attendee_count']
    list_filter = ['session_type', 'is_open', 'date']
    search_fields = ['name']
    inlines = [AttendanceRecordInline]


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ['member', 'session', 'method', 'checked_in_at', 'checked_out_at']
    list_filter = ['method', 'session__session_type']
    search_fields = ['member__first_name', 'member__last_name']


@admin.register(AbsenceAlert)
class AbsenceAlertAdmin(admin.ModelAdmin):
    list_display = ['member', 'consecutive_absences', 'alert_sent',
                    'last_attendance_date', 'acknowledged_by']
    list_filter = ['alert_sent']
    search_fields = ['member__first_name', 'member__last_name']


@admin.register(ChildCheckIn)
class ChildCheckInAdmin(admin.ModelAdmin):
    list_display = ['child', 'parent_member', 'session', 'check_in_time',
                    'check_out_time', 'security_code', 'is_checked_out']
    list_filter = ['session__date']
    search_fields = ['child__first_name', 'child__last_name',
                     'parent_member__first_name', 'parent_member__last_name',
                     'security_code']
    readonly_fields = ['security_code', 'check_in_time']


@admin.register(KioskConfig)
class KioskConfigAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'is_active', 'auto_timeout_seconds', 'session']
    list_filter = ['is_active']
    search_fields = ['name', 'location']


@admin.register(NFCTag)
class NFCTagAdmin(admin.ModelAdmin):
    list_display = ['member', 'tag_id', 'registered_at', 'is_active']
    list_filter = ['is_active']
    search_fields = ['member__first_name', 'member__last_name', 'tag_id']
    readonly_fields = ['registered_at']


@admin.register(AttendanceStreak)
class AttendanceStreakAdmin(admin.ModelAdmin):
    list_display = ['member', 'current_streak', 'longest_streak', 'last_attendance_date']
    search_fields = ['member__first_name', 'member__last_name']
    readonly_fields = ['current_streak', 'longest_streak', 'last_attendance_date']


@admin.register(GeoFence)
class GeoFenceAdmin(admin.ModelAdmin):
    list_display = ['name', 'latitude', 'longitude', 'radius_meters', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']


@admin.register(VisitorInfo)
class VisitorInfoAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'source', 'session',
                    'follow_up_completed', 'welcome_sent']
    list_filter = ['source', 'follow_up_completed', 'welcome_sent']
    search_fields = ['name', 'email', 'phone']
