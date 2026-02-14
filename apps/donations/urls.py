"""Donations URLs."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_frontend, views_api

api_router = DefaultRouter()
api_router.register(r'donations', views_api.DonationViewSet, basename='donation')
api_router.register(r'campaigns', views_api.DonationCampaignViewSet, basename='campaign')
api_router.register(r'receipts', views_api.TaxReceiptViewSet, basename='receipt')
api_router.register(r'pledges', views_api.PledgeViewSet, basename='pledge')
api_router.register(r'statements', views_api.GivingStatementViewSet, basename='statement')
api_router.register(r'goals', views_api.GivingGoalViewSet, basename='goal')
api_router.register(r'imports', views_api.DonationImportViewSet, basename='import')
api_router.register(r'matching', views_api.MatchingCampaignViewSet, basename='matching')
api_router.register(r'crypto', views_api.CryptoDonationViewSet, basename='crypto')
api_router.register(r'analytics', views_api.AnalyticsViewSet, basename='analytics')

api_urlpatterns = [path('', include(api_router.urls))]

frontend_urlpatterns = [
    # Donations CRUD
    path('donate/', views_frontend.donation_create, name='donation_create'),
    path('history/', views_frontend.donation_history, name='donation_history'),
    path('<uuid:pk>/', views_frontend.donation_detail, name='donation_detail'),
    path('<uuid:pk>/edit/', views_frontend.donation_edit, name='donation_edit'),
    path('<uuid:pk>/delete/', views_frontend.donation_delete, name='donation_delete'),
    path('admin/', views_frontend.donation_admin_list, name='donation_admin_list'),
    path('admin/export/', views_frontend.donation_export_csv, name='donation_export_csv'),
    path('admin/export/excel/', views_frontend.donation_export_excel, name='donation_export_excel'),
    path('admin/export/pdf/', views_frontend.donation_export_pdf, name='donation_export_pdf'),
    path('record/', views_frontend.donation_record, name='donation_record'),

    # Campaigns
    path('campaigns/', views_frontend.campaign_list, name='campaign_list'),
    path('campaigns/create/', views_frontend.campaign_create, name='campaign_create'),
    path('campaigns/<uuid:pk>/', views_frontend.campaign_detail, name='campaign_detail'),
    path('campaigns/<uuid:pk>/edit/', views_frontend.campaign_update, name='campaign_update'),
    path('campaigns/<uuid:pk>/delete/', views_frontend.campaign_delete, name='campaign_delete'),

    # Tax Receipts
    path('receipts/', views_frontend.receipt_list, name='receipt_list'),
    path('receipts/batch-email/', views_frontend.receipt_batch_email, name='receipt_batch_email'),
    path('receipts/<uuid:pk>/', views_frontend.receipt_detail, name='receipt_detail'),
    path('receipts/<uuid:pk>/pdf/', views_frontend.receipt_download_pdf, name='receipt_download_pdf'),

    # Reports
    path('reports/monthly/', views_frontend.donation_monthly_report, name='monthly_report'),

    # Finance delegations
    path('delegations/', views_frontend.finance_delegations, name='finance_delegations'),
    path('delegations/grant/', views_frontend.delegate_finance_access, name='delegate_finance_access'),
    path('delegations/<uuid:pk>/revoke/', views_frontend.revoke_finance_access, name='revoke_finance_access'),

    # Pledges
    path('pledges/', views_frontend.pledge_list, name='pledge_list'),
    path('pledges/create/', views_frontend.pledge_create, name='pledge_create'),
    path('pledges/<uuid:pk>/', views_frontend.pledge_detail, name='pledge_detail'),
    path('pledges/<uuid:pk>/edit/', views_frontend.pledge_update, name='pledge_update'),
    path('pledges/<uuid:pk>/delete/', views_frontend.pledge_delete, name='pledge_delete'),

    # Giving Statements
    path('statements/', views_frontend.statement_list, name='statement_list'),
    path('statements/generate/', views_frontend.statement_generate, name='statement_generate'),
    path('statements/<uuid:pk>/download/', views_frontend.statement_download, name='statement_download'),

    # Giving Goals
    path('goals/', views_frontend.goal_create, name='goal_create'),
    path('goals/report/', views_frontend.goal_report, name='goal_report'),

    # Import Wizard
    path('imports/', views_frontend.import_history, name='import_history'),
    path('imports/upload/', views_frontend.import_upload, name='import_upload'),
    path('imports/<uuid:pk>/preview/', views_frontend.import_preview, name='import_preview'),
    path('imports/<uuid:pk>/confirm/', views_frontend.import_confirm, name='import_confirm'),

    # Analytics
    path('analytics/', views_frontend.analytics_dashboard, name='analytics_dashboard'),

    # Kiosk
    path('kiosk/', views_frontend.kiosk_donation, name='kiosk_donation'),

    # Crypto
    path('crypto/', views_frontend.crypto_donate, name='crypto_donate'),
    path('crypto/<uuid:pk>/', views_frontend.crypto_detail, name='crypto_detail'),
]

app_name = 'donations'
urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
    path('', include((frontend_urlpatterns, 'frontend'))),
]
