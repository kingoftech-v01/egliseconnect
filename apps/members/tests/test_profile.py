"""Tests for profile page, access control, and modification requests."""
import pytest
from django.test import Client
from django.utils import timezone

from apps.core.constants import Roles, ModificationRequestStatus
from apps.members.models import ProfileModificationRequest
from apps.members.tests.factories import (
    UserFactory, MemberFactory, MemberWithUserFactory,
    PastorFactory, AdminMemberFactory, DeaconFactory,
)


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def member_user():
    """Regular member with linked user account."""
    user = UserFactory()
    member = MemberFactory(user=user, role=Roles.MEMBER)
    return user, member


@pytest.fixture
def pastor_user():
    """Pastor with linked user account."""
    user = UserFactory()
    member = PastorFactory(user=user)
    return user, member


@pytest.fixture
def admin_user():
    """Admin member with linked user account."""
    user = UserFactory()
    member = AdminMemberFactory(user=user)
    return user, member


@pytest.fixture
def deacon_user():
    """Deacon with linked user account."""
    user = UserFactory()
    member = DeaconFactory(user=user)
    return user, member


# ── ProfileModificationRequest Model ──


@pytest.mark.django_db
class TestProfileModificationRequestModel:

    def test_create_request(self, pastor_user, member_user):
        _, pastor = pastor_user
        _, member = member_user
        req = ProfileModificationRequest.objects.create(
            target_member=member,
            requested_by=pastor,
            message='Veuillez mettre à jour votre adresse.',
        )
        assert req.status == ModificationRequestStatus.PENDING
        assert req.completed_at is None

    def test_complete_request(self, pastor_user, member_user):
        _, pastor = pastor_user
        _, member = member_user
        req = ProfileModificationRequest.objects.create(
            target_member=member,
            requested_by=pastor,
            message='Test',
        )
        req.status = ModificationRequestStatus.COMPLETED
        req.completed_at = timezone.now()
        req.save()
        req.refresh_from_db()
        assert req.status == ModificationRequestStatus.COMPLETED
        assert req.completed_at is not None

    def test_str_representation(self, pastor_user, member_user):
        _, pastor = pastor_user
        _, member = member_user
        req = ProfileModificationRequest.objects.create(
            target_member=member,
            requested_by=pastor,
            message='Test',
        )
        assert member.full_name in str(req)

    def test_ordering_is_by_created_at_desc(self, pastor_user, member_user):
        _, pastor = pastor_user
        _, member = member_user
        # Verify the model Meta ordering is set
        assert ProfileModificationRequest._meta.ordering == ['-created_at']


# ── My Profile View ──


@pytest.mark.django_db
class TestMyProfileView:

    def test_requires_login(self, client):
        response = client.get('/members/my-profile/')
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_user_without_member_returns_404(self, client):
        user = UserFactory()
        client.force_login(user)
        response = client.get('/members/my-profile/')
        assert response.status_code == 404

    def test_renders_for_member(self, client, member_user):
        user, member = member_user
        client.force_login(user)
        response = client.get('/members/my-profile/')
        assert response.status_code == 200
        content = response.content.decode()
        assert 'Mon profil' in content
        assert member.full_name in content

    def test_shows_form_fields(self, client, member_user):
        user, _ = member_user
        client.force_login(user)
        response = client.get('/members/my-profile/')
        content = response.content.decode()
        assert 'form-control' in content
        assert 'Enregistrer les modifications' in content

    def test_shows_security_links(self, client, member_user):
        user, _ = member_user
        client.force_login(user)
        response = client.get('/members/my-profile/')
        content = response.content.decode()
        assert '/accounts/password/change/' in content
        assert '/accounts/2fa/' in content
        assert '/accounts/email/' in content

    def test_post_updates_profile(self, client, member_user):
        user, member = member_user
        client.force_login(user)
        response = client.post('/members/my-profile/', {
            'first_name': 'NouveauPrenom',
            'last_name': member.last_name,
            'email': member.email,
            'province': 'QC',
            'family_status': 'single',
        })
        assert response.status_code == 302
        member.refresh_from_db()
        assert member.first_name == 'NouveauPrenom'

    def test_post_invalid_rerenders(self, client, member_user):
        user, _ = member_user
        client.force_login(user)
        response = client.post('/members/my-profile/', {
            'first_name': '',  # required field
            'last_name': '',
        })
        assert response.status_code == 200

    def test_shows_pending_modification_requests(self, client, member_user, pastor_user):
        user, member = member_user
        _, pastor = pastor_user
        ProfileModificationRequest.objects.create(
            target_member=member,
            requested_by=pastor,
            message='Veuillez mettre à jour votre téléphone.',
        )
        client.force_login(user)
        response = client.get('/members/my-profile/')
        content = response.content.decode()
        assert 'Demandes de modification' in content
        assert 'mettre à jour votre téléphone' in content


# ── Access Control (member_update) ──


@pytest.mark.django_db
class TestMemberUpdateAccessControl:

    def test_member_edits_own_profile(self, client, member_user):
        user, member = member_user
        client.force_login(user)
        response = client.get(f'/members/{member.pk}/edit/')
        assert response.status_code == 200
        content = response.content.decode()
        # Should show personal fields (MemberProfileForm)
        assert 'first_name' in content

    def test_admin_editing_other_gets_staff_form(self, client, admin_user, member_user):
        admin_u, _ = admin_user
        _, member = member_user
        client.force_login(admin_u)
        response = client.get(f'/members/{member.pk}/edit/')
        assert response.status_code == 200
        content = response.content.decode()
        # Should show admin fields (MemberStaffForm), NOT personal fields
        assert 'id_role' in content
        assert 'id_notes' in content

    def test_admin_cannot_change_personal_fields(self, client, admin_user, member_user):
        admin_u, _ = admin_user
        _, member = member_user
        original_name = member.first_name
        client.force_login(admin_u)
        # Post with admin fields only (MemberStaffForm)
        response = client.post(f'/members/{member.pk}/edit/', {
            'role': Roles.VOLUNTEER,
            'membership_status': 'active',
            'is_active': True,
        })
        assert response.status_code == 302
        member.refresh_from_db()
        assert member.first_name == original_name  # unchanged
        assert member.role == Roles.VOLUNTEER

    def test_regular_member_cannot_edit_other(self, client, member_user):
        user, _ = member_user
        other = MemberFactory()
        client.force_login(user)
        response = client.get(f'/members/{other.pk}/edit/')
        assert response.status_code == 302  # redirect with error

    def test_pastor_editing_other_gets_staff_form(self, client, pastor_user, member_user):
        pastor_u, _ = pastor_user
        _, member = member_user
        client.force_login(pastor_u)
        response = client.get(f'/members/{member.pk}/edit/')
        assert response.status_code == 200
        content = response.content.decode()
        assert 'id_role' in content

    def test_deacon_editing_other_gets_staff_form(self, client, deacon_user, member_user):
        deacon_u, _ = deacon_user
        _, member = member_user
        client.force_login(deacon_u)
        response = client.get(f'/members/{member.pk}/edit/')
        assert response.status_code == 200
        content = response.content.decode()
        assert 'id_role' in content


# ── member_detail View ──


@pytest.mark.django_db
class TestMemberDetailAccessControl:

    def test_own_profile_shows_my_profile_link(self, client, member_user):
        user, member = member_user
        client.force_login(user)
        response = client.get(f'/members/{member.pk}/')
        content = response.content.decode()
        assert '/members/my-profile/' in content
        assert 'Mon profil' in content

    def test_staff_sees_admin_and_request_buttons(self, client, admin_user, member_user):
        admin_u, _ = admin_user
        _, member = member_user
        client.force_login(admin_u)
        response = client.get(f'/members/{member.pk}/')
        content = response.content.decode()
        assert 'Modifier (admin)' in content
        assert 'Demander une modification' in content

    def test_staff_does_not_see_own_admin_buttons(self, client, admin_user):
        admin_u, admin_member = admin_user
        client.force_login(admin_u)
        response = client.get(f'/members/{admin_member.pk}/')
        content = response.content.decode()
        assert 'Mon profil' in content
        assert 'Modifier (admin)' not in content


# ── Request Modification View ──


@pytest.mark.django_db
class TestRequestModificationView:

    def test_requires_login(self, client, member_user):
        _, member = member_user
        response = client.get(f'/members/{member.pk}/request-modification/')
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_non_staff_denied(self, client, member_user):
        user, _ = member_user
        other = MemberFactory()
        client.force_login(user)
        response = client.get(f'/members/{other.pk}/request-modification/')
        assert response.status_code == 302

    def test_staff_can_access(self, client, pastor_user, member_user):
        pastor_u, _ = pastor_user
        _, member = member_user
        client.force_login(pastor_u)
        response = client.get(f'/members/{member.pk}/request-modification/')
        assert response.status_code == 200
        content = response.content.decode()
        assert member.full_name in content

    def test_staff_creates_request(self, client, pastor_user, member_user):
        pastor_u, pastor = pastor_user
        _, member = member_user
        client.force_login(pastor_u)
        response = client.post(f'/members/{member.pk}/request-modification/', {
            'message': 'Veuillez corriger votre adresse.',
        })
        assert response.status_code == 302
        req = ProfileModificationRequest.objects.get(target_member=member)
        assert req.requested_by == pastor
        assert 'corriger votre adresse' in req.message


# ── Complete Modification Request View ──


@pytest.mark.django_db
class TestCompleteModificationRequestView:

    def test_target_member_can_complete(self, client, member_user, pastor_user):
        user, member = member_user
        _, pastor = pastor_user
        req = ProfileModificationRequest.objects.create(
            target_member=member,
            requested_by=pastor,
            message='Test',
        )
        client.force_login(user)
        response = client.post(f'/members/modification-requests/{req.pk}/complete/')
        assert response.status_code == 302
        req.refresh_from_db()
        assert req.status == ModificationRequestStatus.COMPLETED
        assert req.completed_at is not None

    def test_other_user_cannot_complete(self, client, pastor_user, member_user):
        _, member = member_user
        pastor_u, pastor = pastor_user
        req = ProfileModificationRequest.objects.create(
            target_member=member,
            requested_by=pastor,
            message='Test',
        )
        client.force_login(pastor_u)
        response = client.post(f'/members/modification-requests/{req.pk}/complete/')
        assert response.status_code == 302
        req.refresh_from_db()
        assert req.status == ModificationRequestStatus.PENDING  # unchanged


# ── Header & Sidebar ──


@pytest.mark.django_db
class TestHeaderAndSidebar:

    def test_header_profile_link(self, client, member_user):
        user, _ = member_user
        client.force_login(user)
        response = client.get('/members/my-profile/')
        content = response.content.decode()
        assert '/members/my-profile/' in content
