"""Tests for finance delegation views."""
import pytest

from apps.core.constants import Roles
from apps.communication.models import Notification
from apps.donations.models import FinanceDelegation
from apps.members.tests.factories import (
    MemberFactory, PastorFactory, MemberWithUserFactory, UserFactory,
)


def _pastor_login(client):
    """Create a pastor with user and log them in."""
    pastor = PastorFactory()
    user = UserFactory()
    pastor.user = user
    pastor.save()
    client.force_login(user)
    return pastor


@pytest.mark.django_db
class TestFinanceDelegationsView:
    """Tests for finance_delegations list view."""

    def test_pastor_can_view(self, client):
        _pastor_login(client)
        response = client.get('/donations/delegations/')
        assert response.status_code == 200

    def test_non_pastor_denied(self, client):
        member = MemberWithUserFactory(role=Roles.MEMBER)
        client.force_login(member.user)
        response = client.get('/donations/delegations/')
        assert response.status_code == 302

    def test_treasurer_denied(self, client):
        member = MemberWithUserFactory(role=Roles.TREASURER)
        client.force_login(member.user)
        response = client.get('/donations/delegations/')
        assert response.status_code == 302


@pytest.mark.django_db
class TestDelegateFinanceAccess:
    """Tests for granting finance access."""

    def test_grant_access(self, client):
        pastor = _pastor_login(client)
        target = MemberFactory(role=Roles.DEACON, is_active=True)
        response = client.post('/donations/delegations/grant/', {
            'member': str(target.pk),
            'reason': 'Besoin temporaire',
        })
        assert response.status_code == 302
        assert FinanceDelegation.objects.filter(
            delegated_to=target, revoked_at__isnull=True
        ).exists()

    def test_grant_creates_notification(self, client):
        _pastor_login(client)
        target = MemberFactory(role=Roles.DEACON, is_active=True)
        client.post('/donations/delegations/grant/', {
            'member': str(target.pk),
        })
        assert Notification.objects.filter(
            member=target,
            title='Accès financier accordé',
        ).exists()

    def test_no_duplicate_delegation(self, client):
        pastor = _pastor_login(client)
        target = MemberFactory(role=Roles.DEACON, is_active=True)
        FinanceDelegation.objects.create(
            delegated_to=target, delegated_by=pastor,
        )
        client.post('/donations/delegations/grant/', {
            'member': str(target.pk),
        })
        # Should still be just 1
        assert FinanceDelegation.objects.filter(
            delegated_to=target, revoked_at__isnull=True
        ).count() == 1

    def test_invalid_member(self, client):
        _pastor_login(client)
        response = client.post('/donations/delegations/grant/', {
            'member': 'invalid-uuid',
        })
        assert response.status_code == 302


@pytest.mark.django_db
class TestRevokeFinanceAccess:
    """Tests for revoking finance access."""

    def test_revoke_access(self, client):
        pastor = _pastor_login(client)
        target = MemberFactory()
        delegation = FinanceDelegation.objects.create(
            delegated_to=target, delegated_by=pastor,
        )
        response = client.post(f'/donations/delegations/{delegation.pk}/revoke/')
        assert response.status_code == 302
        delegation.refresh_from_db()
        assert delegation.revoked_at is not None

    def test_revoke_creates_notification(self, client):
        pastor = _pastor_login(client)
        target = MemberFactory()
        delegation = FinanceDelegation.objects.create(
            delegated_to=target, delegated_by=pastor,
        )
        client.post(f'/donations/delegations/{delegation.pk}/revoke/')
        assert Notification.objects.filter(
            member=target,
            title='Accès financier révoqué',
        ).exists()

    def test_non_pastor_cannot_revoke(self, client):
        member = MemberWithUserFactory(role=Roles.MEMBER)
        client.force_login(member.user)
        pastor = PastorFactory()
        target = MemberFactory()
        delegation = FinanceDelegation.objects.create(
            delegated_to=target, delegated_by=pastor,
        )
        response = client.post(f'/donations/delegations/{delegation.pk}/revoke/')
        assert response.status_code == 302
        delegation.refresh_from_db()
        assert delegation.revoked_at is None  # Not revoked
