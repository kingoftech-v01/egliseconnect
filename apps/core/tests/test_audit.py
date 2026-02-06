"""Tests for LoginAudit model and login/logout signals."""
import pytest
from unittest.mock import patch, MagicMock
from django.test import RequestFactory
from django.contrib.auth.signals import user_logged_in, user_login_failed

from apps.core.audit import LoginAudit
from apps.core.signals import get_client_ip, log_successful_login, log_failed_login
from apps.members.tests.factories import MemberFactory, UserFactory


@pytest.mark.django_db
class TestLoginAuditModel:
    """Tests for the LoginAudit model fields and metadata."""

    def test_str_success(self):
        audit = LoginAudit.objects.create(
            email_attempted='user@example.com',
            ip_address='192.168.1.1',
            success=True,
        )
        assert str(audit) == 'user@example.com [OK] 192.168.1.1'

    def test_str_failure(self):
        audit = LoginAudit.objects.create(
            email_attempted='bad@example.com',
            ip_address='10.0.0.1',
            success=False,
            failure_reason='invalid_credentials',
        )
        assert str(audit) == 'bad@example.com [FAIL] 10.0.0.1'

    def test_ordering_newest_first(self):
        a1 = LoginAudit.objects.create(
            email_attempted='first@example.com',
            ip_address='1.1.1.1',
            success=True,
        )
        a2 = LoginAudit.objects.create(
            email_attempted='second@example.com',
            ip_address='2.2.2.2',
            success=True,
        )
        audits = list(LoginAudit.objects.all())
        assert audits[0] == a2
        assert audits[1] == a1

    def test_default_method_is_password(self):
        audit = LoginAudit.objects.create(
            email_attempted='test@example.com',
            ip_address='127.0.0.1',
        )
        assert audit.method == 'password'

    def test_user_nullable(self):
        audit = LoginAudit.objects.create(
            email_attempted='no-user@example.com',
            ip_address='127.0.0.1',
            success=False,
        )
        assert audit.user is None

    def test_user_foreign_key(self):
        user = UserFactory()
        audit = LoginAudit.objects.create(
            user=user,
            email_attempted=user.email,
            ip_address='192.168.0.1',
            success=True,
        )
        assert audit.user == user
        assert user.login_audits.count() == 1

    def test_verbose_names(self):
        meta = LoginAudit._meta
        assert meta.verbose_name == 'Audit de connexion'
        assert meta.verbose_name_plural == 'Audits de connexion'

    def test_blank_fields_default(self):
        audit = LoginAudit.objects.create(
            ip_address='1.2.3.4',
        )
        assert audit.email_attempted == ''
        assert audit.user_agent == ''
        assert audit.failure_reason == ''
        assert audit.success is True

    def test_method_choices(self):
        for method_value, _ in LoginAudit._meta.get_field('method').choices:
            audit = LoginAudit.objects.create(
                email_attempted='test@test.com',
                ip_address='1.1.1.1',
                method=method_value,
            )
            assert audit.method == method_value

    def test_has_uuid_pk(self):
        audit = LoginAudit.objects.create(
            email_attempted='test@test.com',
            ip_address='1.1.1.1',
        )
        assert audit.pk is not None
        assert hasattr(audit, 'created_at')
        assert hasattr(audit, 'updated_at')


@pytest.mark.django_db
class TestGetClientIp:
    """Tests for the get_client_ip helper function."""

    def test_direct_ip(self):
        factory = RequestFactory()
        request = factory.get('/', REMOTE_ADDR='192.168.1.1')
        assert get_client_ip(request) == '192.168.1.1'

    def test_forwarded_ip_single(self):
        factory = RequestFactory()
        request = factory.get('/', HTTP_X_FORWARDED_FOR='10.0.0.1')
        assert get_client_ip(request) == '10.0.0.1'

    def test_forwarded_ip_multiple(self):
        factory = RequestFactory()
        request = factory.get('/', HTTP_X_FORWARDED_FOR='10.0.0.1, 192.168.1.1, 172.16.0.1')
        assert get_client_ip(request) == '10.0.0.1'

    def test_forwarded_ip_with_spaces(self):
        factory = RequestFactory()
        request = factory.get('/', HTTP_X_FORWARDED_FOR='  10.0.0.2 , 192.168.1.1')
        assert get_client_ip(request) == '10.0.0.2'

    def test_no_ip_returns_default(self):
        factory = RequestFactory()
        request = factory.get('/')
        # RequestFactory sets REMOTE_ADDR='127.0.0.1' by default
        ip = get_client_ip(request)
        assert ip == '127.0.0.1'

    def test_forwarded_takes_precedence_over_remote_addr(self):
        factory = RequestFactory()
        request = factory.get(
            '/',
            REMOTE_ADDR='192.168.1.1',
            HTTP_X_FORWARDED_FOR='10.0.0.1',
        )
        assert get_client_ip(request) == '10.0.0.1'


@pytest.mark.django_db
class TestLogSuccessfulLogin:
    """Tests for the log_successful_login signal handler."""

    def _make_request(self, ip='127.0.0.1', user_agent='TestBrowser'):
        factory = RequestFactory()
        request = factory.get('/', REMOTE_ADDR=ip)
        request.META['HTTP_USER_AGENT'] = user_agent
        return request

    def test_creates_audit_on_login(self):
        user = UserFactory()
        request = self._make_request()
        log_successful_login(sender=None, request=request, user=user)

        audit = LoginAudit.objects.last()
        assert audit is not None
        assert audit.success is True
        assert audit.user == user
        assert audit.email_attempted == user.email
        assert audit.ip_address == '127.0.0.1'
        assert audit.user_agent == 'TestBrowser'

    def test_captures_ip_correctly(self):
        user = UserFactory()
        request = self._make_request(ip='203.0.113.50')
        log_successful_login(sender=None, request=request, user=user)

        audit = LoginAudit.objects.last()
        assert audit.ip_address == '203.0.113.50'

    def test_truncates_long_user_agent(self):
        user = UserFactory()
        long_ua = 'X' * 1000
        request = self._make_request(user_agent=long_ua)
        log_successful_login(sender=None, request=request, user=user)

        audit = LoginAudit.objects.last()
        assert len(audit.user_agent) == 500

    def test_user_without_email(self):
        user = UserFactory(email='')
        request = self._make_request()
        log_successful_login(sender=None, request=request, user=user)

        audit = LoginAudit.objects.last()
        assert audit.email_attempted == ''

    def test_user_without_member_profile_no_2fa_update(self):
        user = UserFactory()
        request = self._make_request()
        # No member_profile linked, should not raise
        log_successful_login(sender=None, request=request, user=user)
        assert LoginAudit.objects.count() == 1

    def test_updates_2fa_status_when_totp_exists(self):
        user = UserFactory()
        member = MemberFactory(
            user=user,
            two_factor_enabled=False,
            registration_date=None,
        )
        request = self._make_request()

        mock_qs = MagicMock()
        mock_qs.filter.return_value.exists.return_value = True

        with patch('apps.core.signals.Authenticator', create=True) as MockAuth:
            # Patch the import inside the signal
            with patch.dict('sys.modules', {'allauth.mfa.models': MagicMock()}):
                import importlib
                import apps.core.signals as signals_module
                # Directly call the function and mock the Authenticator inside
                with patch('apps.core.signals.log_successful_login') as _:
                    pass

                # Let's test by directly exercising the function with mocked import
                from unittest.mock import patch as mock_patch
                mock_authenticator = MagicMock()
                mock_authenticator.objects.filter.return_value.exists.return_value = True

                with mock_patch.dict('sys.modules', {
                    'allauth.mfa.models': MagicMock(Authenticator=mock_authenticator),
                    'allauth.mfa': MagicMock(),
                    'allauth': MagicMock(),
                }):
                    log_successful_login(sender=None, request=request, user=user)

        member.refresh_from_db()
        assert member.two_factor_enabled is True

    def test_does_not_update_2fa_if_already_enabled(self):
        user = UserFactory()
        member = MemberFactory(
            user=user,
            two_factor_enabled=True,
            registration_date=None,
        )
        request = self._make_request()

        mock_authenticator = MagicMock()
        mock_authenticator.objects.filter.return_value.exists.return_value = True

        with patch.dict('sys.modules', {
            'allauth.mfa.models': MagicMock(Authenticator=mock_authenticator),
            'allauth.mfa': MagicMock(),
            'allauth': MagicMock(),
        }):
            log_successful_login(sender=None, request=request, user=user)

        member.refresh_from_db()
        assert member.two_factor_enabled is True

    def test_does_not_update_2fa_if_no_totp(self):
        user = UserFactory()
        member = MemberFactory(
            user=user,
            two_factor_enabled=False,
            registration_date=None,
        )
        request = self._make_request()

        mock_authenticator = MagicMock()
        mock_authenticator.objects.filter.return_value.exists.return_value = False

        with patch.dict('sys.modules', {
            'allauth.mfa.models': MagicMock(Authenticator=mock_authenticator),
            'allauth.mfa': MagicMock(),
            'allauth': MagicMock(),
        }):
            log_successful_login(sender=None, request=request, user=user)

        member.refresh_from_db()
        assert member.two_factor_enabled is False

    def test_2fa_check_exception_handled_silently(self):
        user = UserFactory()
        member = MemberFactory(
            user=user,
            two_factor_enabled=False,
            registration_date=None,
        )
        request = self._make_request()

        # Force an import error for allauth.mfa.models
        with patch.dict('sys.modules', {'allauth.mfa.models': None}):
            log_successful_login(sender=None, request=request, user=user)

        # No crash, audit still created
        assert LoginAudit.objects.count() == 1
        member.refresh_from_db()
        assert member.two_factor_enabled is False

    def test_empty_user_agent(self):
        user = UserFactory()
        factory = RequestFactory()
        request = factory.get('/', REMOTE_ADDR='1.2.3.4')
        # No user agent set
        log_successful_login(sender=None, request=request, user=user)

        audit = LoginAudit.objects.last()
        assert audit.user_agent == ''


@pytest.mark.django_db
class TestLogFailedLogin:
    """Tests for the log_failed_login signal handler."""

    def _make_request(self, ip='1.2.3.4', user_agent='BadBot'):
        factory = RequestFactory()
        request = factory.get('/', REMOTE_ADDR=ip)
        request.META['HTTP_USER_AGENT'] = user_agent
        return request

    def test_creates_audit_on_failure(self):
        request = self._make_request()
        log_failed_login(
            sender=None,
            credentials={'email': 'bad@test.com'},
            request=request,
        )

        audit = LoginAudit.objects.last()
        assert audit is not None
        assert audit.success is False
        assert audit.email_attempted == 'bad@test.com'
        assert audit.ip_address == '1.2.3.4'
        assert audit.user_agent == 'BadBot'
        assert audit.failure_reason == 'invalid_credentials'
        assert audit.user is None

    def test_uses_username_when_no_email(self):
        request = self._make_request()
        log_failed_login(
            sender=None,
            credentials={'username': 'baduser'},
            request=request,
        )

        audit = LoginAudit.objects.last()
        assert audit.email_attempted == 'baduser'

    def test_empty_credentials(self):
        request = self._make_request()
        log_failed_login(
            sender=None,
            credentials={},
            request=request,
        )

        audit = LoginAudit.objects.last()
        assert audit.email_attempted == ''

    def test_no_request_does_not_create_audit(self):
        log_failed_login(
            sender=None,
            credentials={'email': 'bad@test.com'},
            request=None,
        )
        assert LoginAudit.objects.count() == 0

    def test_captures_forwarded_ip(self):
        factory = RequestFactory()
        request = factory.get(
            '/',
            HTTP_X_FORWARDED_FOR='203.0.113.1, 10.0.0.1',
            REMOTE_ADDR='192.168.1.1',
        )
        request.META['HTTP_USER_AGENT'] = 'SomeBot'
        log_failed_login(
            sender=None,
            credentials={'email': 'test@example.com'},
            request=request,
        )

        audit = LoginAudit.objects.last()
        assert audit.ip_address == '203.0.113.1'

    def test_truncates_long_user_agent(self):
        long_ua = 'A' * 1000
        request = self._make_request(user_agent=long_ua)
        log_failed_login(
            sender=None,
            credentials={'email': 'test@test.com'},
            request=request,
        )

        audit = LoginAudit.objects.last()
        assert len(audit.user_agent) == 500


@pytest.mark.django_db
class TestSignalIntegration:
    """Integration test: signals actually fire when connected."""

    def test_user_logged_in_signal_connected(self):
        """Verify the receiver is connected to user_logged_in."""
        receivers = [r[1]() for r in user_logged_in.receivers if r[1]() is not None]
        # Check our handler is registered
        handler_found = any(
            getattr(r, '__name__', '') == 'log_successful_login'
            for r in receivers
        )
        assert handler_found

    def test_user_login_failed_signal_connected(self):
        """Verify the receiver is connected to user_login_failed."""
        receivers = [r[1]() for r in user_login_failed.receivers if r[1]() is not None]
        handler_found = any(
            getattr(r, '__name__', '') == 'log_failed_login'
            for r in receivers
        )
        assert handler_found
