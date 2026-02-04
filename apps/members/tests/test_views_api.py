"""
Tests for members API views.
"""
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
    """Return an API client."""
    return APIClient()


@pytest.fixture
def authenticated_member(api_client):
    """Return an authenticated regular member."""
    member = MemberWithUserFactory()
    api_client.force_authenticate(user=member.user)
    return member


@pytest.fixture
def authenticated_pastor(api_client):
    """Return an authenticated pastor."""
    user = UserFactory()
    member = PastorFactory(user=user)
    api_client.force_authenticate(user=user)
    return member


@pytest.fixture
def authenticated_admin(api_client):
    """Return an authenticated admin."""
    user = UserFactory()
    member = AdminMemberFactory(user=user)
    api_client.force_authenticate(user=user)
    return member


@pytest.mark.django_db
class TestMemberViewSet:
    """Tests for MemberViewSet."""

    def test_list_members_as_pastor(self, api_client, authenticated_pastor):
        """Test that pastors can list all members."""
        # Create some members
        MemberFactory.create_batch(5)

        url = '/api/v1/members/members/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # 5 created + 1 pastor
        assert response.data['count'] >= 5

    def test_list_members_as_regular_member(self, api_client, authenticated_member):
        """Test that regular members only see themselves."""
        MemberFactory.create_batch(5)

        url = '/api/v1/members/members/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1  # Only themselves

    def test_retrieve_own_profile(self, api_client, authenticated_member):
        """Test member can retrieve their own profile."""
        url = f'/api/v1/members/members/{authenticated_member.id}/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(authenticated_member.id)

    def test_me_endpoint(self, api_client, authenticated_member):
        """Test /me/ endpoint returns current user's profile."""
        url = '/api/v1/members/members/me/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(authenticated_member.id)

    def test_update_own_profile(self, api_client, authenticated_member):
        """Test member can update their own profile."""
        url = f'/api/v1/members/members/{authenticated_member.id}/'
        data = {'first_name': 'Updated'}
        response = api_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK

        authenticated_member.refresh_from_db()
        assert authenticated_member.first_name == 'Updated'

    def test_create_member_public(self, api_client):
        """Test that member creation is public (registration)."""
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
        """Test that only staff can delete members."""
        other_member = MemberFactory()

        url = f'/api/v1/members/members/{other_member.id}/'
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_as_pastor(self, api_client, authenticated_pastor):
        """Test that pastors can delete members."""
        member = MemberFactory()

        url = f'/api/v1/members/members/{member.id}/'
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_search_members(self, api_client, authenticated_pastor):
        """Test member search."""
        MemberFactory(first_name='Jean', last_name='Dupont')
        MemberFactory(first_name='Marie', last_name='Martin')

        url = '/api/v1/members/members/?search=Dupont'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1

    def test_filter_by_role(self, api_client, authenticated_pastor):
        """Test filtering members by role."""
        MemberFactory.create_batch(3)

        url = '/api/v1/members/members/?role=pastor'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Should find at least the authenticated pastor
        assert response.data['count'] >= 1


@pytest.mark.django_db
class TestBirthdayEndpoint:
    """Tests for birthday endpoint."""

    def test_birthdays_today(self, api_client, authenticated_member):
        """Test birthdays today endpoint."""
        url = '/api/v1/members/members/birthdays/?period=today'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_birthdays_week(self, api_client, authenticated_member):
        """Test birthdays this week endpoint."""
        url = '/api/v1/members/members/birthdays/?period=week'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_birthdays_month(self, api_client, authenticated_member):
        """Test birthdays this month endpoint."""
        url = '/api/v1/members/members/birthdays/?period=month&month=6'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestDirectoryEndpoint:
    """Tests for directory endpoint."""

    def test_directory_respects_privacy(self, api_client, authenticated_member):
        """Test that directory respects privacy settings."""
        # Create a private member
        private_member = MemberFactory()
        DirectoryPrivacy.objects.filter(member=private_member).update(visibility='private')

        url = '/api/v1/members/members/directory/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        # Private member should not be visible to regular members
        ids = [item['id'] for item in response.data['results']]
        assert str(private_member.id) not in ids

    def test_directory_search(self, api_client, authenticated_member):
        """Test directory search."""
        MemberFactory(first_name='Searchable', last_name='User')

        url = '/api/v1/members/members/directory/?search=Searchable'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestGroupViewSet:
    """Tests for GroupViewSet."""

    def test_list_groups(self, api_client, authenticated_member):
        """Test listing groups."""
        GroupFactory.create_batch(3)

        url = '/api/v1/members/groups/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 3

    def test_retrieve_group(self, api_client, authenticated_member):
        """Test retrieving a group."""
        group = GroupFactory()

        url = f'/api/v1/members/groups/{group.id}/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == group.name

    def test_create_group_requires_staff(self, api_client, authenticated_member):
        """Test that creating groups requires staff."""
        url = '/api/v1/members/groups/'
        data = {'name': 'New Group', 'group_type': 'cell'}
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_group_as_pastor(self, api_client, authenticated_pastor):
        """Test that pastors can create groups."""
        url = '/api/v1/members/groups/'
        data = {'name': 'New Group', 'group_type': 'cell'}
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
class TestFamilyViewSet:
    """Tests for FamilyViewSet."""

    def test_list_families(self, api_client, authenticated_member):
        """Test listing families."""
        FamilyFactory.create_batch(3)

        url = '/api/v1/members/families/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 3

    def test_create_family_requires_staff(self, api_client, authenticated_member):
        """Test that creating families requires staff."""
        url = '/api/v1/members/families/'
        data = {'name': 'New Family'}
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_403_FORBIDDEN
