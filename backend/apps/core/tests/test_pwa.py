"""Tests for PWA views: service worker, manifest, and offline page."""
import pytest
from django.test import Client


class TestServiceWorkerView:
    """Tests for the service worker endpoint at /sw.js."""

    def test_service_worker_url_accessible(self):
        client = Client()
        response = client.get('/sw.js')
        assert response.status_code == 200

    def test_service_worker_content_type(self):
        client = Client()
        response = client.get('/sw.js')
        assert 'javascript' in response['Content-Type']

    def test_service_worker_no_cache(self):
        client = Client()
        response = client.get('/sw.js')
        cache_control = response.get('Cache-Control', '')
        # never_cache decorator sets max-age=0, no-cache, no-store, must-revalidate
        assert 'no-cache' in cache_control or 'max-age=0' in cache_control


class TestManifestView:
    """Tests for the PWA manifest endpoint at /manifest.json."""

    def test_manifest_url_accessible(self):
        client = Client()
        response = client.get('/manifest.json')
        assert response.status_code == 200

    def test_manifest_json_content_type(self):
        client = Client()
        response = client.get('/manifest.json')
        assert 'json' in response['Content-Type']

    def test_manifest_has_name(self):
        client = Client()
        response = client.get('/manifest.json')
        data = response.json()
        assert data['name'] == 'EgliseConnect'

    def test_manifest_has_short_name(self):
        client = Client()
        response = client.get('/manifest.json')
        data = response.json()
        assert data['short_name'] == 'EgliseConnect'

    def test_manifest_has_start_url(self):
        client = Client()
        response = client.get('/manifest.json')
        data = response.json()
        assert data['start_url'] == '/'

    def test_manifest_has_display(self):
        client = Client()
        response = client.get('/manifest.json')
        data = response.json()
        assert data['display'] == 'standalone'

    def test_manifest_has_lang(self):
        client = Client()
        response = client.get('/manifest.json')
        data = response.json()
        assert data['lang'] == 'fr-CA'

    def test_manifest_has_theme_color(self):
        client = Client()
        response = client.get('/manifest.json')
        data = response.json()
        assert data['theme_color'] == '#1a73e8'

    def test_manifest_has_background_color(self):
        client = Client()
        response = client.get('/manifest.json')
        data = response.json()
        assert data['background_color'] == '#ffffff'

    def test_manifest_has_icons(self):
        client = Client()
        response = client.get('/manifest.json')
        data = response.json()
        assert 'icons' in data
        assert len(data['icons']) >= 1
        assert data['icons'][0]['sizes'] == '192x192'

    def test_manifest_has_description(self):
        client = Client()
        response = client.get('/manifest.json')
        data = response.json()
        assert 'description' in data

    def test_manifest_has_orientation(self):
        client = Client()
        response = client.get('/manifest.json')
        data = response.json()
        assert data['orientation'] == 'any'


class TestOfflineView:
    """Tests for the offline fallback page at /offline/."""

    def test_offline_page_accessible(self):
        client = Client()
        response = client.get('/offline/')
        assert response.status_code == 200

    def test_offline_page_uses_template(self):
        client = Client()
        response = client.get('/offline/')
        templates_used = [t.name for t in response.templates]
        assert 'pwa/offline.html' in templates_used

    def test_offline_page_no_login_required(self):
        """Offline page should be accessible without authentication."""
        client = Client()
        response = client.get('/offline/')
        assert response.status_code == 200
