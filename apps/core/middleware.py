"""Custom middleware for security and access control."""
from django.shortcuts import redirect

from apps.core.constants import Roles


# Paths that don't require 2FA
TWO_FACTOR_EXEMPT_PATHS = [
    '/accounts/',
    '/api/',
    '/static/',
    '/media/',
    '/admin/',
]

# The allauth MFA TOTP setup URL
MFA_SETUP_URL = '/accounts/2fa/'


class TwoFactorEnforcementMiddleware:
    """Force 2FA activation within deadline period.

    After the deadline, users without 2FA enabled are redirected
    to the 2FA setup page on every request (except exempted paths).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            member = getattr(request.user, 'member_profile', None)
            if member and member.is_2fa_overdue:
                path = request.path
                if not any(path.startswith(p) for p in TWO_FACTOR_EXEMPT_PATHS):
                    if path != MFA_SETUP_URL and not path.startswith(MFA_SETUP_URL):
                        return redirect(MFA_SETUP_URL)

        return self.get_response(request)


class MembershipAccessMiddleware:
    """Restricts access to full dashboard pages based on membership_status.

    Non-active members are redirected to the onboarding dashboard when
    they try to access members-only pages.
    """

    # Paths always accessible regardless of membership status
    ALWAYS_ALLOWED = [
        '/accounts/',
        '/onboarding/',
        '/attendance/my-qr/',
        '/attendance/my-history/',
        '/api/',
        '/static/',
        '/media/',
        '/admin/',
        '/sw.js',
        '/manifest.json',
        '/offline/',
        '/payments/',
        '/audit/',
    ]

    # Paths that require ACTIVE membership status
    MEMBERS_ONLY = [
        '/donations/',
        '/events/',
        '/volunteers/',
        '/communication/',
        '/help-requests/',
        '/members/',
        '/reports/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            return self.get_response(request)

        member = getattr(request.user, 'member_profile', None)
        if not member:
            return self.get_response(request)

        path = request.path

        # Always allow exempt paths
        if any(path.startswith(p) for p in self.ALWAYS_ALLOWED):
            return self.get_response(request)

        # Staff bypass (admin/pastor can always access)
        if member.role in Roles.STAFF_ROLES:
            return self.get_response(request)

        # Block non-active members from members-only pages
        if not member.has_full_access:
            if any(path.startswith(p) for p in self.MEMBERS_ONLY):
                return redirect('frontend:onboarding:dashboard')

        return self.get_response(request)
