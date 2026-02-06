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
    path('admin/', views_frontend.donation_admin_list, name='donation_admin_list'),
    path('record/', views_frontend.donation_record, name='donation_record'),
    path('campaigns/', views_frontend.campaign_list, name='campaign_list'),
    path('campaigns/<uuid:pk>/', views_frontend.campaign_detail, name='campaign_detail'),
    path('receipts/', views_frontend.receipt_list, name='receipt_list'),
    path('receipts/<uuid:pk>/', views_frontend.receipt_detail, name='receipt_detail'),
    path('reports/monthly/', views_frontend.donation_monthly_report, name='monthly_report'),
]

app_name = 'donations'
urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
    path('', include((frontend_urlpatterns, 'frontend'))),
]
