"""Tests for frontend audit views (login_audit_list, two_factor_status)."""
import pytest
from django.test import Client
from django.urls import reverse

from apps.core.audit import LoginAudit
from apps.core.constants import Roles, MembershipStatus
from apps.members.tests.factories import MemberFactory, UserFactory


@pytest.mark.django_db
class TestLoginAuditListView:
    """Tests for the login_audit_list frontend view."""

    def _url(self):
        return reverse('frontend:audit:login_audit_list')

    def test_anonymous_redirected_to_login(self):
        client = Client()
        response = client.get(self._url())
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_admin_can_access(self):
        user = UserFactory()
        MemberFactory(user=user, role=Roles.ADMIN, registration_date=None)
        client = Client()
        client.force_login(user)
        response = client.get(self._url())
        assert response.status_code == 200

    def test_pastor_can_access(self):
        user = UserFactory()
        MemberFactory(user=user, role=Roles.PASTOR, registration_date=None)
        client = Client()
        client.force_login(user)
        response = client.get(self._url())
        assert response.status_code == 200

    def test_regular_member_redirected(self):
        user = UserFactory()
        MemberFactory(user=user, role=Roles.MEMBER, registration_date=None)
        client = Client()
        client.force_login(user)
        response = client.get(self._url())
        assert response.status_code == 302
        assert response['Location'] == '/'

    def test_treasurer_redirected(self):
        user = UserFactory()
        MemberFactory(user=user, role=Roles.TREASURER, registration_date=None)
        client = Client()
        client.force_login(user)
        response = client.get(self._url())
        assert response.status_code == 302
        assert response['Location'] == '/'

    def test_volunteer_redirected(self):
        user = UserFactory()
        MemberFactory(user=user, role=Roles.VOLUNTEER, registration_date=None)
        client = Client()
        client.force_login(user)
        response = client.get(self._url())
        assert response.status_code == 302

    def test_no_member_profile_redirected(self):
        user = UserFactory()
        client = Client()
        client.force_login(user)
        response = client.get(self._url())
        assert response.status_code == 302
        assert response['Location'] == '/'

    def test_shows_audits_in_context(self):
        user = UserFactory()
        MemberFactory(user=user, role=Roles.ADMIN, registration_date=None)

        client = Client()
        client.force_login(user)
        # force_login triggers user_logged_in signal, which creates an audit.
        # Clear everything first to have a clean baseline.
        LoginAudit.objects.all().delete()

        LoginAudit.objects.create(
            email_attempted='user1@test.com',
            ip_address='1.1.1.1',
            success=True,
        )
        LoginAudit.objects.create(
            email_attempted='user2@test.com',
            ip_address='2.2.2.2',
            success=False,
        )

        response = client.get(self._url())
        assert response.status_code == 200
        assert len(response.context['audits']) == 2
        assert response.context['page_title'] == 'Journal de connexions'

    def test_audits_ordered_newest_first(self):
        user = UserFactory()
        MemberFactory(user=user, role=Roles.ADMIN, registration_date=None)

        client = Client()
        client.force_login(user)
        # Clear audits created by force_login
        LoginAudit.objects.all().delete()

        a1 = LoginAudit.objects.create(
            email_attempted='first@test.com',
            ip_address='1.1.1.1',
            success=True,
        )
        a2 = LoginAudit.objects.create(
            email_attempted='second@test.com',
            ip_address='2.2.2.2',
            success=True,
        )

        response = client.get(self._url())
        audits_list = list(response.context['audits'])
        assert audits_list[0].pk == a2.pk
        assert audits_list[1].pk == a1.pk

    def test_limited_to_200_audits(self):
        user = UserFactory()
        MemberFactory(user=user, role=Roles.ADMIN, registration_date=None)

        # Create 210 audits
        for i in range(210):
            LoginAudit.objects.create(
                email_attempted=f'user{i}@test.com',
                ip_address='1.1.1.1',
            )

        client = Client()
        client.force_login(user)
        response = client.get(self._url())
        assert len(response.context['audits']) == 200


@pytest.mark.django_db
class TestTwoFactorStatusView:
    """Tests for the two_factor_status frontend view."""

    def _url(self):
        return reverse('frontend:audit:two_factor_status')

    def test_anonymous_redirected_to_login(self):
        client = Client()
        response = client.get(self._url())
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_admin_can_access(self):
        user = UserFactory()
        MemberFactory(user=user, role=Roles.ADMIN, registration_date=None)
        client = Client()
        client.force_login(user)
        response = client.get(self._url())
        assert response.status_code == 200

    def test_pastor_can_access(self):
        user = UserFactory()
        MemberFactory(user=user, role=Roles.PASTOR, registration_date=None)
        client = Client()
        client.force_login(user)
        response = client.get(self._url())
        assert response.status_code == 200

    def test_regular_member_redirected(self):
        user = UserFactory()
        MemberFactory(user=user, role=Roles.MEMBER, registration_date=None)
        client = Client()
        client.force_login(user)
        response = client.get(self._url())
        assert response.status_code == 302
        assert response['Location'] == '/'

    def test_no_member_profile_redirected(self):
        user = UserFactory()
        client = Client()
        client.force_login(user)
        response = client.get(self._url())
        assert response.status_code == 302
        assert response['Location'] == '/'

    def test_shows_members_without_2fa(self):
        admin_user = UserFactory()
        MemberFactory(user=admin_user, role=Roles.ADMIN, registration_date=None)

        # Create members without 2FA
        user_no_2fa = UserFactory()
        member_no_2fa = MemberFactory(
            user=user_no_2fa,
            two_factor_enabled=False,
            registration_date=None,
        )

        client = Client()
        client.force_login(admin_user)
        response = client.get(self._url())
        assert response.status_code == 200
        members_without = list(response.context['members_without_2fa'])
        pks = [m.pk for m in members_without]
        assert member_no_2fa.pk in pks

    def test_shows_members_with_2fa(self):
        admin_user = UserFactory()
        MemberFactory(user=admin_user, role=Roles.ADMIN, registration_date=None)

        # Create member with 2FA
        user_2fa = UserFactory()
        member_2fa = MemberFactory(
            user=user_2fa,
            two_factor_enabled=True,
            registration_date=None,
        )

        client = Client()
        client.force_login(admin_user)
        response = client.get(self._url())
        assert response.status_code == 200
        members_with = list(response.context['members_with_2fa'])
        pks = [m.pk for m in members_with]
        assert member_2fa.pk in pks

    def test_page_title(self):
        admin_user = UserFactory()
        MemberFactory(user=admin_user, role=Roles.ADMIN, registration_date=None)

        client = Client()
        client.force_login(admin_user)
        response = client.get(self._url())
        assert response.context['page_title'] == 'Statut 2FA'

    def test_excludes_inactive_members(self):
        admin_user = UserFactory()
        MemberFactory(user=admin_user, role=Roles.ADMIN, registration_date=None)

        # Create soft-deleted member (is_active=False)
        user_inactive = UserFactory()
        inactive_member = MemberFactory(
            user=user_inactive,
            two_factor_enabled=False,
            registration_date=None,
        )
        inactive_member.is_active = False
        inactive_member.save()

        client = Client()
        client.force_login(admin_user)
        response = client.get(self._url())
        members_without = list(response.context['members_without_2fa'])
        pks = [m.pk for m in members_without]
        assert inactive_member.pk not in pks

    def test_excludes_members_without_user(self):
        admin_user = UserFactory()
        MemberFactory(user=admin_user, role=Roles.ADMIN, registration_date=None)

        # Create member without user account
        member_no_user = MemberFactory(two_factor_enabled=False)

        client = Client()
        client.force_login(admin_user)
        response = client.get(self._url())
        members_without = list(response.context['members_without_2fa'])
        pks = [m.pk for m in members_without]
        assert member_no_user.pk not in pks
