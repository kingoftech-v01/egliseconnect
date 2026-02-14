"""Tests for pastoral care models and views."""
import pytest
from datetime import timedelta
from django.test import RequestFactory
from django.utils import timezone

from apps.core.constants import CareStatus, CareType
from apps.help_requests.models import PastoralCare, CareTeam, CareTeamMember
from apps.members.tests.factories import MemberFactory, MemberWithUserFactory, PastorFactory
from .factories import (
    PastoralCareFactory, CareTeamFactory, CareTeamMemberFactory,
)


@pytest.mark.django_db
class TestPastoralCareModel:
    """Tests for PastoralCare model."""

    def test_create_pastoral_care(self):
        care = PastoralCareFactory(care_type=CareType.HOME_VISIT)
        assert care.care_type == CareType.HOME_VISIT
        assert care.status == CareStatus.OPEN
        assert care.member is not None

    def test_pastoral_care_str(self):
        care = PastoralCareFactory(care_type=CareType.HOSPITAL_VISIT)
        assert "hôpital" in str(care).lower() or "hospital" in str(care).lower() or str(care.member) in str(care)

    def test_care_types(self):
        for care_type, _ in CareType.CHOICES:
            care = PastoralCareFactory(care_type=care_type)
            assert care.care_type == care_type

    def test_care_with_follow_up(self):
        follow_up = (timezone.now() + timedelta(days=7)).date()
        care = PastoralCareFactory(follow_up_date=follow_up)
        assert care.follow_up_date == follow_up

    def test_care_status_transitions(self):
        care = PastoralCareFactory(status=CareStatus.OPEN)
        care.status = CareStatus.FOLLOW_UP
        care.save()
        care.refresh_from_db()
        assert care.status == CareStatus.FOLLOW_UP

        care.status = CareStatus.CLOSED
        care.save()
        care.refresh_from_db()
        assert care.status == CareStatus.CLOSED


@pytest.mark.django_db
class TestCareTeamModel:
    """Tests for CareTeam and CareTeamMember models."""

    def test_create_care_team(self):
        team = CareTeamFactory(name='Prayer Warriors')
        assert team.name == 'Prayer Warriors'
        assert team.leader is not None

    def test_care_team_str(self):
        team = CareTeamFactory(name='Visitation Team')
        assert str(team) == 'Visitation Team'

    def test_add_member_to_team(self):
        team = CareTeamFactory()
        member = MemberFactory()
        membership = CareTeamMemberFactory(team=team, member=member)
        assert membership.team == team
        assert membership.member == member
        assert team.memberships.count() == 1

    def test_care_team_member_str(self):
        membership = CareTeamMemberFactory()
        assert str(membership.team) in str(membership)

    def test_unique_together_team_member(self):
        team = CareTeamFactory()
        member = MemberFactory()
        CareTeamMemberFactory(team=team, member=member)
        with pytest.raises(Exception):
            CareTeamMemberFactory(team=team, member=member)


@pytest.mark.django_db
class TestCareDashboardView:
    """Tests for the care dashboard frontend view."""

    def test_dashboard_requires_pastor(self, client):
        member = MemberWithUserFactory(role='member')
        client.force_login(member.user)
        response = client.get('/help-requests/care/')
        assert response.status_code == 302

    def test_dashboard_accessible_by_pastor(self, client):
        pastor = MemberWithUserFactory(role='pastor')
        client.force_login(pastor.user)
        response = client.get('/help-requests/care/')
        assert response.status_code == 200

    def test_dashboard_shows_open_cases(self, client):
        pastor = MemberWithUserFactory(role='pastor')
        client.force_login(pastor.user)
        PastoralCareFactory(status=CareStatus.OPEN)
        response = client.get('/help-requests/care/')
        assert response.status_code == 200


@pytest.mark.django_db
class TestCareCreateView:
    """Tests for creating pastoral care records."""

    def test_care_create_requires_pastor(self, client):
        member = MemberWithUserFactory(role='member')
        client.force_login(member.user)
        response = client.get('/help-requests/care/create/')
        assert response.status_code == 302

    def test_care_create_get(self, client):
        pastor = MemberWithUserFactory(role='pastor')
        client.force_login(pastor.user)
        response = client.get('/help-requests/care/create/')
        assert response.status_code == 200

    def test_care_create_post(self, client):
        pastor = MemberWithUserFactory(role='pastor')
        target = MemberFactory()
        client.force_login(pastor.user)
        response = client.post('/help-requests/care/create/', {
            'care_type': CareType.HOME_VISIT,
            'member': str(target.pk),
            'assigned_to': str(pastor.pk),
            'date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'notes': 'Test visit notes',
            'status': CareStatus.OPEN,
        })
        assert response.status_code == 302
        assert PastoralCare.objects.filter(member=target).exists()


@pytest.mark.django_db
class TestCareUpdateView:
    """Tests for updating pastoral care records."""

    def test_care_update_get(self, client):
        pastor = MemberWithUserFactory(role='pastor')
        client.force_login(pastor.user)
        care = PastoralCareFactory()
        response = client.get(f'/help-requests/care/{care.pk}/update/')
        assert response.status_code == 200

    def test_care_update_post(self, client):
        pastor = MemberWithUserFactory(role='pastor')
        client.force_login(pastor.user)
        care = PastoralCareFactory()
        response = client.post(f'/help-requests/care/{care.pk}/update/', {
            'notes': 'Updated notes',
            'status': CareStatus.FOLLOW_UP,
        })
        assert response.status_code == 302
        care.refresh_from_db()
        assert care.notes == 'Updated notes'
        assert care.status == CareStatus.FOLLOW_UP
