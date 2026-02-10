"""Donations URLs."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_frontend, views_api

api_router = DefaultRouter()
api_router.register(r'donations', views_api.DonationViewSet, basename='donation')
api_router.register(r'campaigns', views_api.DonationCampaignViewSet, basename='campaign')
api_router.register(r'receipts', views_api.TaxReceiptViewSet, basename='receipt')

api_urlpatterns = [path('', include(api_router.urls))]

frontend_urlpatterns = [
    path('donate/', views_frontend.donation_create, name='donation_create'),
    path('history/', views_frontend.donation_history, name='donation_history'),
    path('<uuid:pk>/', views_frontend.donation_detail, name='donation_detail'),
    path('<uuid:pk>/edit/', views_frontend.donation_edit, name='donation_edit'),
    path('<uuid:pk>/delete/', views_frontend.donation_delete, name='donation_delete'),
    path('admin/', views_frontend.donation_admin_list, name='donation_admin_list'),
    path('admin/export/', views_frontend.donation_export_csv, name='donation_export_csv'),
    path('record/', views_frontend.donation_record, name='donation_record'),
    path('campaigns/', views_frontend.campaign_list, name='campaign_list'),
    path('campaigns/create/', views_frontend.campaign_create, name='campaign_create'),
    path('campaigns/<uuid:pk>/', views_frontend.campaign_detail, name='campaign_detail'),
    path('campaigns/<uuid:pk>/edit/', views_frontend.campaign_update, name='campaign_update'),
    path('campaigns/<uuid:pk>/delete/', views_frontend.campaign_delete, name='campaign_delete'),
    path('receipts/', views_frontend.receipt_list, name='receipt_list'),
    path('receipts/batch-email/', views_frontend.receipt_batch_email, name='receipt_batch_email'),
    path('receipts/<uuid:pk>/', views_frontend.receipt_detail, name='receipt_detail'),
    path('receipts/<uuid:pk>/pdf/', views_frontend.receipt_download_pdf, name='receipt_download_pdf'),
    path('reports/monthly/', views_frontend.donation_monthly_report, name='monthly_report'),
    # Finance delegations
    path('delegations/', views_frontend.finance_delegations, name='finance_delegations'),
    path('delegations/grant/', views_frontend.delegate_finance_access, name='delegate_finance_access'),
    path('delegations/<uuid:pk>/revoke/', views_frontend.revoke_finance_access, name='revoke_finance_access'),
]

app_name = 'donations'
urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
    path('', include((frontend_urlpatterns, 'frontend'))),
]
