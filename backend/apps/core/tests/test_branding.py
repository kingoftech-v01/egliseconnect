"""Tests for church branding model, views, and context processor."""
import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from apps.core.constants import Roles
from apps.core.context_processors import branding, language_context
from apps.core.forms import ChurchBrandingForm
from apps.core.models_extended import ChurchBranding
from apps.members.tests.factories import MemberWithUserFactory, UserFactory

User = get_user_model()


@pytest.mark.django_db
class TestChurchBrandingModel:
    def test_create_branding(self):
        brand = ChurchBranding.objects.create(
            church_name='Eglise Test',
            primary_color='#1a73e8',
            secondary_color='#6c757d',
            accent_color='#28a745',
        )
        assert brand.church_name == 'Eglise Test'
        assert brand.is_active is True

    def test_str_representation(self):
        brand = ChurchBranding.objects.create(church_name='Eglise ABC')
        assert str(brand) == 'Eglise ABC'

    def test_get_current_returns_first(self):
        ChurchBranding.objects.create(church_name='First')
        ChurchBranding.objects.create(church_name='Second')
        current = ChurchBranding.get_current()
        assert current is not None

    def test_get_current_returns_none_when_empty(self):
        result = ChurchBranding.get_current()
        assert result is None

    def test_default_colors(self):
        brand = ChurchBranding.objects.create(church_name='Test')
        assert brand.primary_color == '#1a73e8'
        assert brand.secondary_color == '#6c757d'
        assert brand.accent_color == '#28a745'

    def test_optional_fields_blank(self):
        brand = ChurchBranding.objects.create(church_name='Minimal')
        assert brand.address == ''
        assert brand.phone == ''
        assert brand.email == ''
        assert brand.website == ''


@pytest.mark.django_db
class TestChurchBrandingForm:
    def test_valid_form(self):
        form = ChurchBrandingForm(data={
            'church_name': 'Test Church',
            'primary_color': '#ff0000',
            'secondary_color': '#00ff00',
            'accent_color': '#0000ff',
        })
        assert form.is_valid()

    def test_required_church_name(self):
        form = ChurchBrandingForm(data={
            'primary_color': '#ff0000',
        })
        assert not form.is_valid()
        assert 'church_name' in form.errors

    def test_form_saves(self):
        form = ChurchBrandingForm(data={
            'church_name': 'Saved Church',
            'primary_color': '#123456',
            'secondary_color': '#654321',
            'accent_color': '#abcdef',
        })
        assert form.is_valid()
        instance = form.save()
        assert instance.pk is not None
        assert instance.church_name == 'Saved Church'


@pytest.mark.django_db
class TestBrandingContextProcessor:
    def test_returns_branding(self):
        ChurchBranding.objects.create(church_name='Context Test')
        factory = RequestFactory()
        request = factory.get('/')
        context = branding(request)
        assert 'church_branding' in context
        assert context['church_branding'].church_name == 'Context Test'

    def test_returns_none_when_no_branding(self):
        factory = RequestFactory()
        request = factory.get('/')
        context = branding(request)
        assert context['church_branding'] is None

    def test_language_context(self):
        factory = RequestFactory()
        request = factory.get('/')
        context = language_context(request)
        assert 'current_language' in context
        assert context['current_language'] in ['fr', 'en', 'fr-ca']


@pytest.mark.django_db
class TestBrandingSettingsView:
    def test_requires_login(self, client):
        response = client.get('/settings/branding/')
        assert response.status_code == 302

    def test_requires_admin(self, client):
        member = MemberWithUserFactory(role=Roles.MEMBER)
        client.force_login(member.user)
        response = client.get('/settings/branding/')
        assert response.status_code == 302

    def test_admin_can_access(self, client):
        admin = MemberWithUserFactory(role=Roles.ADMIN)
        client.force_login(admin.user)
        response = client.get('/settings/branding/')
        assert response.status_code == 200

    def test_pastor_can_access(self, client):
        pastor = MemberWithUserFactory(role=Roles.PASTOR)
        client.force_login(pastor.user)
        response = client.get('/settings/branding/')
        assert response.status_code == 200

    def test_superuser_can_access(self, client):
        user = User.objects.create_superuser(
            username='superadmin', password='Admin123!',
            email='super@test.com',
        )
        client.force_login(user)
        response = client.get('/settings/branding/')
        assert response.status_code == 200

    def test_save_branding(self, client):
        admin = MemberWithUserFactory(role=Roles.ADMIN)
        client.force_login(admin.user)
        response = client.post('/settings/branding/', {
            'church_name': 'New Church Name',
            'primary_color': '#ff0000',
            'secondary_color': '#00ff00',
            'accent_color': '#0000ff',
        })
        assert response.status_code == 302
        brand = ChurchBranding.get_current()
        assert brand.church_name == 'New Church Name'
