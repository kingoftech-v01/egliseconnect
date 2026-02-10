"""ÉgliseConnect URL configuration with namespaced routing."""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from rest_framework.routers import DefaultRouter

from apps.members.urls import api_urlpatterns as members_api
from apps.donations.urls import api_urlpatterns as donations_api
from apps.events.urls import api_urlpatterns as events_api
from apps.volunteers.urls import api_urlpatterns as volunteers_api
from apps.communication.urls import api_urlpatterns as communication_api
from apps.help_requests.urls import api_urlpatterns as help_requests_api
from apps.reports.urls import api_urlpatterns as reports_api
from apps.onboarding.urls import api_urlpatterns as onboarding_api
from apps.attendance.urls import api_urlpatterns as attendance_api
from apps.payments.urls import api_urlpatterns as payments_api
from apps.worship.urls import api_urlpatterns as worship_api

from apps.members.urls import frontend_urlpatterns as members_frontend
from apps.donations.urls import frontend_urlpatterns as donations_frontend
from apps.events.urls import frontend_urlpatterns as events_frontend
from apps.volunteers.urls import frontend_urlpatterns as volunteers_frontend
from apps.communication.urls import frontend_urlpatterns as communication_frontend
from apps.help_requests.urls import frontend_urlpatterns as help_requests_frontend
from apps.reports.urls import frontend_urlpatterns as reports_frontend
from apps.onboarding.urls import frontend_urlpatterns as onboarding_frontend
from apps.attendance.urls import frontend_urlpatterns as attendance_frontend
from apps.payments.urls import frontend_urlpatterns as payments_frontend
from apps.worship.urls import frontend_urlpatterns as worship_frontend

from apps.core.views_audit import LoginAuditViewSet
from apps.core import views_frontend_audit as core_frontend_audit
from apps.core.views_frontend_search import search_view as core_search_view
from apps.core.views_pwa import service_worker, offline, manifest

# Audit API router
audit_router = DefaultRouter()
audit_router.register(r'login-audits', LoginAuditViewSet, basename='login-audit')


api_v1_patterns = [
    path('members/', include((members_api, 'members'))),
    path('donations/', include((donations_api, 'donations'))),
    path('events/', include((events_api, 'events'))),
    path('volunteers/', include((volunteers_api, 'volunteers'))),
    path('communication/', include((communication_api, 'communication'))),
    path('help-requests/', include((help_requests_api, 'help_requests'))),
    path('reports/', include((reports_api, 'reports'))),
    path('onboarding/', include((onboarding_api, 'onboarding'))),
    path('attendance/', include((attendance_api, 'attendance'))),
    path('payments/', include((payments_api, 'payments'))),
    path('worship/', include((worship_api, 'worship'))),
    path('audit/', include((audit_router.urls, 'audit'))),
]


frontend_patterns = [
    path('members/', include((members_frontend, 'members'))),
    path('donations/', include((donations_frontend, 'donations'))),
    path('events/', include((events_frontend, 'events'))),
    path('volunteers/', include((volunteers_frontend, 'volunteers'))),
    path('communication/', include((communication_frontend, 'communication'))),
    path('help-requests/', include((help_requests_frontend, 'help_requests'))),
    path('reports/', include((reports_frontend, 'reports'))),
    path('onboarding/', include((onboarding_frontend, 'onboarding'))),
    path('attendance/', include((attendance_frontend, 'attendance'))),
    path('payments/', include((payments_frontend, 'payments'))),
    path('worship/', include((worship_frontend, 'worship'))),
    path('audit/logins/', include(([
        path('', core_frontend_audit.login_audit_list, name='login_audit_list'),
        path('2fa-status/', core_frontend_audit.two_factor_status, name='two_factor_status'),
    ], 'audit'))),
]


urlpatterns = [
    # PWA routes (must be at root scope for service worker)
    path('sw.js', service_worker, name='service_worker'),
    path('manifest.json', manifest, name='manifest'),
    path('offline/', offline, name='offline'),
    path('admin/', admin.site.urls),
    path('api/v1/', include((api_v1_patterns, 'api'), namespace='v1')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    re_path(r'^departments/(?P<rest>.*)$', RedirectView.as_view(url='/members/departments/%(rest)s', permanent=False)),
    path('search/', core_search_view, name='search'),
    path('', RedirectView.as_view(url='/onboarding/dashboard/', permanent=False), name='home'),
    path('', include((frontend_patterns, 'frontend'))),
    path('accounts/', include('allauth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
