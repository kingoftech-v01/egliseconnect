"""Tests for reports services."""
import pytest
from datetime import date
from decimal import Decimal
from django.utils import timezone

from apps.reports.services import DashboardService, ReportService
from apps.members.tests.factories import MemberFactory
from apps.donations.tests.factories import DonationFactory
from apps.events.tests.factories import EventFactory, EventRSVPFactory
from apps.volunteers.tests.factories import (
    VolunteerPositionFactory, VolunteerScheduleFactory
)
from apps.help_requests.tests.factories import HelpRequestFactory


@pytest.mark.django_db
class TestDashboardService:
    """Tests for DashboardService statistics methods."""

    def test_get_member_stats(self):
        MemberFactory.create_batch(5, is_active=True)
        MemberFactory.create_batch(2, is_active=False)
        stats = DashboardService.get_member_stats()
        assert stats['total'] == 7
        assert stats['active'] == 5
        assert stats['inactive'] == 2

    def test_get_donation_stats(self):
        DonationFactory(amount=Decimal('100.00'))
        DonationFactory(amount=Decimal('200.00'))
        DonationFactory(amount=Decimal('150.00'))
        stats = DashboardService.get_donation_stats()
        assert stats['total_count'] == 3
        assert stats['total_amount'] == Decimal('450.00')

    def test_get_event_stats(self):
        EventFactory.create_batch(3, is_cancelled=False)
        EventFactory(is_cancelled=True)
        stats = DashboardService.get_event_stats()
        assert stats['total_events'] == 4
        assert stats['cancelled'] == 1

    def test_get_volunteer_stats(self):
        VolunteerPositionFactory.create_batch(3, is_active=True)
        stats = DashboardService.get_volunteer_stats()
        assert stats['total_positions'] == 3

    def test_get_help_request_stats(self):
        HelpRequestFactory.create_batch(2, status='new')
        HelpRequestFactory(status='in_progress')
        HelpRequestFactory(status='resolved')
        stats = DashboardService.get_help_request_stats()
        assert stats['total'] == 4
        assert stats['open'] == 3  # new + in_progress

    def test_get_dashboard_summary(self):
        MemberFactory()
        DonationFactory()
        EventFactory()
        summary = DashboardService.get_dashboard_summary()
        assert 'members' in summary
        assert 'donations' in summary
        assert 'events' in summary
        assert 'volunteers' in summary
        assert 'help_requests' in summary
        assert 'upcoming_birthdays' in summary
        assert 'generated_at' in summary


@pytest.mark.django_db
class TestReportService:
    """Tests for ReportService report generation methods."""

    def test_get_attendance_report(self):
        past_dt = timezone.now() - timezone.timedelta(days=7)
        event = EventFactory(
            is_cancelled=False,
            start_datetime=past_dt,
            end_datetime=past_dt + timezone.timedelta(hours=2),
        )
        EventRSVPFactory(event=event, status='confirmed')
        EventRSVPFactory(event=event, status='declined')
        report = ReportService.get_attendance_report()
        assert 'events' in report
        assert report['total_events'] >= 1

    def test_get_donation_report(self):
        year = date.today().year
        DonationFactory(amount=Decimal('100.00'))
        DonationFactory(amount=Decimal('200.00'))
        report = ReportService.get_donation_report(year)
        assert report['year'] == year
        assert report['total'] == Decimal('300.00')
        assert report['total_count'] == 2
        assert len(report['monthly']) == 12

    def test_get_volunteer_report(self):
        past_date = date.today() - timezone.timedelta(days=7)
        position = VolunteerPositionFactory()
        VolunteerScheduleFactory(position=position, status='completed', date=past_date)
        VolunteerScheduleFactory(position=position, status='no_show', date=past_date)
        report = ReportService.get_volunteer_report()
        assert report['total_shifts'] >= 2
        assert report['completed'] >= 1
        assert report['no_shows'] >= 1
