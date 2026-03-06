"""Frontend views for audit logs."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from apps.core.constants import Roles
from .audit import LoginAudit


@login_required
def login_audit_list(request):
    """View login audit logs - admin only."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        return redirect('/')

    audits = LoginAudit.objects.select_related('user').order_by('-created_at')[:200]

    context = {
        'audits': audits,
        'page_title': 'Journal de connexions',
    }
    return render(request, 'core/login_audit_list.html', context)


@login_required
def two_factor_status(request):
    """View 2FA status for admins - shows which members have/haven't set up 2FA."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        return redirect('/')

    from apps.members.models import Member
    members_without_2fa = Member.objects.filter(
        two_factor_enabled=False,
        is_active=True,
        user__isnull=False,
    ).select_related('user').order_by('last_name')

    members_with_2fa = Member.objects.filter(
        two_factor_enabled=True,
        is_active=True,
    ).select_related('user').order_by('last_name')

    context = {
        'members_without_2fa': members_without_2fa,
        'members_with_2fa': members_with_2fa,
        'page_title': 'Statut 2FA',
    }
    return render(request, 'core/two_factor_status.html', context)
