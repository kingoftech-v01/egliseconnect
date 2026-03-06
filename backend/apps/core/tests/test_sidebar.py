"""Tests for sidebar role-based visibility."""
import pytest
from django.test import Client

from apps.core.constants import Roles, MembershipStatus
from apps.members.tests.factories import MemberWithUserFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    return Client()


class TestSidebarRoleBased:
    """Test that sidebar items are visible/hidden based on role."""

    def test_staff_sees_admin_items(self, client):
        member = MemberWithUserFactory(role=Roles.ADMIN, membership_status=MembershipStatus.ACTIVE)
        client.force_login(member.user)
        response = client.get('/members/my-profile/')
        content = response.content.decode()
        assert 'ADMINISTRATION' in content
        assert '/onboarding/admin/pipeline/' in content
        assert '/members/background-checks/' in content
        assert '/events/create/' in content

    def test_pastor_sees_admin_items(self, client):
        member = MemberWithUserFactory(role=Roles.PASTOR, membership_status=MembershipStatus.ACTIVE)
        client.force_login(member.user)
        response = client.get('/members/my-profile/')
        content = response.content.decode()
        assert 'ADMINISTRATION' in content

    def test_deacon_sees_admin_items(self, client):
        member = MemberWithUserFactory(role=Roles.DEACON, membership_status=MembershipStatus.ACTIVE)
        client.force_login(member.user)
        response = client.get('/members/my-profile/')
        content = response.content.decode()
        assert 'ADMINISTRATION' in content

    def test_regular_member_no_admin_items(self, client):
        member = MemberWithUserFactory(role=Roles.MEMBER, membership_status=MembershipStatus.ACTIVE)
        client.force_login(member.user)
        response = client.get('/members/my-profile/')
        content = response.content.decode()
        assert 'ADMINISTRATION' not in content
        assert '/members/background-checks/' not in content
        assert '/events/create/' not in content

    def test_treasurer_sees_finance_items(self, client):
        member = MemberWithUserFactory(role=Roles.TREASURER, membership_status=MembershipStatus.ACTIVE)
        client.force_login(member.user)
        response = client.get('/members/my-profile/')
        content = response.content.decode()
        # Treasurer should see finance admin items
        assert '/donations/imports/' in content
        assert '/donations/kiosk/' in content
        assert '/payments/kiosk/' in content
        # But should NOT see general admin items
        assert 'ADMINISTRATION' not in content
        assert '/events/create/' not in content

    def test_onboarding_member_sees_parcours(self, client):
        member = MemberWithUserFactory(role=Roles.MEMBER, membership_status=MembershipStatus.REGISTERED)
        client.force_login(member.user)
        response = client.get('/onboarding/dashboard/')
        content = response.content.decode()
        assert 'MON PARCOURS' in content
        assert '/onboarding/dashboard/' in content
