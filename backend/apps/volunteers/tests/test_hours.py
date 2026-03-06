"""Tests for volunteer hour tracking: model, service, views."""
import pytest
from decimal import Decimal
from django.test import Client
from django.utils import timezone

from apps.core.constants import Roles
from apps.members.tests.factories import MemberFactory, MemberWithUserFactory
from apps.volunteers.models import VolunteerHours
from apps.volunteers.tests.factories import (
    VolunteerPositionFactory, VolunteerHoursFactory,
)
from apps.volunteers.services_hours import (
    log_hours, summarize_by_member, summarize_by_position,
    get_admin_report, export_report,
)

pytestmark = pytest.mark.django_db


class TestVolunteerHoursModel:
    """Tests for VolunteerHours model."""

    def test_str_contains_member_hours_date(self):
        entry = VolunteerHoursFactory()
        result = str(entry)
        assert str(entry.hours_worked) in result
        assert str(entry.date) in result

    def test_create_entry(self):
        entry = VolunteerHoursFactory(hours_worked=Decimal('5.00'))
        assert entry.hours_worked == Decimal('5.00')
        assert entry.pk is not None

    def test_approved_by_optional(self):
        entry = VolunteerHoursFactory(approved_by=None)
        assert entry.approved_by is None

    def test_approved_by_set(self):
        approver = MemberFactory()
        entry = VolunteerHoursFactory(approved_by=approver, approved_at=timezone.now())
        assert entry.approved_by == approver
        assert entry.approved_at is not None


class TestLogHoursService:
    """Tests for the log_hours service function."""

    def test_log_hours_creates_entry(self):
        member = MemberFactory()
        position = VolunteerPositionFactory()
        entry = log_hours(member, position, timezone.now().date(), 3.5, 'Testing')
        assert entry.pk is not None
        assert entry.hours_worked == Decimal('3.5')
        assert entry.description == 'Testing'

    def test_log_hours_with_approver(self):
        member = MemberFactory()
        approver = MemberFactory()
        position = VolunteerPositionFactory()
        entry = log_hours(member, position, timezone.now().date(), 2, approved_by=approver)
        assert entry.approved_by == approver
        assert entry.approved_at is not None

    def test_log_hours_without_approver(self):
        member = MemberFactory()
        position = VolunteerPositionFactory()
        entry = log_hours(member, position, timezone.now().date(), 1)
        assert entry.approved_by is None
        assert entry.approved_at is None


class TestSummarizeByMember:
    """Tests for summarize_by_member."""

    def test_empty_summary(self):
        member = MemberFactory()
        result = summarize_by_member(member)
        assert result['total_hours'] == Decimal('0')
        assert result['count'] == 0

    def test_summary_with_hours(self):
        member = MemberFactory()
        pos = VolunteerPositionFactory()
        VolunteerHoursFactory(member=member, position=pos, hours_worked=Decimal('5.00'))
        VolunteerHoursFactory(member=member, position=pos, hours_worked=Decimal('3.50'))
        result = summarize_by_member(member)
        assert result['total_hours'] == Decimal('8.50')
        assert result['count'] == 2
        assert len(result['by_position']) == 1

    def test_summary_with_date_filter(self):
        member = MemberFactory()
        pos = VolunteerPositionFactory()
        today = timezone.now().date()
        VolunteerHoursFactory(member=member, position=pos, date=today, hours_worked=Decimal('4.00'))
        yesterday = today - timezone.timedelta(days=1)
        VolunteerHoursFactory(member=member, position=pos, date=yesterday, hours_worked=Decimal('2.00'))
        result = summarize_by_member(member, date_from=today)
        assert result['total_hours'] == Decimal('4.00')


class TestSummarizeByPosition:
    """Tests for summarize_by_position."""

    def test_summary_by_position(self):
        pos = VolunteerPositionFactory()
        m1 = MemberFactory()
        m2 = MemberFactory()
        VolunteerHoursFactory(member=m1, position=pos, hours_worked=Decimal('3.00'))
        VolunteerHoursFactory(member=m2, position=pos, hours_worked=Decimal('5.00'))
        result = summarize_by_position(pos)
        assert result['total_hours'] == Decimal('8.00')
        assert result['count'] == 2


class TestAdminReport:
    """Tests for get_admin_report."""

    def test_returns_all_hours(self):
        VolunteerHoursFactory()
        VolunteerHoursFactory()
        result = get_admin_report()
        assert result.count() == 2

    def test_filter_by_position(self):
        pos1 = VolunteerPositionFactory()
        pos2 = VolunteerPositionFactory()
        VolunteerHoursFactory(position=pos1)
        VolunteerHoursFactory(position=pos2)
        result = get_admin_report(position=pos1)
        assert result.count() == 1


class TestExportReport:
    """Tests for CSV export."""

    def test_export_returns_csv_response(self):
        VolunteerHoursFactory()
        qs = get_admin_report()
        response = export_report(qs)
        assert response['Content-Type'] == 'text/csv'
        assert 'rapport_heures_benevoles' in response['Content-Disposition']


class TestHoursViews:
    """Tests for hours frontend views."""

    def test_hours_log_requires_login(self):
        client = Client()
        response = client.get('/volunteers/hours/log/')
        assert response.status_code == 302

    def test_hours_log_get(self):
        user = MemberWithUserFactory(role=Roles.VOLUNTEER).user
        client = Client()
        client.force_login(user)
        response = client.get('/volunteers/hours/log/')
        assert response.status_code == 200

    def test_hours_my_summary_get(self):
        user = MemberWithUserFactory(role=Roles.VOLUNTEER).user
        client = Client()
        client.force_login(user)
        response = client.get('/volunteers/hours/my-summary/')
        assert response.status_code == 200

    def test_hours_admin_report_requires_staff(self):
        user = MemberWithUserFactory(role=Roles.MEMBER).user
        client = Client()
        client.force_login(user)
        response = client.get('/volunteers/hours/report/')
        assert response.status_code == 302  # Redirect for non-staff

    def test_hours_admin_report_for_staff(self):
        user = MemberWithUserFactory(role=Roles.PASTOR).user
        client = Client()
        client.force_login(user)
        response = client.get('/volunteers/hours/report/')
        assert response.status_code == 200

    def test_hours_log_post_self(self):
        user = MemberWithUserFactory(role=Roles.VOLUNTEER).user
        position = VolunteerPositionFactory()
        client = Client()
        client.force_login(user)
        response = client.post('/volunteers/hours/log/', {
            'position': position.pk,
            'date': timezone.now().date().isoformat(),
            'hours_worked': '3.5',
            'description': 'Test hours',
        })
        assert response.status_code == 302
        assert VolunteerHours.objects.filter(member=user.member_profile).exists()

    def test_hours_export_csv(self):
        user = MemberWithUserFactory(role=Roles.PASTOR).user
        VolunteerHoursFactory()
        client = Client()
        client.force_login(user)
        response = client.get('/volunteers/hours/report/?export=csv')
        assert response.status_code == 200
        assert response['Content-Type'] == 'text/csv'
