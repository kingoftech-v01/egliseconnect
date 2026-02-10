"""Extended tests for members API views covering edge cases and specific code paths."""
import uuid
from unittest.mock import patch

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.members.models import Member, Family, Group, GroupMembership, DirectoryPrivacy
from apps.members.views_api import MemberViewSet
from apps.members.serializers import (
    MemberAdminSerializer,
    BirthdaySerializer,
    DirectoryMemberSerializer,
)
from apps.core.permissions import IsMember

from .factories import (
    UserFactory,
    MemberFactory,
    MemberWithUserFactory,
    PastorFactory,
    AdminMemberFactory,
    GroupLeaderFactory,
    GroupFactory,
    FamilyFactory,
    GroupMembershipFactory,
)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestMemberViewSetExtended:
    """Extended tests for MemberViewSet covering specific code paths."""

    def test_staff_user_sees_all_members(self, api_client):
        """Staff user (is_staff=True) sees all members."""
        user = UserFactory(is_staff=True)
        api_client.force_authenticate(user=user)
        MemberFactory.create_batch(5)

        url = '/api/v1/members/members/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 5

    def test_superuser_sees_all_members(self, api_client):
        """Superuser sees all members (including their own auto-created profile)."""
        user = UserFactory(is_superuser=True)
        api_client.force_authenticate(user=user)
        MemberFactory.create_batch(4)

        url = '/api/v1/members/members/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # 4 batch + 1 auto-created for the superuser
        assert response.data['count'] == 5

    def test_group_leader_sees_own_group_members(self, api_client):
        """Group leader sees themselves plus their group members only."""
        user = UserFactory()
        leader = GroupLeaderFactory(user=user)
        api_client.force_authenticate(user=user)

        group = GroupFactory(leader=leader)
        member_in_group_1 = MemberFactory()
        member_in_group_2 = MemberFactory()
        GroupMembership.objects.create(member=member_in_group_1, group=group)
        GroupMembership.objects.create(member=member_in_group_2, group=group)

        outsider = MemberFactory()

        url = '/api/v1/members/members/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        result_ids = [item['id'] for item in response.data['results']]
        assert str(leader.id) in result_ids
        assert str(member_in_group_1.id) in result_ids
        assert str(member_in_group_2.id) in result_ids
        assert str(outsider.id) not in result_ids

    def test_user_without_member_profile_gets_empty_queryset(self, api_client):
        """User with no member_profile and not staff gets empty queryset."""
        user = UserFactory()
        api_client.force_authenticate(user=user)
        MemberFactory.create_batch(3)

        url = '/api/v1/members/members/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 0

    def test_staff_update_uses_admin_serializer(self, api_client):
        """Staff updating a member uses MemberAdminSerializer with role field."""
        user = UserFactory(is_staff=True)
        api_client.force_authenticate(user=user)
        member = MemberFactory()

        url = f'/api/v1/members/members/{member.id}/'
        data = {'first_name': 'AdminUpdated', 'role': 'pastor'}
        response = api_client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        member.refresh_from_db()
        assert member.first_name == 'AdminUpdated'
        assert member.role == 'pastor'

    def test_pastor_update_uses_admin_serializer(self, api_client):
        """Pastor updating another member uses MemberAdminSerializer."""
        user = UserFactory()
        pastor = PastorFactory(user=user)
        api_client.force_authenticate(user=user)
        member = MemberFactory()

        url = f'/api/v1/members/members/{member.id}/'
        data = {'role': 'admin'}
        response = api_client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        member.refresh_from_db()
        assert member.role == 'admin'

    def test_get_serializer_class_returns_birthday_serializer(self):
        """get_serializer_class returns BirthdaySerializer for birthdays action."""
        viewset = MemberViewSet()
        viewset.action = 'birthdays'
        viewset.request = type('Request', (), {'user': UserFactory()})()
        assert viewset.get_serializer_class() == BirthdaySerializer

    def test_get_serializer_class_returns_directory_serializer(self):
        """get_serializer_class returns DirectoryMemberSerializer for directory action."""
        viewset = MemberViewSet()
        viewset.action = 'directory'
        viewset.request = type('Request', (), {'user': UserFactory()})()
        assert viewset.get_serializer_class() == DirectoryMemberSerializer

    def test_default_permissions_fallback(self):
        """Unknown action falls back to IsMember permission."""
        viewset = MemberViewSet()
        viewset.action = 'unknown_custom_action'
        permissions = viewset.get_permissions()
        assert len(permissions) == 1
        assert isinstance(permissions[0], IsMember)

    def test_me_no_member_profile_returns_404(self, api_client):
        """me() returns 404 when user has no member_profile."""
        user = UserFactory()
        api_client.force_authenticate(user=user)

        url = '/api/v1/members/members/me/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data['error'] == 'Aucun profil membre trouvé'

    def test_me_patch_updates_profile(self, api_client):
        """PATCH /me/ partially updates the member profile."""
        member = MemberWithUserFactory()
        api_client.force_authenticate(user=member.user)

        url = '/api/v1/members/members/me/'
        data = {'first_name': 'PatchedFirst'}
        response = api_client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        member.refresh_from_db()
        assert member.first_name == 'PatchedFirst'
        assert 'id' in response.data

    def test_me_put_updates_full_profile(self, api_client):
        """PUT /me/ updates the full member profile."""
        member = MemberWithUserFactory()
        api_client.force_authenticate(user=member.user)

        url = '/api/v1/members/members/me/'
        data = {
            'first_name': 'PutFirst',
            'last_name': 'PutLast',
            'email': 'put@example.com',
            'phone': '514-555-9999',
            'phone_secondary': '',
            'birth_date': '1990-01-15',
            'address': '123 Rue Principale',
            'city': 'Montreal',
            'province': 'QC',
            'postal_code': 'H1A 1A1',
            'family_status': 'single',
        }
        response = api_client.put(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        member.refresh_from_db()
        assert member.first_name == 'PutFirst'
        assert member.last_name == 'PutLast'

    def test_me_patch_invalid_data_returns_400(self, api_client):
        """PATCH /me/ with invalid data returns 400."""
        member = MemberWithUserFactory()
        api_client.force_authenticate(user=member.user)

        url = '/api/v1/members/members/me/'
        data = {'email': 'not-a-valid-email'}
        response = api_client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_birthdays_invalid_month_parameter(self, api_client):
        """Invalid month parameter handled gracefully."""
        member = MemberWithUserFactory()
        api_client.force_authenticate(user=member.user)

        url = '/api/v1/members/members/birthdays/?period=month&month=invalid'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_birthdays_month_period_without_month_param(self, api_client):
        """period=month without month param uses default."""
        member = MemberWithUserFactory()
        api_client.force_authenticate(user=member.user)

        url = '/api/v1/members/members/birthdays/?period=month'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestDirectoryEndpointExtended:
    """Extended tests for directory endpoint edge cases."""

    def test_directory_staff_role_sees_all_including_private(self, api_client):
        """Staff roles see all members including private ones."""
        user = UserFactory()
        pastor = PastorFactory(user=user)
        api_client.force_authenticate(user=user)

        private_member = MemberFactory()
        DirectoryPrivacy.objects.filter(member=private_member).update(
            visibility='private'
        )

        url = '/api/v1/members/members/directory/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        ids = [item['id'] for item in response.data['results']]
        assert str(private_member.id) in ids

    def test_directory_no_member_profile_not_staff_sees_public_only(self, api_client):
        """Users without member profile and not staff see only public profiles."""
        user = UserFactory()
        api_client.force_authenticate(user=user)

        public_member = MemberFactory()
        DirectoryPrivacy.objects.filter(member=public_member).update(
            visibility='public'
        )

        private_member = MemberFactory()
        DirectoryPrivacy.objects.filter(member=private_member).update(
            visibility='private'
        )

        url = '/api/v1/members/members/directory/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        ids = [item['id'] for item in response.data['results']]
        assert str(public_member.id) in ids
        assert str(private_member.id) not in ids

    def test_directory_non_paginated_response(self, api_client):
        """Without pagination, directory returns a flat list."""
        member = MemberWithUserFactory()
        api_client.force_authenticate(user=member.user)
        MemberFactory.create_batch(3)

        url = '/api/v1/members/members/directory/'
        with patch.object(MemberViewSet, 'pagination_class', None):
            response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)


@pytest.mark.django_db
class TestFamilyViewSetExtended:
    """Extended tests for FamilyViewSet."""

    def test_retrieve_family_uses_detail_serializer(self, api_client):
        """Retrieving a family uses FamilySerializer with members list."""
        member = MemberWithUserFactory()
        api_client.force_authenticate(user=member.user)
        family = FamilyFactory()
        MemberFactory(family=family)

        url = f'/api/v1/members/families/{family.id}/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == family.name
        assert 'members' in response.data
        assert 'full_address' in response.data


@pytest.mark.django_db
class TestGroupViewSetExtended:
    """Extended tests for GroupViewSet."""

    def test_group_members_returns_active_memberships(self, api_client):
        """GET /groups/{pk}/members/ returns only active memberships."""
        member = MemberWithUserFactory()
        api_client.force_authenticate(user=member.user)

        group = GroupFactory()
        active_member = MemberFactory()
        inactive_member = MemberFactory()
        GroupMembership.objects.create(
            member=active_member, group=group, is_active=True
        )
        GroupMembership.objects.create(
            member=inactive_member, group=group, is_active=False
        )

        url = f'/api/v1/members/groups/{group.id}/members/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert str(response.data[0]['member']) == str(active_member.id)

    def test_group_add_member_success(self, api_client):
        """POST /groups/{pk}/add-member/ successfully adds a member."""
        user = UserFactory()
        PastorFactory(user=user)
        api_client.force_authenticate(user=user)
        group = GroupFactory()
        new_member = MemberFactory()

        url = f'/api/v1/members/groups/{group.id}/add-member/'
        data = {'member': str(new_member.id), 'role': 'member'}
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert GroupMembership.objects.filter(
            member=new_member, group=group
        ).exists()

    def test_group_add_member_already_exists(self, api_client):
        """Adding existing member returns 400."""
        user = UserFactory()
        PastorFactory(user=user)
        api_client.force_authenticate(user=user)
        group = GroupFactory()
        existing_member = MemberFactory()
        GroupMembership.objects.create(member=existing_member, group=group)

        url = f'/api/v1/members/groups/{group.id}/add-member/'
        data = {'member': str(existing_member.id), 'role': 'member'}
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data

    def test_group_add_member_not_found(self, api_client):
        """Adding non-existent member returns 404."""
        user = UserFactory()
        PastorFactory(user=user)
        api_client.force_authenticate(user=user)
        group = GroupFactory()

        url = f'/api/v1/members/groups/{group.id}/add-member/'
        fake_id = str(uuid.uuid4())
        data = {'member': fake_id, 'role': 'member'}
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert 'error' in response.data

    def test_group_remove_member_success(self, api_client):
        """POST /groups/{pk}/remove-member/ successfully removes a member."""
        user = UserFactory()
        PastorFactory(user=user)
        api_client.force_authenticate(user=user)
        group = GroupFactory()
        member_to_remove = MemberFactory()
        GroupMembership.objects.create(member=member_to_remove, group=group)

        url = f'/api/v1/members/groups/{group.id}/remove-member/'
        data = {'member': str(member_to_remove.id)}
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not GroupMembership.objects.filter(
            member=member_to_remove, group=group
        ).exists()

    def test_group_remove_member_not_in_group(self, api_client):
        """Removing member not in group returns 404."""
        user = UserFactory()
        PastorFactory(user=user)
        api_client.force_authenticate(user=user)
        group = GroupFactory()
        member_not_in_group = MemberFactory()

        url = f'/api/v1/members/groups/{group.id}/remove-member/'
        data = {'member': str(member_not_in_group.id)}
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert 'error' in response.data


@pytest.mark.django_db
class TestDirectoryPrivacyViewSetExtended:
    """Extended tests for DirectoryPrivacyViewSet."""

    def test_privacy_queryset_staff_sees_all(self, api_client):
        """Staff user sees all privacy settings."""
        user = UserFactory(is_staff=True)
        api_client.force_authenticate(user=user)
        MemberFactory.create_batch(3)

        url = '/api/v1/members/privacy/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 3

    def test_privacy_queryset_member_sees_own_only(self, api_client):
        """Member only sees their own privacy settings."""
        member = MemberWithUserFactory()
        api_client.force_authenticate(user=member.user)
        MemberFactory.create_batch(3)

        url = '/api/v1/members/privacy/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1

    def test_privacy_queryset_no_profile_returns_empty(self, api_client):
        """User without member profile gets empty queryset."""
        user = UserFactory()
        api_client.force_authenticate(user=user)

        url = '/api/v1/members/privacy/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 0

    def test_privacy_me_get(self, api_client):
        """GET /privacy/me/ returns current user's privacy settings."""
        member = MemberWithUserFactory()
        api_client.force_authenticate(user=member.user)

        url = '/api/v1/members/privacy/me/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'visibility' in response.data
        assert 'show_email' in response.data

    def test_privacy_me_put(self, api_client):
        """PUT /privacy/me/ updates all privacy settings."""
        member = MemberWithUserFactory()
        api_client.force_authenticate(user=member.user)

        url = '/api/v1/members/privacy/me/'
        data = {
            'visibility': 'private',
            'show_email': False,
            'show_phone': False,
            'show_address': False,
            'show_birth_date': False,
            'show_photo': False,
        }
        response = api_client.put(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        privacy = DirectoryPrivacy.objects.get(member=member)
        assert privacy.visibility == 'private'
        assert privacy.show_email is False
        assert privacy.show_phone is False

    def test_privacy_me_patch(self, api_client):
        """PATCH /privacy/me/ partially updates privacy settings."""
        member = MemberWithUserFactory()
        api_client.force_authenticate(user=member.user)

        url = '/api/v1/members/privacy/me/'
        data = {'visibility': 'group'}
        response = api_client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        privacy = DirectoryPrivacy.objects.get(member=member)
        assert privacy.visibility == 'group'

    def test_privacy_me_no_profile_returns_404(self, api_client):
        """GET /privacy/me/ without member profile returns 404."""
        user = UserFactory()
        api_client.force_authenticate(user=user)

        url = '/api/v1/members/privacy/me/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data['error'] == 'Aucun profil membre trouvé'

    def test_privacy_me_returns_existing_settings(self, api_client):
        """GET /privacy/me/ returns existing settings."""
        member = MemberWithUserFactory()
        api_client.force_authenticate(user=member.user)

        url = '/api/v1/members/privacy/me/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'visibility' in response.data

    def test_privacy_me_patch_invalid_data_returns_400(self, api_client):
        """PATCH /privacy/me/ with invalid data returns 400."""
        member = MemberWithUserFactory()
        api_client.force_authenticate(user=member.user)

        url = '/api/v1/members/privacy/me/'
        data = {'visibility': 'INVALID_CHOICE'}
        response = api_client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
