"""Reports API views."""
from datetime import date
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.core.permissions import IsPastor, IsAdmin, IsTreasurer
from .services import DashboardService, ReportService
from .serializers import (
    DashboardSummarySerializer,
    MemberStatsSerializer,
    DonationStatsSerializer,
    EventStatsSerializer,
    VolunteerStatsSerializer,
    HelpRequestStatsSerializer,
    AttendanceReportSerializer,
    DonationReportSerializer,
    VolunteerReportSerializer,
)


class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsPastor | IsAdmin]

    def list(self, request):
        data = DashboardService.get_dashboard_summary()
        serializer = DashboardSummarySerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def members(self, request):
        data = DashboardService.get_member_stats()
        serializer = MemberStatsSerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def donations(self, request):
        year = request.query_params.get('year')
        if year:
            try:
                year = int(year)
            except ValueError:
                year = None
        data = DashboardService.get_donation_stats(year)
        serializer = DonationStatsSerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def events(self, request):
        year = request.query_params.get('year')
        if year:
            try:
                year = int(year)
            except ValueError:
                year = None
        data = DashboardService.get_event_stats(year)
        serializer = EventStatsSerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def volunteers(self, request):
        data = DashboardService.get_volunteer_stats()
        serializer = VolunteerStatsSerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def help_requests(self, request):
        data = DashboardService.get_help_request_stats()
        serializer = HelpRequestStatsSerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def birthdays(self, request):
        days = request.query_params.get('days', 7)
        try:
            days = int(days)
        except ValueError:
            days = 7
        data = DashboardService.get_upcoming_birthdays(days)
        return Response(data)


class ReportViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsPastor | IsAdmin]

    @action(detail=False, methods=['get'])
    def attendance(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if start_date:
            try:
                start_date = date.fromisoformat(start_date)
            except ValueError:
                start_date = None
        if end_date:
            try:
                end_date = date.fromisoformat(end_date)
            except ValueError:
                end_date = None

        data = ReportService.get_attendance_report(start_date, end_date)
        serializer = AttendanceReportSerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='donations/(?P<year>[0-9]{4})')
    def donations(self, request, year=None):
        try:
            year = int(year)
        except (ValueError, TypeError):
            year = date.today().year

        data = ReportService.get_donation_report(year)
        serializer = DonationReportSerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def volunteers(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if start_date:
            try:
                start_date = date.fromisoformat(start_date)
            except ValueError:
                start_date = None
        if end_date:
            try:
                end_date = date.fromisoformat(end_date)
            except ValueError:
                end_date = None

        data = ReportService.get_volunteer_report(start_date, end_date)
        serializer = VolunteerReportSerializer(data)
        return Response(serializer.data)


class TreasurerDonationReportView(APIView):
    """Allows treasurers to access donation reports without full admin access."""
    permission_classes = [IsAuthenticated, IsTreasurer | IsPastor | IsAdmin]

    def get(self, request, year=None):
        if not year:
            year = date.today().year
        else:
            try:
                year = int(year)
            except ValueError:
                year = date.today().year

        data = ReportService.get_donation_report(year)
        serializer = DonationReportSerializer(data)
        return Response(serializer.data)
