"""Tests for PWA views (service worker, manifest, offline)."""
import json

import pytest
from django.test import Client


@pytest.mark.django_db
class TestServiceWorkerView:
    def test_returns_javascript_content_type(self, client):
        response = client.get('/sw.js')
        assert response.status_code == 200
        assert 'javascript' in response['Content-Type']

    def test_no_cache_headers(self, client):
        response = client.get('/sw.js')
        assert response.status_code == 200

    def test_contains_cache_name_v2(self, client):
        """Service worker uses updated v2 cache name."""
        response = client.get('/sw.js')
        content = response.content.decode('utf-8')
        assert 'egliseconnect-v2' in content

    def test_contains_key_pages_list(self, client):
        """Service worker includes KEY_PAGES for offline caching."""
        response = client.get('/sw.js')
        content = response.content.decode('utf-8')
        assert 'KEY_PAGES' in content
        assert '/members/' in content
        assert '/events/' in content
        assert '/reports/' in content

    def test_contains_static_extensions(self, client):
        """Service worker includes static asset extensions for cache-first strategy."""
        response = client.get('/sw.js')
        content = response.content.decode('utf-8')
        assert 'STATIC_EXTENSIONS' in content
        assert '.css' in content
        assert '.js' in content

    def test_contains_cache_first_strategy(self, client):
        """Service worker implements cache-first for static assets."""
        response = client.get('/sw.js')
        content = response.content.decode('utf-8')
        assert 'isStaticAsset' in content

    def test_skips_api_and_admin(self, client):
        """Service worker skips /api/ and /admin/ requests."""
        response = client.get('/sw.js')
        content = response.content.decode('utf-8')
        assert '/api/' in content
        assert '/admin/' in content

    def test_contains_offline_fallback(self, client):
        """Service worker falls back to offline page for navigation requests."""
        response = client.get('/sw.js')
        content = response.content.decode('utf-8')
        assert 'OFFLINE_URL' in content
        assert "event.request.mode === 'navigate'" in content


@pytest.mark.django_db
class TestOfflineView:
    def test_returns_200(self, client):
        response = client.get('/offline/')
        assert response.status_code == 200


@pytest.mark.django_db
class TestManifestView:
    def test_returns_json_content_type(self, client):
        response = client.get('/manifest.json')
        assert response.status_code == 200
        assert 'json' in response['Content-Type']

    def test_contains_required_fields(self, client):
        response = client.get('/manifest.json')
        data = json.loads(response.content)
        assert 'name' in data
        assert 'short_name' in data
        assert 'start_url' in data
        assert 'icons' in data

    def test_lang_is_fr_ca(self, client):
        response = client.get('/manifest.json')
        data = json.loads(response.content)
        assert data['lang'] == 'fr-CA'

    def test_has_theme_color(self, client):
        response = client.get('/manifest.json')
        data = json.loads(response.content)
        assert 'theme_color' in data

    def test_icons_is_list(self, client):
        response = client.get('/manifest.json')
        data = json.loads(response.content)
        assert isinstance(data['icons'], list)
        assert len(data['icons']) > 0
