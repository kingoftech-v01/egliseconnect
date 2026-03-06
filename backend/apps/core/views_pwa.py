"""PWA views for service worker and offline support."""
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache


@never_cache
def service_worker(request):
    """Serve the service worker from root URL scope."""
    return render(
        request,
        'pwa/service-worker.js',
        content_type='application/javascript',
    )


def offline(request):
    """Offline fallback page."""
    return render(request, 'pwa/offline.html')


def manifest(request):
    """Serve the PWA manifest."""
    manifest_data = {
        'name': 'EgliseConnect',
        'short_name': 'EgliseConnect',
        'description': "Systeme de gestion d'eglise",
        'start_url': '/',
        'display': 'standalone',
        'background_color': '#ffffff',
        'theme_color': '#1a73e8',
        'orientation': 'any',
        'lang': 'fr-CA',
        'dir': 'ltr',
        'icons': [
            {
                'src': '/static/w3crm/images/favicon.png',
                'sizes': '192x192',
                'type': 'image/png',
                'purpose': 'any maskable',
            }
        ],
    }
    return JsonResponse(manifest_data)
