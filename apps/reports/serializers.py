"""Reports serializers."""
from rest_framework import serializers


class MemberStatsSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    active = serializers.IntegerField()
    inactive = serializers.IntegerField()
    new_this_month = serializers.IntegerField()
    new_this_year = serializers.IntegerField()
    role_breakdown = serializers.ListField()


class DonationStatsSerializer(serializers.Serializer):
    year = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_count = serializers.IntegerField()
    average_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    monthly_breakdown = serializers.ListField()
    by_type = serializers.ListField()
    by_payment_method = serializers.ListField()


class EventStatsSerializer(serializers.Serializer):
    year = serializers.IntegerField()
    total_events = serializers.IntegerField()
    upcoming = serializers.IntegerField()
    cancelled = serializers.IntegerField()
    by_type = serializers.ListField()
    total_rsvps = serializers.IntegerField()
    confirmed_rsvps = serializers.IntegerField()


class VolunteerStatsSerializer(serializers.Serializer):
    total_positions = serializers.IntegerField()
    volunteers_by_position = serializers.ListField()
    upcoming_schedules = serializers.IntegerField()
    confirmed_this_month = serializers.IntegerField()
    pending_this_month = serializers.IntegerField()


class HelpRequestStatsSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    open = serializers.IntegerField()
    resolved_this_month = serializers.IntegerField()
    by_urgency = serializers.ListField()
    by_category = serializers.ListField()


class BirthdaySerializer(serializers.Serializer):
    member_id = serializers.UUIDField()
    member_name = serializers.CharField()
    birthday = serializers.DateField()
    age = serializers.IntegerField(allow_null=True)


class DashboardSummarySerializer(serializers.Serializer):
    members = MemberStatsSerializer()
    donations = DonationStatsSerializer()
    events = EventStatsSerializer()
    volunteers = VolunteerStatsSerializer()
    help_requests = HelpRequestStatsSerializer()
    upcoming_birthdays = BirthdaySerializer(many=True)
    generated_at = serializers.DateTimeField()


class AttendanceReportSerializer(serializers.Serializer):
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    total_events = serializers.IntegerField()
    events = serializers.ListField()


class DonationReportSerializer(serializers.Serializer):
    year = serializers.IntegerField()
    total = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_count = serializers.IntegerField()
    unique_donors = serializers.IntegerField()
    monthly = serializers.ListField()
    top_donors = serializers.ListField()
    campaigns = serializers.ListField()


class VolunteerReportSerializer(serializers.Serializer):
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    total_shifts = serializers.IntegerField()
    completed = serializers.IntegerField()
    no_shows = serializers.IntegerField()
    by_position = serializers.ListField()
    top_volunteers = serializers.ListField()
