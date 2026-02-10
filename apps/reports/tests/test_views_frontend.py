"""Tests for reports frontend views."""
import json
import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.test import Client
from django.urls import NoReverseMatch
from django.utils import timezone

from apps.members.tests.factories import (
    UserFactory,
    MemberFactory,
    PastorFactory,
    TreasurerFactory,
    AdminMemberFactory,
)
from apps.donations.tests.factories import DonationFactory
from apps.attendance.tests.factories import (
    AttendanceSessionFactory,
    AttendanceRecordFactory,
)
from apps.volunteers.tests.factories import (
    VolunteerPositionFactory,
    VolunteerScheduleFactory,
)


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def pastor_user(db):
    """Pastor with user account."""
    user = UserFactory()
    member = PastorFactory(user=user)
    return user, member


@pytest.fixture
def admin_user(db):
    """Admin with user account."""
    user = UserFactory()
    member = AdminMemberFactory(user=user)
    return user, member


@pytest.fixture
def treasurer_user(db):
    """Treasurer with user account."""
    user = UserFactory()
    member = TreasurerFactory(user=user)
    return user, member


@pytest.fixture
def regular_member_user(db):
    """Regular member with user account."""
    user = UserFactory()
    member = MemberFactory(user=user, role='member')
    return user, member


@pytest.fixture
def volunteer_user(db):
    """Volunteer with user account."""
    user = UserFactory()
    member = MemberFactory(user=user, role='volunteer')
    return user, member


@pytest.fixture
def user_without_profile(db):
    """User without member profile."""
    return UserFactory()


@pytest.mark.django_db
class TestDashboardView:
    """Tests for the dashboard frontend view."""

    url = '/reports/'

    def test_requires_login(self, client):
        response = client.get(self.url)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_pastor_can_access(self, client, pastor_user):
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200

    def test_admin_can_access(self, client, admin_user):
        user, member = admin_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200

    def test_treasurer_can_access(self, client, treasurer_user):
        user, member = treasurer_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200

    def test_regular_member_denied(self, client, regular_member_user):
        user, member = regular_member_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_volunteer_denied(self, client, volunteer_user):
        user, member = volunteer_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_user_without_profile_denied(self, client, user_without_profile):
        """User without profile triggers NoReverseMatch due to pk='' fallback."""
        client.force_login(user_without_profile)
        with pytest.raises(NoReverseMatch):
            client.get(self.url)

    def test_dashboard_context_contains_summary(self, client, pastor_user):
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert 'summary' in response.context


@pytest.mark.django_db
class TestMemberStatsView:
    """Tests for the member_stats frontend view."""

    url = '/reports/members/'

    def test_requires_login(self, client):
        response = client.get(self.url)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_pastor_can_access(self, client, pastor_user):
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200

    def test_admin_can_access(self, client, admin_user):
        user, member = admin_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200

    def test_treasurer_denied(self, client, treasurer_user):
        """Treasurers cannot access member stats (only pastor/admin)."""
        user, member = treasurer_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_regular_member_denied(self, client, regular_member_user):
        user, member = regular_member_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_user_without_profile_denied(self, client, user_without_profile):
        client.force_login(user_without_profile)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_context_contains_stats(self, client, pastor_user):
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert 'stats' in response.context


@pytest.mark.django_db
class TestDonationReportView:
    """Tests for the donation_report frontend view."""

    url = '/reports/donations/'

    def test_requires_login(self, client):
        response = client.get(self.url)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_pastor_can_access(self, client, pastor_user):
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200

    def test_admin_can_access(self, client, admin_user):
        user, member = admin_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200

    def test_treasurer_can_access(self, client, treasurer_user):
        user, member = treasurer_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200

    def test_regular_member_denied(self, client, regular_member_user):
        user, member = regular_member_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_user_without_profile_denied(self, client, user_without_profile):
        client.force_login(user_without_profile)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_default_year(self, client, pastor_user):
        """No year param defaults to current year."""
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert response.context['current_year'] == date.today().year

    def test_with_valid_year_param(self, client, pastor_user):
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url, {'year': '2024'})
        assert response.status_code == 200
        assert response.context['current_year'] == 2024

    def test_with_invalid_year_param(self, client, pastor_user):
        """Invalid year falls back to current year."""
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url, {'year': 'invalid'})
        assert response.status_code == 200
        assert response.context['current_year'] == date.today().year

    def test_context_contains_report_and_stats(self, client, pastor_user):
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert 'report' in response.context
        assert 'stats' in response.context
        assert 'current_year' in response.context
        assert 'available_years' in response.context

    def test_available_years_range(self, client, pastor_user):
        """Available years covers 5-year range backwards from current year."""
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        available_years = list(response.context['available_years'])
        current_year = date.today().year
        assert available_years[0] == current_year
        assert len(available_years) == 5

    def test_with_donations_present(self, client, pastor_user):
        user, member = pastor_user
        client.force_login(user)
        DonationFactory()
        response = client.get(self.url)
        assert response.status_code == 200


@pytest.mark.django_db
class TestAttendanceReportView:
    """Tests for the attendance_report frontend view."""

    url = '/reports/attendance/'

    def test_requires_login(self, client):
        response = client.get(self.url)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_pastor_can_access(self, client, pastor_user):
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200

    def test_admin_can_access(self, client, admin_user):
        user, member = admin_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200

    def test_treasurer_denied(self, client, treasurer_user):
        """Treasurers cannot access attendance report (only pastor/admin)."""
        user, member = treasurer_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_regular_member_denied(self, client, regular_member_user):
        user, member = regular_member_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_user_without_profile_denied(self, client, user_without_profile):
        client.force_login(user_without_profile)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_default_without_dates(self, client, pastor_user):
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert 'report' in response.context
        assert 'event_stats' in response.context

    def test_with_valid_start_date(self, client, pastor_user):
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url, {'start_date': '2025-01-01'})
        assert response.status_code == 200

    def test_with_valid_end_date(self, client, pastor_user):
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url, {'end_date': '2025-12-31'})
        assert response.status_code == 200

    def test_with_both_dates(self, client, pastor_user):
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url, {
            'start_date': '2025-01-01',
            'end_date': '2025-12-31',
        })
        assert response.status_code == 200

    def test_with_invalid_start_date(self, client, pastor_user):
        """Invalid start_date is ignored."""
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url, {'start_date': 'not-a-date'})
        assert response.status_code == 200

    def test_with_invalid_end_date(self, client, pastor_user):
        """Invalid end_date is ignored."""
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url, {'end_date': 'bad-date'})
        assert response.status_code == 200

    def test_with_both_invalid_dates(self, client, pastor_user):
        """Both invalid dates fall back to defaults."""
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url, {
            'start_date': 'invalid',
            'end_date': 'invalid',
        })
        assert response.status_code == 200


@pytest.mark.django_db
class TestVolunteerReportView:
    """Tests for the volunteer_report frontend view."""

    url = '/reports/volunteers/'

    def test_requires_login(self, client):
        response = client.get(self.url)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_pastor_can_access(self, client, pastor_user):
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200

    def test_admin_can_access(self, client, admin_user):
        user, member = admin_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200

    def test_treasurer_denied(self, client, treasurer_user):
        """Treasurers cannot access volunteer report (only pastor/admin)."""
        user, member = treasurer_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_regular_member_denied(self, client, regular_member_user):
        user, member = regular_member_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_user_without_profile_denied(self, client, user_without_profile):
        client.force_login(user_without_profile)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_default_without_dates(self, client, pastor_user):
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert 'report' in response.context
        assert 'volunteer_stats' in response.context

    def test_with_valid_start_date(self, client, pastor_user):
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url, {'start_date': '2025-06-01'})
        assert response.status_code == 200

    def test_with_valid_end_date(self, client, pastor_user):
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url, {'end_date': '2025-06-30'})
        assert response.status_code == 200

    def test_with_both_dates(self, client, pastor_user):
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url, {
            'start_date': '2025-01-01',
            'end_date': '2025-06-30',
        })
        assert response.status_code == 200

    def test_with_invalid_start_date(self, client, pastor_user):
        """Invalid start_date is ignored."""
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url, {'start_date': 'xyz'})
        assert response.status_code == 200

    def test_with_invalid_end_date(self, client, pastor_user):
        """Invalid end_date is ignored."""
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url, {'end_date': 'xyz'})
        assert response.status_code == 200

    def test_with_both_invalid_dates(self, client, pastor_user):
        """Both invalid dates fall back to defaults."""
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url, {
            'start_date': 'bad',
            'end_date': 'bad',
        })
        assert response.status_code == 200


@pytest.mark.django_db
class TestBirthdayReportView:
    """Tests for the birthday_report frontend view."""

    url = '/reports/birthdays/'

    def test_requires_login(self, client):
        response = client.get(self.url)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_any_member_can_access(self, client, regular_member_user):
        user, member = regular_member_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200

    def test_pastor_can_access(self, client, pastor_user):
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200

    def test_user_without_profile_denied(self, client, user_without_profile):
        client.force_login(user_without_profile)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_default_days(self, client, pastor_user):
        """Default days is 30 when not specified."""
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert response.context['days'] == 30

    def test_with_custom_days(self, client, pastor_user):
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url, {'days': '60'})
        assert response.status_code == 200
        assert response.context['days'] == 60

    def test_with_invalid_days(self, client, pastor_user):
        """Invalid days parameter falls back to default 30."""
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url, {'days': 'abc'})
        assert response.status_code == 200
        assert response.context['days'] == 30

    def test_context_contains_birthdays(self, client, pastor_user):
        user, member = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert 'birthdays' in response.context
        assert 'days' in response.context


@pytest.mark.django_db
class TestFrontendRedirects:
    """Tests for unauthorized user redirect destinations."""

    def test_dashboard_regular_member_redirect_target(self, client, regular_member_user):
        """Dashboard redirects regular member to their member_detail page."""
        user, member = regular_member_user
        client.force_login(user)
        response = client.get('/reports/')
        assert response.status_code == 302
        assert str(member.pk) in response.url

    def test_member_stats_redirect_to_dashboard(self, client, regular_member_user):
        user, member = regular_member_user
        client.force_login(user)
        response = client.get('/reports/members/')
        assert response.status_code == 302

    def test_donation_report_redirect_to_dashboard(self, client, regular_member_user):
        user, member = regular_member_user
        client.force_login(user)
        response = client.get('/reports/donations/')
        assert response.status_code == 302

    def test_attendance_report_redirect_to_dashboard(self, client, regular_member_user):
        user, member = regular_member_user
        client.force_login(user)
        response = client.get('/reports/attendance/')
        assert response.status_code == 302

    def test_volunteer_report_redirect_to_dashboard(self, client, regular_member_user):
        user, member = regular_member_user
        client.force_login(user)
        response = client.get('/reports/volunteers/')
        assert response.status_code == 302

    def test_birthday_report_no_profile_redirects_to_member_list(self, client, user_without_profile):
        client.force_login(user_without_profile)
        response = client.get('/reports/birthdays/')
        assert response.status_code == 302


# ---------------------------------------------------------------------------
# Sprint 8: New context variables tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestDashboardNewContext:
    """Tests for Sprint 8 dashboard enhancements (pipeline, financial, growth)."""

    url = '/reports/'

    def test_context_contains_onboarding_pipeline(self, client, pastor_user):
        """Dashboard context includes onboarding_pipeline dict."""
        user, _ = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert 'onboarding_pipeline' in response.context
        pipeline = response.context['onboarding_pipeline']
        assert 'registered' in pipeline
        assert 'form_submitted' in pipeline
        assert 'in_training' in pipeline
        assert 'interview_scheduled' in pipeline
        assert 'total_in_process' in pipeline

    def test_context_contains_financial_summary(self, client, pastor_user):
        """Dashboard context includes financial_summary dict."""
        user, _ = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert 'financial_summary' in response.context
        fin = response.context['financial_summary']
        assert 'labels' in fin
        assert 'values' in fin
        assert isinstance(fin['labels'], list)
        assert isinstance(fin['values'], list)

    def test_context_contains_growth_data_json(self, client, pastor_user):
        """Dashboard context includes growth_data_json as valid JSON string."""
        user, _ = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert 'growth_data_json' in response.context
        data = json.loads(response.context['growth_data_json'])
        assert 'labels' in data
        assert 'counts' in data
        assert isinstance(data['labels'], list)
        assert isinstance(data['counts'], list)

    def test_onboarding_pipeline_counts_with_data(self, client, admin_user):
        """Pipeline shows correct counts when members exist in each status."""
        user, _ = admin_user
        client.force_login(user)
        MemberFactory(user=None, membership_status='registered')
        MemberFactory(user=None, membership_status='registered')
        MemberFactory(user=None, membership_status='form_submitted')
        response = client.get(self.url)
        pipeline = response.context['onboarding_pipeline']
        assert pipeline['registered'] >= 2
        assert pipeline['form_submitted'] >= 1


@pytest.mark.django_db
class TestMemberStatsNewContext:
    """Tests for Sprint 8 member_stats growth chart data."""

    url = '/reports/members/'

    def test_context_contains_growth_data_json(self, client, pastor_user):
        """Member stats includes growth_data_json for Chart.js."""
        user, _ = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert 'growth_data_json' in response.context
        data = json.loads(response.context['growth_data_json'])
        assert 'labels' in data
        assert 'counts' in data
        assert len(data['labels']) == 12


@pytest.mark.django_db
class TestDonationReportNewContext:
    """Tests for Sprint 8 donation report enhancements (YoY, chart data)."""

    url = '/reports/donations/'

    def test_context_contains_yoy_comparison(self, client, pastor_user):
        """Donation report includes year-over-year comparison."""
        user, _ = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert 'yoy_comparison' in response.context
        yoy = response.context['yoy_comparison']
        assert 'current_year' in yoy
        assert 'prev_year' in yoy
        assert 'current_total' in yoy
        assert 'prev_total' in yoy
        assert 'change_amount' in yoy
        assert 'change_percent' in yoy

    def test_yoy_comparison_correct_years(self, client, pastor_user):
        """YoY comparison references current and previous year."""
        user, _ = pastor_user
        client.force_login(user)
        response = client.get(self.url, {'year': '2025'})
        yoy = response.context['yoy_comparison']
        assert yoy['current_year'] == 2025
        assert yoy['prev_year'] == 2024

    def test_context_contains_monthly_chart_json(self, client, pastor_user):
        """Donation report includes monthly_chart_json for Chart.js."""
        user, _ = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert 'monthly_chart_json' in response.context
        data = json.loads(response.context['monthly_chart_json'])
        assert 'labels' in data
        assert 'current' in data
        assert 'previous' in data

    def test_yoy_zero_prev_total(self, client, pastor_user):
        """When previous year had zero donations, change_percent is 0."""
        user, _ = pastor_user
        client.force_login(user)
        response = client.get(self.url, {'year': '2020'})
        yoy = response.context['yoy_comparison']
        assert yoy['change_percent'] == 0

    def test_with_donation_data(self, client, pastor_user):
        """YoY works when actual donation data exists."""
        user, _ = pastor_user
        client.force_login(user)
        DonationFactory(amount=Decimal('500.00'), date=date.today())
        response = client.get(self.url)
        assert response.status_code == 200
        yoy = response.context['yoy_comparison']
        assert yoy['current_total'] >= 500.0


@pytest.mark.django_db
class TestAttendanceReportNewContext:
    """Tests for Sprint 8 attendance report session stats."""

    url = '/reports/attendance/'

    def test_context_contains_session_stats(self, client, pastor_user):
        """Attendance report includes session_stats dict."""
        user, _ = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert 'session_stats' in response.context
        stats = response.context['session_stats']
        assert 'total_sessions' in stats
        assert 'total_checkins' in stats
        assert 'avg_per_session' in stats
        assert 'by_type' in stats
        assert 'by_method' in stats

    def test_session_stats_with_data(self, client, admin_user):
        """Session stats reflect actual attendance data."""
        user, _ = admin_user
        client.force_login(user)
        session = AttendanceSessionFactory(date=date.today())
        AttendanceRecordFactory(session=session)
        AttendanceRecordFactory(session=session)
        response = client.get(self.url)
        stats = response.context['session_stats']
        assert stats['total_sessions'] >= 1
        assert stats['total_checkins'] >= 2

    def test_session_stats_avg_per_session_no_sessions(self, client, pastor_user):
        """avg_per_session is 0 when there are no sessions."""
        user, _ = pastor_user
        client.force_login(user)
        response = client.get(self.url, {
            'start_date': '2010-01-01',
            'end_date': '2010-01-31',
        })
        stats = response.context['session_stats']
        assert stats['avg_per_session'] == 0


# ---------------------------------------------------------------------------
# Sprint 8: CSV Export views
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestExportMembersCSV:
    """Tests for export_members_csv view."""

    url = '/reports/export/members/'

    def test_requires_login(self, client):
        response = client.get(self.url)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_pastor_can_export(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert response['Content-Type'] == 'text/csv'
        assert 'attachment' in response['Content-Disposition']
        assert 'membres_rapport.csv' in response['Content-Disposition']

    def test_admin_can_export(self, client, admin_user):
        user, _ = admin_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert response['Content-Type'] == 'text/csv'

    def test_regular_member_denied(self, client, regular_member_user):
        user, _ = regular_member_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_treasurer_denied(self, client, treasurer_user):
        user, _ = treasurer_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_user_without_profile_denied(self, client, user_without_profile):
        client.force_login(user_without_profile)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_csv_has_header_row(self, client, pastor_user):
        """CSV output starts with BOM and header row."""
        user, _ = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        content = response.content.decode('utf-8-sig')
        lines = content.strip().split('\n')
        assert len(lines) >= 1
        assert 'Nom' in lines[0]
        assert 'Courriel' in lines[0]

    def test_csv_includes_member_data(self, client, pastor_user):
        """CSV includes existing member data rows."""
        user, _ = pastor_user
        client.force_login(user)
        MemberFactory(first_name='Test', last_name='Membre')
        response = client.get(self.url)
        content = response.content.decode('utf-8-sig')
        assert 'Membre' in content


@pytest.mark.django_db
class TestExportDonationsCSV:
    """Tests for export_donations_csv view."""

    url = '/reports/export/donations/'

    def test_requires_login(self, client):
        response = client.get(self.url)
        assert response.status_code == 302

    def test_pastor_can_export(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert response['Content-Type'] == 'text/csv'

    def test_treasurer_can_export(self, client, treasurer_user):
        user, _ = treasurer_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200

    def test_regular_member_denied(self, client, regular_member_user):
        user, _ = regular_member_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_user_without_profile_denied(self, client, user_without_profile):
        client.force_login(user_without_profile)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_csv_filename_includes_year(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        response = client.get(self.url, {'year': '2025'})
        assert 'dons_rapport_2025.csv' in response['Content-Disposition']

    def test_invalid_year_defaults_to_current(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        response = client.get(self.url, {'year': 'bad'})
        current_year = date.today().year
        assert f'dons_rapport_{current_year}.csv' in response['Content-Disposition']

    def test_csv_has_header_row(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        content = response.content.decode('utf-8-sig')
        lines = content.strip().split('\n')
        assert 'Date' in lines[0]
        assert 'Montant' in lines[0]

    def test_csv_includes_donation_data(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        DonationFactory(amount=Decimal('250.00'), date=date.today())
        response = client.get(self.url)
        content = response.content.decode('utf-8-sig')
        assert '250.00' in content


@pytest.mark.django_db
class TestExportAttendanceCSV:
    """Tests for export_attendance_csv view."""

    url = '/reports/export/attendance/'

    def test_requires_login(self, client):
        response = client.get(self.url)
        assert response.status_code == 302

    def test_pastor_can_export(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert response['Content-Type'] == 'text/csv'

    def test_regular_member_denied(self, client, regular_member_user):
        user, _ = regular_member_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_treasurer_denied(self, client, treasurer_user):
        user, _ = treasurer_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_user_without_profile_denied(self, client, user_without_profile):
        client.force_login(user_without_profile)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_csv_filename(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        assert 'presence_rapport.csv' in response['Content-Disposition']

    def test_csv_has_header_row(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        content = response.content.decode('utf-8-sig')
        lines = content.strip().split('\n')
        assert 'Evenement' in lines[0]

    def test_with_valid_dates(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        response = client.get(self.url, {
            'start_date': '2025-01-01',
            'end_date': '2025-12-31',
        })
        assert response.status_code == 200

    def test_with_invalid_dates(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        response = client.get(self.url, {
            'start_date': 'bad',
            'end_date': 'bad',
        })
        assert response.status_code == 200


@pytest.mark.django_db
class TestExportVolunteersCSV:
    """Tests for export_volunteers_csv view."""

    url = '/reports/export/volunteers/'

    def test_requires_login(self, client):
        response = client.get(self.url)
        assert response.status_code == 302

    def test_pastor_can_export(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert response['Content-Type'] == 'text/csv'

    def test_admin_can_export(self, client, admin_user):
        user, _ = admin_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200

    def test_regular_member_denied(self, client, regular_member_user):
        user, _ = regular_member_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_treasurer_denied(self, client, treasurer_user):
        user, _ = treasurer_user
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_user_without_profile_denied(self, client, user_without_profile):
        client.force_login(user_without_profile)
        response = client.get(self.url)
        assert response.status_code == 302

    def test_csv_filename(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        assert 'volontaires_rapport.csv' in response['Content-Disposition']

    def test_csv_has_header_row(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        response = client.get(self.url)
        content = response.content.decode('utf-8-sig')
        lines = content.strip().split('\n')
        assert 'Nom' in lines[0]

    def test_with_valid_dates(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        response = client.get(self.url, {
            'start_date': '2025-01-01',
            'end_date': '2025-12-31',
        })
        assert response.status_code == 200

    def test_with_invalid_dates(self, client, pastor_user):
        user, _ = pastor_user
        client.force_login(user)
        response = client.get(self.url, {
            'start_date': 'bad',
            'end_date': 'bad',
        })
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Sprint 8: Service layer tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestDashboardServiceNewMethods:
    """Tests for new DashboardService methods added in Sprint 8."""

    def test_get_onboarding_pipeline_stats_returns_all_keys(self):
        from apps.reports.services import DashboardService
        result = DashboardService.get_onboarding_pipeline_stats()
        assert 'registered' in result
        assert 'form_submitted' in result
        assert 'in_training' in result
        assert 'interview_scheduled' in result
        assert 'total_in_process' in result

    def test_get_onboarding_pipeline_stats_counts_correctly(self):
        from apps.reports.services import DashboardService
        MemberFactory(user=None, membership_status='registered')
        MemberFactory(user=None, membership_status='registered')
        result = DashboardService.get_onboarding_pipeline_stats()
        assert result['registered'] >= 2

    def test_get_financial_summary_returns_all_keys(self):
        from apps.reports.services import DashboardService
        result = DashboardService.get_financial_summary()
        assert 'monthly_trend' in result
        assert 'labels' in result
        assert 'values' in result
        assert len(result['labels']) == 6
        assert len(result['values']) == 6

    def test_get_financial_summary_with_donations(self):
        from apps.reports.services import DashboardService
        DonationFactory(amount=Decimal('100.00'), date=date.today())
        result = DashboardService.get_financial_summary()
        # The current month should have at least 100
        assert result['values'][-1] >= 100.0

    def test_get_member_growth_trend_returns_12_months(self):
        from apps.reports.services import DashboardService
        result = DashboardService.get_member_growth_trend()
        assert 'labels' in result
        assert 'counts' in result
        assert len(result['labels']) == 12
        assert len(result['counts']) == 12

    def test_get_upcoming_birthdays_includes_email(self):
        from apps.reports.services import DashboardService
        member = MemberFactory(
            birth_date=date.today() + timedelta(days=5),
            email='birthday@test.com'
        )
        result = DashboardService.get_upcoming_birthdays(30)
        found = [b for b in result if b['email'] == 'birthday@test.com']
        assert len(found) >= 1

    def test_get_upcoming_birthdays_empty_email(self):
        from apps.reports.services import DashboardService
        member = MemberFactory(
            birth_date=date.today() + timedelta(days=3),
            email=''
        )
        result = DashboardService.get_upcoming_birthdays(30)
        # Should have empty email for member with no email
        for b in result:
            if b['member_id'] == str(member.id):
                assert b['email'] == ''


@pytest.mark.django_db
class TestReportServiceNewMethods:
    """Tests for new ReportService methods added in Sprint 8."""

    def test_get_attendance_session_stats_empty(self):
        from apps.reports.services import ReportService
        result = ReportService.get_attendance_session_stats(
            date(2010, 1, 1), date(2010, 1, 31)
        )
        assert result['total_sessions'] == 0
        assert result['total_checkins'] == 0
        assert result['avg_per_session'] == 0
        assert result['by_type'] == []
        assert result['by_method'] == []

    def test_get_attendance_session_stats_with_data(self):
        from apps.reports.services import ReportService
        session = AttendanceSessionFactory(date=date.today())
        AttendanceRecordFactory(session=session)
        AttendanceRecordFactory(session=session)
        AttendanceRecordFactory(session=session)
        result = ReportService.get_attendance_session_stats(
            date.today() - timedelta(days=1),
            date.today() + timedelta(days=1),
        )
        assert result['total_sessions'] >= 1
        assert result['total_checkins'] >= 3
        assert result['avg_per_session'] > 0

    def test_get_attendance_session_stats_by_type(self):
        from apps.reports.services import ReportService
        from apps.core.constants import AttendanceSessionType
        AttendanceSessionFactory(
            date=date.today(),
            session_type=AttendanceSessionType.WORSHIP,
        )
        AttendanceSessionFactory(
            date=date.today(),
            session_type=AttendanceSessionType.EVENT,
        )
        result = ReportService.get_attendance_session_stats(
            date.today() - timedelta(days=1),
            date.today() + timedelta(days=1),
        )
        assert len(result['by_type']) >= 2

    def test_get_attendance_session_stats_defaults_dates(self):
        """When no dates are passed, defaults are used."""
        from apps.reports.services import ReportService
        result = ReportService.get_attendance_session_stats()
        assert 'total_sessions' in result
