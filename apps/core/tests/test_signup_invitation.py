"""Tests for custom signup form with invitation code field."""
import pytest
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.core.constants import MembershipStatus, Roles
from apps.members.models import Member
from apps.members.tests.factories import MemberFactory, UserFactory
from apps.onboarding.models import InvitationCode

User = get_user_model()


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def admin_member():
    """Admin member for creating invitations."""
    user = UserFactory()
    return MemberFactory(user=user, role=Roles.ADMIN)


@pytest.fixture
def valid_invitation(admin_member):
    """A valid, usable invitation code."""
    return InvitationCode.objects.create(
        code='TESTCODE1',
        role=Roles.MEMBER,
        created_by=admin_member,
        expires_at=timezone.now() + timedelta(days=30),
        max_uses=1,
    )


@pytest.fixture
def skip_onboarding_invitation(admin_member):
    """Invitation that skips onboarding."""
    return InvitationCode.objects.create(
        code='SKIPCODE1',
        role=Roles.VOLUNTEER,
        created_by=admin_member,
        expires_at=timezone.now() + timedelta(days=30),
        max_uses=1,
        skip_onboarding=True,
    )


@pytest.fixture
def expired_invitation(admin_member):
    """An expired invitation code."""
    return InvitationCode.objects.create(
        code='EXPCODE01',
        role=Roles.MEMBER,
        created_by=admin_member,
        expires_at=timezone.now() - timedelta(days=1),
        max_uses=1,
    )


@pytest.fixture
def used_up_invitation(admin_member):
    """An invitation that has reached max uses."""
    return InvitationCode.objects.create(
        code='USEDCODE',
        role=Roles.MEMBER,
        created_by=admin_member,
        expires_at=timezone.now() + timedelta(days=30),
        max_uses=1,
        use_count=1,
        is_active=False,
    )


SIGNUP_DATA = {
    'email': 'newuser@example.com',
    'password1': 'SecurePass123!',
    'password2': 'SecurePass123!',
}


@pytest.mark.django_db
class TestSignupPageRendering:
    """Test that the invitation code field appears on the signup page."""

    def test_signup_page_shows_invitation_code_field(self, client):
        response = client.get(reverse('account_signup'))
        content = response.content.decode()
        assert 'invitation_code' in content

    def test_signup_page_shows_invitation_label(self, client):
        response = client.get(reverse('account_signup'))
        content = response.content.decode()
        assert "Code d&#x27;invitation" in content or "Code d'invitation" in content


@pytest.mark.django_db
class TestSignupWithoutInvitation:
    """Test signup without an invitation code creates User + Member."""

    def test_signup_creates_user_and_member(self, client):
        response = client.post(reverse('account_signup'), SIGNUP_DATA)
        assert User.objects.filter(email='newuser@example.com').exists()
        user = User.objects.get(email='newuser@example.com')
        assert Member.objects.filter(user=user).exists()
        member = Member.objects.get(user=user)
        assert member.membership_status == MembershipStatus.REGISTERED

    def test_signup_without_code_starts_onboarding(self, client):
        client.post(reverse('account_signup'), SIGNUP_DATA)
        user = User.objects.get(email='newuser@example.com')
        member = Member.objects.get(user=user)
        assert member.registration_date is not None


@pytest.mark.django_db
class TestSignupWithValidInvitation:
    """Test signup with a valid invitation code."""

    def test_signup_with_code_creates_member(self, client, valid_invitation):
        data = {**SIGNUP_DATA, 'invitation_code': 'TESTCODE1'}
        client.post(reverse('account_signup'), data)
        user = User.objects.get(email='newuser@example.com')
        assert Member.objects.filter(user=user).exists()

    def test_signup_with_code_increments_use_count(self, client, valid_invitation):
        data = {**SIGNUP_DATA, 'invitation_code': 'TESTCODE1'}
        client.post(reverse('account_signup'), data)
        valid_invitation.refresh_from_db()
        assert valid_invitation.use_count == 1

    def test_signup_with_code_sets_used_by(self, client, valid_invitation):
        data = {**SIGNUP_DATA, 'invitation_code': 'TESTCODE1'}
        client.post(reverse('account_signup'), data)
        valid_invitation.refresh_from_db()
        user = User.objects.get(email='newuser@example.com')
        member = Member.objects.get(user=user)
        assert valid_invitation.used_by == member

    def test_signup_code_case_insensitive(self, client, valid_invitation):
        data = {**SIGNUP_DATA, 'invitation_code': 'testcode1'}
        client.post(reverse('account_signup'), data)
        valid_invitation.refresh_from_db()
        assert valid_invitation.use_count == 1


@pytest.mark.django_db
class TestSignupWithSkipOnboarding:
    """Test signup with invitation that skips onboarding."""

    def test_skip_onboarding_sets_active(self, client, skip_onboarding_invitation):
        data = {**SIGNUP_DATA, 'invitation_code': 'SKIPCODE1'}
        client.post(reverse('account_signup'), data)
        user = User.objects.get(email='newuser@example.com')
        member = Member.objects.get(user=user)
        assert member.membership_status == MembershipStatus.ACTIVE

    def test_skip_onboarding_sets_joined_date(self, client, skip_onboarding_invitation):
        data = {**SIGNUP_DATA, 'invitation_code': 'SKIPCODE1'}
        client.post(reverse('account_signup'), data)
        user = User.objects.get(email='newuser@example.com')
        member = Member.objects.get(user=user)
        assert member.joined_date is not None


@pytest.mark.django_db
class TestSignupWithInvalidInvitation:
    """Test signup with invalid/expired/used invitation codes."""

    def test_invalid_code_shows_error(self, client):
        data = {**SIGNUP_DATA, 'invitation_code': 'BADCODE99'}
        response = client.post(reverse('account_signup'), data)
        assert response.status_code == 200
        assert not User.objects.filter(email='newuser@example.com').exists()

    def test_expired_code_shows_error(self, client, expired_invitation):
        data = {**SIGNUP_DATA, 'invitation_code': 'EXPCODE01'}
        response = client.post(reverse('account_signup'), data)
        assert response.status_code == 200
        assert not User.objects.filter(email='newuser@example.com').exists()

    def test_used_up_code_shows_error(self, client, used_up_invitation):
        data = {**SIGNUP_DATA, 'invitation_code': 'USEDCODE'}
        response = client.post(reverse('account_signup'), data)
        assert response.status_code == 200
        assert not User.objects.filter(email='newuser@example.com').exists()
