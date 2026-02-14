"""URL configuration for payments app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views_api, views_frontend

# API
router = DefaultRouter()
router.register(r'payments', views_api.OnlinePaymentViewSet, basename='payment')
router.register(r'recurring', views_api.RecurringDonationViewSet, basename='recurring')
router.register(r'statements', views_api.GivingStatementViewSet, basename='statement')
router.register(r'goals', views_api.GivingGoalViewSet, basename='goal')
router.register(r'sms-donations', views_api.SMSDonationViewSet, basename='sms-donation')
router.register(r'plans', views_api.PaymentPlanViewSet, basename='plan')
router.register(r'employer-matches', views_api.EmployerMatchViewSet, basename='employer-match')
router.register(r'campaigns', views_api.GivingCampaignViewSet, basename='campaign')
router.register(r'kiosk-sessions', views_api.KioskSessionViewSet, basename='kiosk-session')

api_urlpatterns = router.urls + [
    path('webhook/', views_api.StripeWebhookView.as_view(), name='stripe_webhook'),
    path('sms-webhook/', views_api.TwilioSMSWebhookView.as_view(), name='twilio_sms_webhook'),
    path('crypto-charge/', views_api.CryptoChargeView.as_view(), name='crypto_charge'),
]

# Frontend
frontend_urlpatterns = [
    path('donate/', views_frontend.donate, name='donate'),
    path('success/', views_frontend.donation_success, name='donation_success'),
    path('history/', views_frontend.payment_history, name='payment_history'),
    path('recurring/', views_frontend.recurring_manage, name='recurring_manage'),
    path('recurring/<uuid:pk>/cancel/', views_frontend.cancel_recurring, name='cancel_recurring'),
    path('recurring/<uuid:pk>/edit/', views_frontend.edit_recurring, name='edit_recurring'),
    # Statements
    path('statements/', views_frontend.statement_list, name='statement_list'),
    path('statements/generate/', views_frontend.bulk_generate_statements, name='bulk_generate_statements'),
    path('statements/<uuid:pk>/download/', views_frontend.statement_download, name='statement_download'),
    # Goals
    path('goals/', views_frontend.giving_goal_manage, name='giving_goal_manage'),
    path('goals/summary/', views_frontend.giving_goal_summary, name='giving_goal_summary'),
    # Kiosk
    path('kiosk/', views_frontend.kiosk_donate, name='kiosk_donate'),
    path('kiosk/reconciliation/', views_frontend.kiosk_reconciliation, name='kiosk_reconciliation'),
    # Payment Plans
    path('plans/', views_frontend.payment_plan_list, name='payment_plan_list'),
    path('plans/create/', views_frontend.payment_plan_create, name='payment_plan_create'),
    path('plans/<uuid:pk>/complete/', views_frontend.payment_plan_complete, name='payment_plan_complete'),
    # Employer Matching
    path('employer-match/', views_frontend.employer_match_create, name='employer_match_create'),
    # Campaigns
    path('campaigns/', views_frontend.giving_campaign_list, name='giving_campaign_list'),
    path('campaigns/create/', views_frontend.giving_campaign_create, name='giving_campaign_create'),
    path('campaigns/<uuid:pk>/', views_frontend.giving_campaign_detail, name='giving_campaign_detail'),
    # Crypto
    path('crypto/', views_frontend.crypto_donate, name='crypto_donate'),
    # Admin
    path('webhook-errors/', views_frontend.webhook_errors, name='webhook_errors'),
    # Payment confirmation
    path('confirmation/<uuid:pk>/', views_frontend.payment_confirmation, name='payment_confirmation'),
]
