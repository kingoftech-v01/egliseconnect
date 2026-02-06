"""ÉgliseConnect URL configuration with namespaced routing."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

from apps.members.urls import api_urlpatterns as members_api
from apps.donations.urls import api_urlpatterns as donations_api
from apps.events.urls import api_urlpatterns as events_api
from apps.volunteers.urls import api_urlpatterns as volunteers_api
from apps.communication.urls import api_urlpatterns as communication_api
from apps.help_requests.urls import api_urlpatterns as help_requests_api
from apps.reports.urls import api_urlpatterns as reports_api

from apps.members.urls import frontend_urlpatterns as members_frontend
from apps.donations.urls import frontend_urlpatterns as donations_frontend
from apps.events.urls import frontend_urlpatterns as events_frontend
from apps.volunteers.urls import frontend_urlpatterns as volunteers_frontend
from apps.communication.urls import frontend_urlpatterns as communication_frontend
from apps.help_requests.urls import frontend_urlpatterns as help_requests_frontend
from apps.reports.urls import frontend_urlpatterns as reports_frontend


api_v1_patterns = [
    path('members/', include((members_api, 'members'))),
    path('donations/', include((donations_api, 'donations'))),
    path('events/', include((events_api, 'events'))),
    path('volunteers/', include((volunteers_api, 'volunteers'))),
    path('communication/', include((communication_api, 'communication'))),
    path('help-requests/', include((help_requests_api, 'help_requests'))),
    path('reports/', include((reports_api, 'reports'))),
]


frontend_patterns = [
    path('members/', include((members_frontend, 'members'))),
    path('donations/', include((donations_frontend, 'donations'))),
    path('events/', include((events_frontend, 'events'))),
    path('volunteers/', include((volunteers_frontend, 'volunteers'))),
    path('communication/', include((communication_frontend, 'communication'))),
    path('help-requests/', include((help_requests_frontend, 'help_requests'))),
    path('reports/', include((reports_frontend, 'reports'))),
]


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include((api_v1_patterns, 'api'), namespace='v1')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('', RedirectView.as_view(url='/reports/', permanent=False), name='home'),
    path('', include((frontend_patterns, 'frontend'))),
    path('accounts/', include('django.contrib.auth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
