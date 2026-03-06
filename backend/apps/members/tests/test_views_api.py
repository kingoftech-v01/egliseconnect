"""Tests for members API views."""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.members.models import Member, Group, DirectoryPrivacy

from .factories import (
    MemberFactory,
    MemberWithUserFactory,
    UserFactory,
    FamilyFactory,
    GroupFactory,
    PastorFactory,
    AdminMemberFactory,
)


@pytest.fixture
def api_client():
    """API client for making requests."""
    return APIClient()


@pytest.fixture
def authenticated_member(api_client):
    """Regular member with authentication."""
    member = MemberWithUserFactory()
    api_client.force_authenticate(user=member.user)
    return member


@pytest.fixture
def authenticated_pastor(api_client):
    """Pastor with authentication."""
    user = UserFactory()
    member = PastorFactory(user=user)
    api_client.force_authenticate(user=user)
    return member


@pytest.fixture
def authenticated_admin(api_client):
    """Admin with authentication."""
    user = UserFactory()
    member = AdminMemberFactory(user=user)
    api_client.force_authenticate(user=user)
    return member


@pytest.mark.django_db
class TestMemberViewSet:
    """Tests for MemberViewSet."""

    def test_list_members_as_pastor(self, api_client, authenticated_pastor):
        """Pastors can list all members."""
        MemberFactory.create_batch(5)

        url = '/api/v1/members/members/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 5

    def test_list_members_as_regular_member(self, api_client, authenticated_member):
        """Regular members only see themselves."""
        MemberFactory.create_batch(5)

        url = '/api/v1/members/members/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1

    def test_retrieve_own_profile(self, api_client, authenticated_member):
        """Members can retrieve their own profile."""
        url = f'/api/v1/members/members/{authenticated_member.id}/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(authenticated_member.id)

    def test_me_endpoint(self, api_client, authenticated_member):
        """/me/ endpoint returns current user's profile."""
        url = '/api/v1/members/members/me/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(authenticated_member.id)

    def test_update_own_profile(self, api_client, authenticated_member):
        """Members can update their own profile."""
        url = f'/api/v1/members/members/{authenticated_member.id}/'
        data = {'first_name': 'Updated'}
        response = api_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK

        authenticated_member.refresh_from_db()
        assert authenticated_member.first_name == 'Updated'

    def test_create_member_public(self, api_client):
        """Member creation is public for registration."""
        url = '/api/v1/members/members/'
        data = {
            'first_name': 'New',
            'last_name': 'Member',
            'email': 'new@example.com',
            'phone': '514-555-0123',
        }
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert Member.objects.filter(email='new@example.com').exists()

    def test_delete_requires_staff(self, api_client, authenticated_member):
        """Only staff can delete members."""
        other_member = MemberFactory()

        url = f'/api/v1/members/members/{other_member.id}/'
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_as_pastor(self, api_client, authenticated_pastor):
        """Pastors can delete members."""
        member = MemberFactory()

        url = f'/api/v1/members/members/{member.id}/'
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_search_members(self, api_client, authenticated_pastor):
        """Search filters by name."""
        MemberFactory(first_name='Jean', last_name='Dupont')
        MemberFactory(first_name='Marie', last_name='Martin')

        url = '/api/v1/members/members/?search=Dupont'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1

    def test_filter_by_role(self, api_client, authenticated_pastor):
        """Filter by role works."""
        MemberFactory.create_batch(3)

        url = '/api/v1/members/members/?role=pastor'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 1


@pytest.mark.django_db
class TestBirthdayEndpoint:
    """Tests for birthday endpoint."""

    def test_birthdays_today(self, api_client, authenticated_member):
        """Birthdays today endpoint works."""
        url = '/api/v1/members/members/birthdays/?period=today'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_birthdays_week(self, api_client, authenticated_member):
        """Birthdays this week endpoint works."""
        url = '/api/v1/members/members/birthdays/?period=week'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_birthdays_month(self, api_client, authenticated_member):
        """Birthdays this month endpoint works."""
        url = '/api/v1/members/members/birthdays/?period=month&month=6'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestDirectoryEndpoint:
    """Tests for directory endpoint."""

    def test_directory_respects_privacy(self, api_client, authenticated_member):
        """Directory hides private members from regular members."""
        private_member = MemberFactory()
        DirectoryPrivacy.objects.filter(member=private_member).update(visibility='private')

        url = '/api/v1/members/members/directory/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        ids = [item['id'] for item in response.data['results']]
        assert str(private_member.id) not in ids

    def test_directory_search(self, api_client, authenticated_member):
        """Directory search works."""
        MemberFactory(first_name='Searchable', last_name='User')

        url = '/api/v1/members/members/directory/?search=Searchable'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestGroupViewSet:
    """Tests for GroupViewSet."""

    def test_list_groups(self, api_client, authenticated_member):
        """List groups works."""
        GroupFactory.create_batch(3)

        url = '/api/v1/members/groups/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 3

    def test_retrieve_group(self, api_client, authenticated_member):
        """Retrieve single group works."""
        group = GroupFactory()

        url = f'/api/v1/members/groups/{group.id}/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == group.name

    def test_create_group_requires_staff(self, api_client, authenticated_member):
        """Creating groups requires staff role."""
        url = '/api/v1/members/groups/'
        data = {'name': 'New Group', 'group_type': 'cell'}
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_group_as_pastor(self, api_client, authenticated_pastor):
        """Pastors can create groups."""
        url = '/api/v1/members/groups/'
        data = {'name': 'New Group', 'group_type': 'cell'}
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
class TestFamilyViewSet:
    """Tests for FamilyViewSet."""

    def test_list_families(self, api_client, authenticated_member):
        """List families works."""
        FamilyFactory.create_batch(3)

        url = '/api/v1/members/families/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 3

    def test_create_family_requires_staff(self, api_client, authenticated_member):
        """Creating families requires staff role."""
        url = '/api/v1/members/families/'
        data = {'name': 'New Family'}
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestMemberViewSetAdminAccess:
    """Tests using authenticated_admin fixture (covers test fixture lines 46-49)."""

    def test_admin_can_list_all_members(self, api_client, authenticated_admin):
        """Admin can list all members."""
        MemberFactory.create_batch(3)
        url = '/api/v1/members/members/'
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 3

    def test_admin_can_delete_member(self, api_client, authenticated_admin):
        """Admin can delete a member."""
        member = MemberFactory()
        url = f'/api/v1/members/members/{member.id}/'
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
class TestDirectoryPrivacyMissedLines:
    """Tests covering missed lines in DirectoryPrivacyViewSet (views_api.py lines 360-361)."""

    def test_privacy_me_auto_creates_when_missing(self, api_client):
        """DirectoryPrivacyViewSet.me creates privacy settings if missing (lines 360-361)."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        member = MemberWithUserFactory()
        user_pk = member.user.pk
        # Delete the auto-created privacy settings
        DirectoryPrivacy.objects.filter(member=member).delete()
        # Verify privacy is gone
        assert not DirectoryPrivacy.objects.filter(member=member).exists()
        # Re-fetch user from DB to clear cached reverse relations
        fresh_user = User.objects.get(pk=user_pk)
        api_client.force_authenticate(user=fresh_user)
        # GET me/ should auto-create privacy settings
        url = '/api/v1/members/privacy/me/'
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert DirectoryPrivacy.objects.filter(member=member).exists()
