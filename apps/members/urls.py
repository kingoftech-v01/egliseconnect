"""
Members URLs - Frontend and API routing.

This module configures URL patterns for:
- Frontend HTML views (views_frontend.py)
- REST API endpoints (views_api.py)

URL Namespaces:
- Frontend: frontend:members:view_name
- API: api:v1:members:resource-name
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views_frontend
from . import views_api


# =============================================================================
# API ROUTER (DRF ViewSets)
# =============================================================================

api_router = DefaultRouter()

api_router.register(
    r'members',
    views_api.MemberViewSet,
    basename='member'
)

api_router.register(
    r'families',
    views_api.FamilyViewSet,
    basename='family'
)

api_router.register(
    r'groups',
    views_api.GroupViewSet,
    basename='group'
)

api_router.register(
    r'privacy',
    views_api.DirectoryPrivacyViewSet,
    basename='privacy'
)


# =============================================================================
# API URLPATTERNS (Non-ViewSet API views)
# =============================================================================

api_urlpatterns = [
    # Include router URLs
    path('', include(api_router.urls)),
]


# =============================================================================
# FRONTEND URLPATTERNS (HTML Template Views)
# =============================================================================

frontend_urlpatterns = [
    # Member list (admin/pastor only)
    path(
        '',
        views_frontend.member_list,
        name='member_list'
    ),

    # Member registration (public)
    path(
        'register/',
        views_frontend.member_create,
        name='member_create'
    ),

    # Member detail
    path(
        '<uuid:pk>/',
        views_frontend.member_detail,
        name='member_detail'
    ),

    # Member update
    path(
        '<uuid:pk>/edit/',
        views_frontend.member_update,
        name='member_update'
    ),

    # Birthdays
    path(
        'birthdays/',
        views_frontend.birthday_list,
        name='birthday_list'
    ),

    # Directory
    path(
        'directory/',
        views_frontend.directory,
        name='directory'
    ),

    # Privacy settings
    path(
        'privacy-settings/',
        views_frontend.privacy_settings,
        name='privacy_settings'
    ),

    # Groups
    path(
        'groups/',
        views_frontend.group_list,
        name='group_list'
    ),

    path(
        'groups/<uuid:pk>/',
        views_frontend.group_detail,
        name='group_detail'
    ),

    # Families
    path(
        'families/<uuid:pk>/',
        views_frontend.family_detail,
        name='family_detail'
    ),
]


# =============================================================================
# APP URL CONFIGURATION
# =============================================================================

app_name = 'members'

urlpatterns = [
    # API URLs: /api/v1/members/
    path('api/', include((api_urlpatterns, 'api'))),

    # Frontend URLs: /members/
    path('', include((frontend_urlpatterns, 'frontend'))),
]
