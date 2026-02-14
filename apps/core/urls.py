"""URL patterns for core app: search, settings, branding, webhooks, audit."""
from django.urls import path

from . import views_frontend, views_frontend_search

app_name = 'core'

# Frontend URL patterns for settings pages
frontend_urlpatterns = [
    # Search
    path('autocomplete/', views_frontend_search.search_autocomplete, name='search_autocomplete'),

    # Branding
    path('branding/', views_frontend.branding_settings, name='branding_settings'),

    # Webhooks
    path('webhooks/', views_frontend.webhook_list, name='webhook_list'),
    path('webhooks/create/', views_frontend.webhook_create, name='webhook_create'),
    path('webhooks/<uuid:pk>/edit/', views_frontend.webhook_edit, name='webhook_edit'),
    path('webhooks/<uuid:pk>/delete/', views_frontend.webhook_delete, name='webhook_delete'),
    path('webhooks/<uuid:pk>/deliveries/', views_frontend.webhook_deliveries, name='webhook_deliveries'),

    # Audit logs
    path('audit/', views_frontend.audit_log_list, name='audit_log_list'),
    path('audit/export/', views_frontend.audit_log_export, name='audit_log_export'),

    # API keys
    path('api-keys/', views_frontend.api_key_management, name='api_key_management'),

    # Campus
    path('campus/', views_frontend.campus_list, name='campus_list'),

    # Language
    path('set-language/', views_frontend.set_language, name='set_language'),
]

# API URL patterns
from rest_framework.routers import DefaultRouter
from . import views_api

api_router = DefaultRouter()
api_router.register(r'audit-logs', views_api.AuditLogViewSet, basename='audit-log')
api_router.register(r'webhooks', views_api.WebhookEndpointViewSet, basename='webhook')
api_router.register(r'branding', views_api.ChurchBrandingViewSet, basename='branding')
api_router.register(r'campuses', views_api.CampusViewSet, basename='campus')

api_urlpatterns = api_router.urls + [
    path('search/', views_api.api_search, name='api_search'),
]
