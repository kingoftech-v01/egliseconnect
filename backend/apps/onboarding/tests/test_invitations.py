"""Tests for invitation system: model, service, views."""
import pytest
from datetime import timedelta

from django.utils import timezone

from apps.core.constants import Roles, MembershipStatus
from apps.members.tests.factories import MemberFactory, PastorFactory, MemberWithUserFactory
from apps.members.models import MemberRole
from apps.onboarding.models import InvitationCode
from apps.onboarding.services import OnboardingService
from .factories import InvitationCodeFactory


# ==============================================================================
# Model tests
# ==============================================================================


@pytest.mark.django_db
class TestInvitationCodeModel:
    """Tests for InvitationCode model."""

    def test_create_invitation(self):
        """InvitationCode creation works with auto-generated code."""
        inv = InvitationCodeFactory()
        assert inv.id is not None
        assert len(inv.code) == 8
        assert inv.code == inv.code.upper()

    def test_unique_code(self):
        """Each invitation gets a unique code."""
        inv1 = InvitationCodeFactory()
        inv2 = InvitationCodeFactory()
        assert inv1.code != inv2.code

    def test_is_expired_future(self):
        """Not expired when expires_at is in the future."""
        inv = InvitationCodeFactory(expires_at=timezone.now() + timedelta(days=10))
        assert inv.is_expired is False

    def test_is_expired_past(self):
        """Expired when expires_at is in the past."""
        inv = InvitationCodeFactory(expires_at=timezone.now() - timedelta(hours=1))
        assert inv.is_expired is True

    def test_is_usable_active(self):
        """Usable when active, not expired, and uses remaining."""
        inv = InvitationCodeFactory()
        assert inv.is_usable is True

    def test_is_usable_expired(self):
        """Not usable when expired."""
        inv = InvitationCodeFactory(expires_at=timezone.now() - timedelta(hours=1))
        assert inv.is_usable is False

    def test_is_usable_max_uses_reached(self):
        """Not usable when max uses reached."""
        inv = InvitationCodeFactory(max_uses=1, use_count=1)
        assert inv.is_usable is False

    def test_is_usable_inactive(self):
        """Not usable when deactivated."""
        inv = InvitationCodeFactory(is_active=False)
        assert inv.is_usable is False

    def test_str(self):
        """String representation includes code and role."""
        inv = InvitationCodeFactory(role=Roles.VOLUNTEER)
        result = str(inv)
        assert inv.code in result

    def test_ordering(self):
        """Ordered by -created_at (newest first)."""
        inv1 = InvitationCodeFactory()
        inv2 = InvitationCodeFactory()
        invitations = list(InvitationCode.objects.all())
        assert invitations[0].pk == inv2.pk


# ==============================================================================
# Service tests
# ==============================================================================


@pytest.mark.django_db
class TestInvitationService:
    """Tests for invitation service methods."""

    def test_create_invitation(self):
        """create_invitation creates a valid invitation code."""
        pastor = PastorFactory()
        inv = OnboardingService.create_invitation(
            created_by=pastor,
            role=Roles.VOLUNTEER,
            expires_in_days=14,
            max_uses=5,
        )
        assert inv.code is not None
        assert inv.role == Roles.VOLUNTEER
        assert inv.max_uses == 5
        assert inv.created_by == pastor
        assert inv.is_usable is True

    def test_create_invitation_defaults(self):
        """create_invitation uses defaults correctly."""
        pastor = PastorFactory()
        inv = OnboardingService.create_invitation(created_by=pastor)
        assert inv.role == Roles.MEMBER
        assert inv.max_uses == 1
        assert inv.skip_onboarding is False

    def test_accept_invitation_assigns_role(self):
        """accept_invitation adds role via MemberRole."""
        pastor = PastorFactory()
        inv = OnboardingService.create_invitation(
            created_by=pastor,
            role=Roles.VOLUNTEER,
        )
        member = MemberFactory()
        OnboardingService.accept_invitation(inv, member)

        inv.refresh_from_db()
        assert inv.use_count == 1
        assert inv.used_by == member
        assert inv.used_at is not None
        assert MemberRole.objects.filter(member=member, role=Roles.VOLUNTEER).exists()

    def test_accept_invitation_skip_onboarding(self):
        """accept_invitation with skip_onboarding makes member active."""
        pastor = PastorFactory()
        inv = OnboardingService.create_invitation(
            created_by=pastor,
            role=Roles.DEACON,
            skip_onboarding=True,
        )
        member = MemberFactory(membership_status=MembershipStatus.REGISTERED)
        OnboardingService.accept_invitation(inv, member)

        member.refresh_from_db()
        assert member.membership_status == MembershipStatus.ACTIVE
        assert member.became_active_at is not None
        assert MemberRole.objects.filter(member=member, role=Roles.DEACON).exists()

    def test_accept_invitation_deactivates_on_max_uses(self):
        """Invitation becomes inactive when max uses reached."""
        pastor = PastorFactory()
        inv = OnboardingService.create_invitation(
            created_by=pastor, max_uses=1,
        )
        member = MemberFactory()
        OnboardingService.accept_invitation(inv, member)

        inv.refresh_from_db()
        assert inv.is_active is False
        assert inv.is_usable is False

    def test_accept_invitation_multi_use(self):
        """Multi-use invitation stays active until max reached."""
        pastor = PastorFactory()
        inv = OnboardingService.create_invitation(
            created_by=pastor, max_uses=3,
        )
        for _ in range(2):
            member = MemberFactory()
            OnboardingService.accept_invitation(inv, member)

        inv.refresh_from_db()
        assert inv.use_count == 2
        assert inv.is_usable is True

        # Third use: should exhaust
        member3 = MemberFactory()
        OnboardingService.accept_invitation(inv, member3)
        inv.refresh_from_db()
        assert inv.use_count == 3
        assert inv.is_usable is False

    def test_accept_expired_invitation_raises(self):
        """Cannot accept an expired invitation."""
        pastor = PastorFactory()
        inv = InvitationCodeFactory(
            created_by=pastor,
            expires_at=timezone.now() - timedelta(hours=1),
        )
        member = MemberFactory()
        with pytest.raises(ValueError, match='plus valide'):
            OnboardingService.accept_invitation(inv, member)

    def test_accept_same_role_no_duplicate(self):
        """If member already has the role, no duplicate MemberRole created."""
        pastor = PastorFactory()
        inv = OnboardingService.create_invitation(
            created_by=pastor, role=Roles.MEMBER,
        )
        member = MemberFactory(role=Roles.MEMBER)
        OnboardingService.accept_invitation(inv, member)
        # Should not create a MemberRole for MEMBER since that's the primary role
        assert MemberRole.objects.filter(member=member).count() == 0


# ==============================================================================
# View tests
# ==============================================================================


@pytest.mark.django_db
class TestInvitationViews:
    """Tests for invitation views."""

    def test_admin_invitations_list(self, client):
        """Admin can view invitation list."""
        from apps.members.tests.factories import AdminMemberFactory
        member = AdminMemberFactory()
        user = member.user if hasattr(member, 'user') and member.user else None
        if not user:
            from apps.members.tests.factories import UserFactory
            user = UserFactory()
            member.user = user
            member.save()
        client.force_login(user)
        InvitationCodeFactory(created_by=member)

        response = client.get('/onboarding/admin/invitations/')
        assert response.status_code == 200

    def test_admin_invitation_create_get(self, client):
        """Admin can access create invitation form."""
        from apps.members.tests.factories import AdminMemberFactory, UserFactory
        member = AdminMemberFactory()
        user = UserFactory()
        member.user = user
        member.save()
        client.force_login(user)

        response = client.get('/onboarding/admin/invitations/create/')
        assert response.status_code == 200

    def test_admin_invitation_create_post(self, client):
        """Admin can create an invitation code."""
        from apps.members.tests.factories import AdminMemberFactory, UserFactory
        member = AdminMemberFactory()
        user = UserFactory()
        member.user = user
        member.save()
        client.force_login(user)

        response = client.post('/onboarding/admin/invitations/create/', {
            'role': Roles.VOLUNTEER,
            'expires_in_days': 14,
            'max_uses': 1,
            'note': 'Test invitation',
        })
        assert response.status_code == 302  # Redirect on success
        assert InvitationCode.objects.count() == 1

    def test_accept_invitation_get(self, client):
        """Member can access accept invitation form."""
        member = MemberWithUserFactory()
        client.force_login(member.user)

        response = client.get('/onboarding/invitation/')
        assert response.status_code == 200

    def test_accept_invitation_post_valid(self, client):
        """Member can accept a valid invitation code."""
        pastor = PastorFactory()
        inv = InvitationCodeFactory(created_by=pastor, role=Roles.VOLUNTEER)

        member = MemberWithUserFactory()
        client.force_login(member.user)

        response = client.post('/onboarding/invitation/', {
            'code': inv.code,
        })
        assert response.status_code == 302  # Redirect on success
        inv.refresh_from_db()
        assert inv.use_count == 1

    def test_accept_invitation_post_invalid_code(self, client):
        """Invalid code shows error."""
        member = MemberWithUserFactory()
        client.force_login(member.user)

        response = client.post('/onboarding/invitation/', {
            'code': 'INVALID1',
        })
        assert response.status_code == 200  # Re-render form with errors

    def test_non_admin_denied_invitations(self, client):
        """Non-admin redirected from invitation admin views."""
        member = MemberWithUserFactory(role=Roles.MEMBER)
        client.force_login(member.user)

        response = client.get('/onboarding/admin/invitations/')
        assert response.status_code == 302  # Redirect
