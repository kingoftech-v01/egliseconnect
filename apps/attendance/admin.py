"""Admin configuration for attendance models."""
from django.contrib import admin
from .models import MemberQRCode, AttendanceSession, AttendanceRecord, AbsenceAlert


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
    list_display = ['member', 'session', 'method', 'checked_in_at']
    list_filter = ['method', 'session__session_type']
    search_fields = ['member__first_name', 'member__last_name']


@admin.register(AbsenceAlert)
class AbsenceAlertAdmin(admin.ModelAdmin):
    list_display = ['member', 'consecutive_absences', 'alert_sent', 'last_attendance_date']
    list_filter = ['alert_sent']
    search_fields = ['member__first_name', 'member__last_name']
