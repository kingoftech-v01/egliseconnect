"""
Donations URLs - Frontend and API routing.

This module configures URL patterns for:
- Frontend HTML views (views_frontend.py)
- REST API endpoints (views_api.py)

URL Namespaces:
- Frontend: frontend:donations:view_name
- API: api:v1:donations:resource-name
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
    r'donations',
    views_api.DonationViewSet,
    basename='donation'
)

api_router.register(
    r'campaigns',
    views_api.DonationCampaignViewSet,
    basename='campaign'
)

api_router.register(
    r'receipts',
    views_api.TaxReceiptViewSet,
    basename='receipt'
)


# =============================================================================
# API URLPATTERNS
# =============================================================================

api_urlpatterns = [
    path('', include(api_router.urls)),
]


# =============================================================================
# FRONTEND URLPATTERNS
# =============================================================================

frontend_urlpatterns = [
    # Donate
    path(
        'donate/',
        views_frontend.donation_create,
        name='donation_create'
    ),

    # My history
    path(
        'history/',
        views_frontend.donation_history,
        name='donation_history'
    ),

    # Donation detail
    path(
        '<uuid:pk>/',
        views_frontend.donation_detail,
        name='donation_detail'
    ),

    # Admin list (treasurer)
    path(
        'admin/',
        views_frontend.donation_admin_list,
        name='donation_admin_list'
    ),

    # Record physical donation
    path(
        'record/',
        views_frontend.donation_record,
        name='donation_record'
    ),

    # Campaigns
    path(
        'campaigns/',
        views_frontend.campaign_list,
        name='campaign_list'
    ),

    path(
        'campaigns/<uuid:pk>/',
        views_frontend.campaign_detail,
        name='campaign_detail'
    ),

    # Tax receipts
    path(
        'receipts/',
        views_frontend.receipt_list,
        name='receipt_list'
    ),

    path(
        'receipts/<uuid:pk>/',
        views_frontend.receipt_detail,
        name='receipt_detail'
    ),

    # Reports
    path(
        'reports/monthly/',
        views_frontend.donation_monthly_report,
        name='monthly_report'
    ),
]


# =============================================================================
# APP URL CONFIGURATION
# =============================================================================

app_name = 'donations'

urlpatterns = [
    # API URLs: /api/v1/donations/
    path('api/', include((api_urlpatterns, 'api'))),

    # Frontend URLs: /donations/
    path('', include((frontend_urlpatterns, 'frontend'))),
]
