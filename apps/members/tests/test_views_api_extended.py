"""
Extended tests for members API views - covering previously uncovered lines.

This file targets specific uncovered lines in views_api.py to improve coverage
beyond the base tests in test_views_api.py.
"""
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


# =============================================================================
# MEMBER VIEWSET EXTENDED TESTS
# =============================================================================


@pytest.mark.django_db
class TestMemberViewSetExtended:
    """Extended tests for MemberViewSet covering uncovered lines."""

    # ----- Line 88: Staff/superuser get_queryset path -----

    def test_staff_user_sees_all_members(self, api_client):
        """Staff user (is_staff=True) should see all members via get_queryset."""
        user = UserFactory(is_staff=True)
        api_client.force_authenticate(user=user)
        MemberFactory.create_batch(5)

        url = '/api/v1/members/members/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 5

    def test_superuser_sees_all_members(self, api_client):
        """Superuser should see all members via get_queryset."""
        user = UserFactory(is_superuser=True)
        api_client.force_authenticate(user=user)
        MemberFactory.create_batch(4)

        url = '/api/v1/members/members/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 4

    # ----- Lines 100-107: Group leader queryset -----

    def test_group_leader_sees_own_group_members(self, api_client):
        """Group leader should see themselves plus their group members."""
        user = UserFactory()
        leader = GroupLeaderFactory(user=user)
        api_client.force_authenticate(user=user)

        group = GroupFactory(leader=leader)
        member_in_group_1 = MemberFactory()
        member_in_group_2 = MemberFactory()
        GroupMembership.objects.create(member=member_in_group_1, group=group)
        GroupMembership.objects.create(member=member_in_group_2, group=group)

        # A member NOT in the group
        outsider = MemberFactory()

        url = '/api/v1/members/members/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        result_ids = [item['id'] for item in response.data['results']]
        assert str(leader.id) in result_ids
        assert str(member_in_group_1.id) in result_ids
        assert str(member_in_group_2.id) in result_ids
        assert str(outsider.id) not in result_ids

    # ----- Line 113: User without member_profile gets empty queryset -----

    def test_user_without_member_profile_gets_empty_queryset(self, api_client):
        """A user with no member_profile and not staff should get empty queryset."""
        user = UserFactory()  # No member profile, not staff
        api_client.force_authenticate(user=user)
        MemberFactory.create_batch(3)

        url = '/api/v1/members/members/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 0

    # ----- Line 131: MemberAdminSerializer returned for staff update -----

    def test_staff_update_uses_admin_serializer(self, api_client):
        """Staff user updating a member should use MemberAdminSerializer.

        MemberAdminSerializer includes the 'role' field that
        MemberProfileSerializer does not, so we verify by updating role.
        """
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
        """Pastor member updating another member should use MemberAdminSerializer."""
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

    # ----- Lines 135, 138: BirthdaySerializer and DirectoryMemberSerializer -----

    def test_get_serializer_class_returns_birthday_serializer(self):
        """get_serializer_class should return BirthdaySerializer for birthdays action."""
        viewset = MemberViewSet()
        viewset.action = 'birthdays'
        viewset.request = type('Request', (), {'user': UserFactory()})()
        assert viewset.get_serializer_class() == BirthdaySerializer

    def test_get_serializer_class_returns_directory_serializer(self):
        """get_serializer_class should return DirectoryMemberSerializer for directory action."""
        viewset = MemberViewSet()
        viewset.action = 'directory'
        viewset.request = type('Request', (), {'user': UserFactory()})()
        assert viewset.get_serializer_class() == DirectoryMemberSerializer

    # ----- Line 166: Default permissions fallback -----

    def test_default_permissions_fallback(self):
        """Unknown/unhandled action should fall back to IsMember permission."""
        viewset = MemberViewSet()
        viewset.action = 'unknown_custom_action'
        permissions = viewset.get_permissions()
        assert len(permissions) == 1
        assert isinstance(permissions[0], IsMember)

    # ----- Line 177: me() endpoint when user has no member_profile -----

    def test_me_no_member_profile_returns_404(self, api_client):
        """me() should return 404 when user has no member_profile."""
        user = UserFactory()  # No member profile
        api_client.force_authenticate(user=user)

        url = '/api/v1/members/members/me/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data['error'] == 'Aucun profil membre trouvé'

    # ----- Lines 189-198: me() endpoint with PUT/PATCH -----

    def test_me_patch_updates_profile(self, api_client):
        """PATCH /me/ should partially update the member profile."""
        member = MemberWithUserFactory()
        api_client.force_authenticate(user=member.user)

        url = '/api/v1/members/members/me/'
        data = {'first_name': 'PatchedFirst'}
        response = api_client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        member.refresh_from_db()
        assert member.first_name == 'PatchedFirst'
        # Response should use MemberSerializer (full detail)
        assert 'id' in response.data

    def test_me_put_updates_full_profile(self, api_client):
        """PUT /me/ should update the full member profile."""
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
        """PATCH /me/ with invalid data should return 400."""
        member = MemberWithUserFactory()
        api_client.force_authenticate(user=member.user)

        url = '/api/v1/members/members/me/'
        data = {'email': 'not-a-valid-email'}
        response = api_client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # ----- Lines 219-222: Birthdays with invalid month / month without param -----

    def test_birthdays_invalid_month_parameter(self, api_client):
        """Birthdays with invalid month should fall back gracefully."""
        member = MemberWithUserFactory()
        api_client.force_authenticate(user=member.user)

        url = '/api/v1/members/members/birthdays/?period=month&month=invalid'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_birthdays_month_period_without_month_param(self, api_client):
        """Birthdays with period=month but no month param should use default."""
        member = MemberWithUserFactory()
        api_client.force_authenticate(user=member.user)

        url = '/api/v1/members/members/birthdays/?period=month'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK


# =============================================================================
# DIRECTORY ENDPOINT EXTENDED TESTS
# =============================================================================


@pytest.mark.django_db
class TestDirectoryEndpointExtended:
    """Extended tests for the directory endpoint."""

    # ----- Line 256: Directory - staff role pass-through -----

    def test_directory_staff_role_sees_all_including_private(self, api_client):
        """Members with staff roles see all members including private ones."""
        user = UserFactory()
        pastor = PastorFactory(user=user)
        api_client.force_authenticate(user=user)

        # Create a member with private visibility
        private_member = MemberFactory()
        DirectoryPrivacy.objects.filter(member=private_member).update(
            visibility='private'
        )

        url = '/api/v1/members/members/directory/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        ids = [item['id'] for item in response.data['results']]
        assert str(private_member.id) in ids

    # ----- Lines 272-274: Directory - user without member_profile and not staff -----

    def test_directory_no_member_profile_not_staff_sees_public_only(self, api_client):
        """Users without member profile and not staff see only public profiles."""
        user = UserFactory()  # No member profile, not staff
        api_client.force_authenticate(user=user)

        public_member = MemberFactory()
        # Ensure public visibility
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

    # ----- Lines 286-287: Directory - non-paginated response path -----

    def test_directory_non_paginated_response(self, api_client):
        """When pagination is disabled, directory returns a flat list."""
        member = MemberWithUserFactory()
        api_client.force_authenticate(user=member.user)
        MemberFactory.create_batch(3)

        url = '/api/v1/members/members/directory/'
        with patch.object(MemberViewSet, 'pagination_class', None):
            response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Without pagination, response.data should be a list, not a dict
        assert isinstance(response.data, list)


# =============================================================================
# FAMILY VIEWSET EXTENDED TESTS
# =============================================================================


@pytest.mark.django_db
class TestFamilyViewSetExtended:
    """Extended tests for FamilyViewSet."""

    # ----- Line 315: FamilySerializer for detail view -----

    def test_retrieve_family_uses_detail_serializer(self, api_client):
        """Retrieving a family should use FamilySerializer (with members list)."""
        member = MemberWithUserFactory()
        api_client.force_authenticate(user=member.user)
        family = FamilyFactory()
        # Add a member to the family
        MemberFactory(family=family)

        url = f'/api/v1/members/families/{family.id}/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == family.name
        # FamilySerializer includes 'members' and 'full_address' (unlike FamilyListSerializer)
        assert 'members' in response.data
        assert 'full_address' in response.data


# =============================================================================
# GROUP VIEWSET EXTENDED TESTS
# =============================================================================


@pytest.mark.django_db
class TestGroupViewSetExtended:
    """Extended tests for GroupViewSet."""

    # ----- Lines 370-374: Group members endpoint -----

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

    # ----- Lines 384-409: Group add-member endpoint -----

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
        """Adding a member who is already in the group should return 400."""
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
        """Adding a non-existent member should return 404."""
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

    # ----- Lines 419-430: Group remove-member endpoint -----

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
        """Removing a member who is not in the group should return 404."""
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


# =============================================================================
# DIRECTORY PRIVACY VIEWSET EXTENDED TESTS
# =============================================================================


@pytest.mark.django_db
class TestDirectoryPrivacyViewSetExtended:
    """Extended tests for DirectoryPrivacyViewSet."""

    # ----- Lines 452-460: DirectoryPrivacy queryset paths -----

    def test_privacy_queryset_staff_sees_all(self, api_client):
        """Staff user should see all privacy settings."""
        user = UserFactory(is_staff=True)
        api_client.force_authenticate(user=user)
        MemberFactory.create_batch(3)

        url = '/api/v1/members/privacy/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 3

    def test_privacy_queryset_member_sees_own_only(self, api_client):
        """Member should only see their own privacy settings."""
        member = MemberWithUserFactory()
        api_client.force_authenticate(user=member.user)
        # Create other members (each gets privacy settings from factory)
        MemberFactory.create_batch(3)

        url = '/api/v1/members/privacy/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1

    def test_privacy_queryset_no_profile_returns_empty(self, api_client):
        """User without member profile gets empty queryset."""
        user = UserFactory()  # No member profile, not staff
        api_client.force_authenticate(user=user)

        url = '/api/v1/members/privacy/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 0

    # ----- Lines 470-498: DirectoryPrivacy me endpoint -----

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
        user = UserFactory()  # No member profile
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
