"""Tests for allauth template overrides (W3CRM styling)."""
import pytest
from django.test import Client
from django.urls import reverse

from apps.members.tests.factories import UserFactory, MemberFactory
from apps.core.constants import Roles


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def user():
    """User with password for auth tests."""
    user = UserFactory()
    user.set_password('TestPass123!')
    user.save()
    return user


@pytest.fixture
def member_user():
    """User with member profile."""
    user = UserFactory()
    user.set_password('TestPass123!')
    user.save()
    MemberFactory(user=user, role=Roles.MEMBER)
    return user


# ── Entrance pages (public, W3CRM standalone layout) ──


@pytest.mark.django_db
class TestLoginPage:
    """Tests for the login page template override."""

    def test_login_page_renders(self, client):
        response = client.get(reverse('account_login'))
        assert response.status_code == 200

    def test_login_page_has_w3crm_classes(self, client):
        response = client.get(reverse('account_login'))
        content = response.content.decode()
        assert 'authincation' in content
        assert 'login-form' in content

    def test_login_page_has_form(self, client):
        response = client.get(reverse('account_login'))
        content = response.content.decode()
        assert 'form-control' in content
        assert 'Se connecter' in content

    def test_login_page_has_links(self, client):
        response = client.get(reverse('account_login'))
        content = response.content.decode()
        assert 'Mot de passe oublie' in content
        assert 'Inscrivez-vous' in content

    def test_login_post_invalid(self, client):
        response = client.post(reverse('account_login'), {
            'login': 'bad@email.com',
            'password': 'wrongpass',
        })
        assert response.status_code == 200
        content = response.content.decode()
        assert 'authincation' in content


@pytest.mark.django_db
class TestSignupPage:
    """Tests for the signup page template override."""

    def test_signup_page_renders(self, client):
        response = client.get(reverse('account_signup'))
        assert response.status_code == 200

    def test_signup_page_has_w3crm_classes(self, client):
        response = client.get(reverse('account_signup'))
        content = response.content.decode()
        assert 'authincation' in content
        assert 'login-form' in content
        assert 'Inscription' in content

    def test_signup_page_has_form_fields(self, client):
        response = client.get(reverse('account_signup'))
        content = response.content.decode()
        assert 'form-control' in content
        assert "S&#x27;inscrire" in content or "S'inscrire" in content


@pytest.mark.django_db
class TestPasswordResetPage:
    """Tests for the password reset page template override."""

    def test_password_reset_renders(self, client):
        response = client.get(reverse('account_reset_password'))
        assert response.status_code == 200

    def test_password_reset_has_w3crm_classes(self, client):
        response = client.get(reverse('account_reset_password'))
        content = response.content.decode()
        assert 'authincation' in content
        assert 'login-form' in content
        assert 'Mot de passe oublie' in content

    def test_password_reset_post(self, client, user):
        response = client.post(reverse('account_reset_password'), {
            'email': user.email,
        })
        assert response.status_code == 302


@pytest.mark.django_db
class TestPasswordResetDonePage:
    """Tests for the password reset done page."""

    def test_password_reset_done_renders(self, client):
        response = client.get(reverse('account_reset_password_done'))
        assert response.status_code == 200
        content = response.content.decode()
        assert 'authincation' in content
        assert 'envoye' in content.lower() or 'E-mail' in content


@pytest.mark.django_db
class TestVerificationSentPage:
    """Tests for the verification sent page."""

    def test_verification_sent_renders(self, client):
        response = client.get(reverse('account_email_verification_sent'))
        assert response.status_code == 200
        content = response.content.decode()
        assert 'authincation' in content


@pytest.mark.django_db
class TestLogoutPage:
    """Tests for the logout page template override."""

    def test_logout_renders_for_authenticated(self, client, user):
        client.force_login(user)
        response = client.get(reverse('account_logout'))
        assert response.status_code == 200
        content = response.content.decode()
        assert 'authincation' in content
        assert 'deconnecter' in content.lower()

    def test_logout_post(self, client, user):
        client.force_login(user)
        response = client.post(reverse('account_logout'))
        assert response.status_code == 302


@pytest.mark.django_db
class TestRequestLoginCodePage:
    """Tests for the login code request page."""

    def test_request_login_code_renders(self, client):
        response = client.get(reverse('account_request_login_code'))
        assert response.status_code == 200
        content = response.content.decode()
        assert 'authincation' in content
        assert 'code' in content.lower()


@pytest.mark.django_db
class TestReauthenticatePage:
    """Tests for the reauthenticate page."""

    def test_reauthenticate_requires_login(self, client):
        response = client.get(reverse('account_reauthenticate'))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url


# ── Manage pages (logged-in, dashboard layout) ──


@pytest.mark.django_db
class TestPasswordChangePage:
    """Tests for the password change page template override."""

    def test_password_change_requires_login(self, client):
        response = client.get(reverse('account_change_password'))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_password_change_renders(self, client, user):
        client.force_login(user)
        response = client.get(reverse('account_change_password'))
        assert response.status_code == 200
        content = response.content.decode()
        assert 'main-wrapper' in content
        assert 'Changer le mot de passe' in content

    def test_password_change_has_form(self, client, user):
        client.force_login(user)
        response = client.get(reverse('account_change_password'))
        content = response.content.decode()
        assert 'form-control' in content


@pytest.mark.django_db
class TestEmailManagementPage:
    """Tests for the email management page template override."""

    def test_email_requires_login(self, client):
        response = client.get(reverse('account_email'))
        assert response.status_code == 302

    def test_email_page_renders(self, client, user):
        client.force_login(user)
        response = client.get(reverse('account_email'))
        assert response.status_code == 200
        content = response.content.decode()
        assert 'main-wrapper' in content
        assert 'e-mail' in content.lower()


@pytest.mark.django_db
class TestMFAIndexPage:
    """Tests for the MFA index page template override."""

    def test_mfa_index_requires_login(self, client):
        response = client.get(reverse('mfa_index'))
        assert response.status_code == 302

    def test_mfa_index_renders(self, client, user):
        client.force_login(user)
        response = client.get(reverse('mfa_index'))
        assert response.status_code == 200
        content = response.content.decode()
        assert 'main-wrapper' in content
        assert 'deux facteurs' in content.lower() or '2FA' in content

    def test_mfa_index_shows_totp_section(self, client, user):
        client.force_login(user)
        response = client.get(reverse('mfa_index'))
        content = response.content.decode()
        assert 'authentification' in content.lower()
        assert 'Activer' in content


@pytest.mark.django_db
class TestTOTPActivatePage:
    """Tests for the TOTP activation page."""

    def test_totp_activate_requires_login(self, client):
        response = client.get(reverse('mfa_activate_totp'))
        assert response.status_code == 302

    def test_totp_activate_requires_reauth(self, client, user):
        """TOTP activate requires reauthentication, redirects to reauth page."""
        client.force_login(user)
        response = client.get(reverse('mfa_activate_totp'))
        assert response.status_code == 302
        assert '/accounts/reauthenticate/' in response.url


@pytest.mark.django_db
class TestRecoveryCodesGeneratePage:
    """Tests for the recovery codes generate page."""

    def test_generate_requires_login(self, client):
        response = client.get(reverse('mfa_generate_recovery_codes'))
        assert response.status_code == 302

    def test_generate_requires_reauth(self, client, user):
        """Recovery codes generate requires reauthentication."""
        client.force_login(user)
        response = client.get(reverse('mfa_generate_recovery_codes'))
        assert response.status_code == 302
        assert '/accounts/reauthenticate/' in response.url


# ── Template filter test ──


@pytest.mark.django_db
class TestAddClassFilter:
    """Tests for the add_class template filter."""

    def test_add_class_on_login_form(self, client):
        """Login page should render form fields with form-control class."""
        response = client.get(reverse('account_login'))
        content = response.content.decode()
        assert 'class="form-control"' in content
