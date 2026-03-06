"""Signals for login auditing."""
import logging

from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Extract client IP from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


@receiver(user_logged_in)
def log_successful_login(sender, request, user, **kwargs):
    """Record successful login."""
    from .audit import LoginAudit
    LoginAudit.objects.create(
        user=user,
        email_attempted=getattr(user, 'email', ''),
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        success=True,
    )

    # Update 2FA status from allauth MFA
    if hasattr(user, 'member_profile'):
        member = user.member_profile
        try:
            from allauth.mfa.models import Authenticator
            has_totp = Authenticator.objects.filter(
                user=user, type='totp'
            ).exists()
            if has_totp and not member.two_factor_enabled:
                member.two_factor_enabled = True
                member.save(update_fields=['two_factor_enabled', 'updated_at'])
        except Exception:
            pass


@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    """Record failed login attempt."""
    from .audit import LoginAudit
    if request:
        LoginAudit.objects.create(
            email_attempted=credentials.get('email', credentials.get('username', '')),
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            success=False,
            failure_reason='invalid_credentials',
        )
