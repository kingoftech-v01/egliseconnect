"""Tests for feature flag template tags and API versioning middleware."""
import pytest
from django.template import Template, Context
from django.test import RequestFactory

from apps.core.middleware_api import APIDeprecationHeadersMiddleware
from apps.members.tests.factories import MemberWithUserFactory


@pytest.mark.django_db
class TestFeatureFlagTemplateTags:
    def test_feature_flag_tag_renders(self):
        """Test that feature_flag tag renders without error."""
        factory = RequestFactory()
        request = factory.get('/')

        template = Template(
            '{% load custom_tags %}'
            '{% feature_flag "test_flag" as is_active %}'
            '{% if is_active %}ON{% else %}OFF{% endif %}'
        )
        context = Context({'request': request})
        result = template.render(context)
        # Flag doesn't exist, so should be OFF
        assert 'OFF' in result

    def test_feature_switch_tag(self):
        """Test that feature_switch tag renders."""
        template = Template(
            '{% load custom_tags %}'
            '{% feature_switch "test_switch" as is_active %}'
            '{% if is_active %}ON{% else %}OFF{% endif %}'
        )
        context = Context({})
        result = template.render(context)
        assert 'OFF' in result

    def test_feature_sample_tag(self):
        """Test that feature_sample tag renders."""
        factory = RequestFactory()
        request = factory.get('/')

        template = Template(
            '{% load custom_tags %}'
            '{% feature_sample "test_sample" as is_active %}'
            '{% if is_active %}ON{% else %}OFF{% endif %}'
        )
        context = Context({'request': request})
        result = template.render(context)
        assert 'OFF' in result

    def test_render_breadcrumbs_tag(self):
        """Test breadcrumb rendering template tag."""
        template = Template(
            '{% load custom_tags %}'
            '{% render_breadcrumbs breadcrumbs %}'
        )
        context = Context({
            'breadcrumbs': [
                ('Accueil', '/'),
                ('Membres', '/members/'),
                ('Jean', None),
            ],
        })
        result = template.render(context)
        assert 'Accueil' in result
        assert 'Membres' in result
        assert 'Jean' in result


class TestAPIDeprecationHeadersMiddleware:
    def test_v1_gets_api_version_header(self):
        factory = RequestFactory()
        request = factory.get('/api/v1/members/')

        def get_response(req):
            from django.http import HttpResponse
            return HttpResponse('OK')

        middleware = APIDeprecationHeadersMiddleware(get_response)
        response = middleware(request)

        assert response['API-Version'] == 'v1'
        assert response['Deprecation'] == 'false'

    def test_v2_gets_api_version_header(self):
        factory = RequestFactory()
        request = factory.get('/api/v2/members/')

        def get_response(req):
            from django.http import HttpResponse
            return HttpResponse('OK')

        middleware = APIDeprecationHeadersMiddleware(get_response)
        response = middleware(request)

        assert response['API-Version'] == 'v2'

    def test_non_api_no_headers(self):
        factory = RequestFactory()
        request = factory.get('/members/')

        def get_response(req):
            from django.http import HttpResponse
            return HttpResponse('OK')

        middleware = APIDeprecationHeadersMiddleware(get_response)
        response = middleware(request)

        assert 'API-Version' not in response


@pytest.mark.django_db
class TestAPIKeyManagementView:
    def test_requires_login(self, client):
        response = client.get('/settings/api-keys/')
        assert response.status_code == 302

    def test_requires_admin(self, client):
        from apps.core.constants import Roles
        member = MemberWithUserFactory(role=Roles.MEMBER)
        client.force_login(member.user)
        response = client.get('/settings/api-keys/')
        assert response.status_code == 302

    def test_admin_can_access(self, client):
        from apps.core.constants import Roles
        admin = MemberWithUserFactory(role=Roles.ADMIN)
        client.force_login(admin.user)
        response = client.get('/settings/api-keys/')
        assert response.status_code == 200


@pytest.mark.django_db
class TestLanguageSwitcher:
    def test_set_language_french(self, client):
        from apps.core.constants import Roles
        admin = MemberWithUserFactory(role=Roles.ADMIN)
        client.force_login(admin.user)
        response = client.post('/settings/set-language/', {
            'language': 'fr',
            'next': '/',
        })
        assert response.status_code == 302

    def test_set_language_english(self, client):
        from apps.core.constants import Roles
        admin = MemberWithUserFactory(role=Roles.ADMIN)
        client.force_login(admin.user)
        response = client.post('/settings/set-language/', {
            'language': 'en',
            'next': '/',
        })
        assert response.status_code == 302

    def test_set_invalid_language(self, client):
        from apps.core.constants import Roles
        admin = MemberWithUserFactory(role=Roles.ADMIN)
        client.force_login(admin.user)
        response = client.post('/settings/set-language/', {
            'language': 'xx',
            'next': '/',
        })
        assert response.status_code == 302

    def test_requires_login(self, client):
        response = client.post('/settings/set-language/', {
            'language': 'en',
        })
        assert response.status_code == 302
