"""URL patterns for JWT authentication API v2."""
from django.urls import path

from .views_auth_v2 import (
    LoginView,
    RegisterView,
    LogoutView,
    MeView,
    ChangePasswordView,
    CustomTokenRefreshView,
    ForgotPasswordView,
    ResetPasswordView,
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', MeView.as_view(), name='me'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),
]
