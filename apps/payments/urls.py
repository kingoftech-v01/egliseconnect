"""URL configuration for payments app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views_api, views_frontend

# API
router = DefaultRouter()
router.register(r'payments', views_api.OnlinePaymentViewSet, basename='payment')
router.register(r'recurring', views_api.RecurringDonationViewSet, basename='recurring')

api_urlpatterns = router.urls + [
    path('webhook/', views_api.StripeWebhookView.as_view(), name='stripe_webhook'),
]

# Frontend
frontend_urlpatterns = [
    path('donate/', views_frontend.donate, name='donate'),
    path('success/', views_frontend.donation_success, name='donation_success'),
    path('history/', views_frontend.payment_history, name='payment_history'),
    path('recurring/', views_frontend.recurring_manage, name='recurring_manage'),
    path('recurring/<uuid:pk>/cancel/', views_frontend.cancel_recurring, name='cancel_recurring'),
]
