"""Frontend views for core app: branding, webhooks, audit log viewer, API keys."""
import csv
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext_lazy as _

from apps.core.constants import Roles
from apps.core.forms import ChurchBrandingForm, WebhookEndpointForm
from apps.core.models_extended import (
    ChurchBranding, WebhookEndpoint, WebhookDelivery, AuditLog, Campus,
)


def _is_admin(request):
    """Check if user has admin/pastor access."""
    if not request.user.is_authenticated:
        return False
    if request.user.is_superuser:
        return True
    member = getattr(request.user, 'member_profile', None)
    if member and member.role in [Roles.ADMIN, Roles.PASTOR]:
        return True
    return False


# ─── Branding ──────────────────────────────────────────────────────────────────

@login_required
def branding_settings(request):
    """View and edit church branding settings."""
    if not _is_admin(request):
        return redirect('/')

    branding = ChurchBranding.get_current()

    if request.method == 'POST':
        form = ChurchBrandingForm(request.POST, request.FILES, instance=branding)
        if form.is_valid():
            form.save()
            messages.success(request, _('Image de marque mise à jour avec succès.'))
            return redirect('/settings/branding/')
    else:
        form = ChurchBrandingForm(instance=branding)

    context = {
        'form': form,
        'branding': branding,
        'page_title': _('Image de marque'),
    }
    return render(request, 'core/branding_settings.html', context)


# ─── Webhooks ──────────────────────────────────────────────────────────────────

@login_required
def webhook_list(request):
    """List all webhook endpoints."""
    if not _is_admin(request):
        return redirect('/')

    endpoints = WebhookEndpoint.objects.all()
    context = {
        'endpoints': endpoints,
        'page_title': _('Webhooks'),
    }
    return render(request, 'core/webhook_list.html', context)


@login_required
def webhook_create(request):
    """Create a new webhook endpoint."""
    if not _is_admin(request):
        return redirect('/')

    if request.method == 'POST':
        form = WebhookEndpointForm(request.POST)
        if form.is_valid():
            webhook = form.save(commit=False)
            webhook.created_by = request.user
            webhook.save()
            messages.success(request, _('Webhook créé avec succès.'))
            return redirect('/settings/webhooks/')
    else:
        form = WebhookEndpointForm()

    context = {
        'form': form,
        'page_title': _('Nouveau webhook'),
    }
    return render(request, 'core/webhook_form.html', context)


@login_required
def webhook_edit(request, pk):
    """Edit an existing webhook endpoint."""
    if not _is_admin(request):
        return redirect('/')

    webhook = get_object_or_404(WebhookEndpoint, pk=pk)

    if request.method == 'POST':
        form = WebhookEndpointForm(request.POST, instance=webhook)
        if form.is_valid():
            form.save()
            messages.success(request, _('Webhook mis à jour avec succès.'))
            return redirect('/settings/webhooks/')
    else:
        form = WebhookEndpointForm(instance=webhook)

    context = {
        'form': form,
        'webhook': webhook,
        'page_title': _('Modifier le webhook'),
    }
    return render(request, 'core/webhook_form.html', context)


@login_required
def webhook_delete(request, pk):
    """Delete a webhook endpoint."""
    if not _is_admin(request):
        return redirect('/')

    webhook = get_object_or_404(WebhookEndpoint, pk=pk)

    if request.method == 'POST':
        webhook.deactivate()
        messages.success(request, _('Webhook supprimé avec succès.'))
        return redirect('/settings/webhooks/')

    context = {
        'webhook': webhook,
        'page_title': _('Supprimer le webhook'),
    }
    return render(request, 'core/webhook_confirm_delete.html', context)


@login_required
def webhook_deliveries(request, pk):
    """View delivery history for a webhook endpoint."""
    if not _is_admin(request):
        return redirect('/')

    webhook = get_object_or_404(WebhookEndpoint, pk=pk)
    deliveries = webhook.deliveries.all()[:100]

    context = {
        'webhook': webhook,
        'deliveries': deliveries,
        'page_title': _('Livraisons webhook'),
    }
    return render(request, 'core/webhook_deliveries.html', context)


# ─── Audit Log Viewer ──────────────────────────────────────────────────────────

@login_required
def audit_log_list(request):
    """View audit logs for admins."""
    if not _is_admin(request):
        return redirect('/')

    logs = AuditLog.objects.select_related('user').order_by('-created_at')

    # Filters
    action = request.GET.get('action', '')
    model_name = request.GET.get('model', '')
    user_id = request.GET.get('user_id', '')

    if action:
        logs = logs.filter(action=action)
    if model_name:
        logs = logs.filter(model_name__icontains=model_name)
    if user_id:
        logs = logs.filter(user_id=user_id)

    logs = logs[:200]

    context = {
        'logs': logs,
        'action_choices': AuditLog.ACTION_CHOICES,
        'selected_action': action,
        'selected_model': model_name,
        'page_title': _('Journal d\'audit'),
    }
    return render(request, 'core/audit_log_list.html', context)


@login_required
def audit_log_export(request):
    """Export audit logs as CSV."""
    if not _is_admin(request):
        return redirect('/')

    format_type = request.GET.get('format', 'csv')
    logs = AuditLog.objects.select_related('user').order_by('-created_at')[:5000]

    if format_type == 'json':
        data = []
        for log in logs:
            data.append({
                'id': str(log.pk),
                'user': log.user.username if log.user else '',
                'action': log.action,
                'model_name': log.model_name,
                'object_id': log.object_id,
                'object_repr': log.object_repr,
                'changes': log.changes,
                'ip_address': log.ip_address or '',
                'created_at': log.created_at.isoformat(),
            })
        response = HttpResponse(
            json.dumps(data, indent=2, ensure_ascii=False),
            content_type='application/json',
        )
        response['Content-Disposition'] = 'attachment; filename="audit_logs.json"'
        return response

    # CSV export
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="audit_logs.csv"'
    response.write('\ufeff')  # BOM for Excel

    writer = csv.writer(response)
    writer.writerow([
        'Date', 'Utilisateur', 'Action', 'Modèle',
        'ID Objet', 'Description', 'Adresse IP',
    ])

    for log in logs:
        writer.writerow([
            log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            log.user.username if log.user else '',
            log.get_action_display(),
            log.model_name,
            log.object_id,
            log.object_repr,
            log.ip_address or '',
        ])

    return response


# ─── API Key Management ────────────────────────────────────────────────────────

@login_required
def api_key_management(request):
    """OAuth2 API key management page for admins."""
    if not _is_admin(request):
        return redirect('/')

    from oauth2_provider.models import Application

    applications = Application.objects.filter(user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create':
            app = Application.objects.create(
                user=request.user,
                name=request.POST.get('name', 'API Application'),
                client_type=Application.CLIENT_CONFIDENTIAL,
                authorization_grant_type=Application.GRANT_CLIENT_CREDENTIALS,
            )
            messages.success(
                request,
                _(f'Application créée. Client ID: {app.client_id}')
            )
            return redirect('/settings/api-keys/')

        elif action == 'revoke':
            app_id = request.POST.get('app_id')
            try:
                app = Application.objects.get(pk=app_id, user=request.user)
                app.delete()
                messages.success(request, _('Application révoquée.'))
            except Application.DoesNotExist:
                messages.error(request, _('Application introuvable.'))
            return redirect('/settings/api-keys/')

    context = {
        'applications': applications,
        'page_title': _('Gestion des clés API'),
    }
    return render(request, 'core/api_key_management.html', context)


# ─── Campus Management ────────────────────────────────────────────────────────

@login_required
def campus_list(request):
    """List all campuses."""
    if not _is_admin(request):
        return redirect('/')

    campuses = Campus.objects.all()
    context = {
        'campuses': campuses,
        'page_title': _('Campus'),
    }
    return render(request, 'core/campus_list.html', context)


# ─── Language Switcher ─────────────────────────────────────────────────────────

@login_required
def set_language(request):
    """Switch the user's language preference."""
    if request.method == 'POST':
        from django.utils.translation import activate
        from django.conf import settings

        lang = request.POST.get('language', 'fr')
        if lang in [l[0] for l in settings.LANGUAGES]:
            request.session['django_language'] = lang
            activate(lang)

            # Update member language preference if available
            if hasattr(request.user, 'member_profile'):
                member = request.user.member_profile
                if hasattr(member, 'language_preference'):
                    member.language_preference = lang
                    member.save(update_fields=['language_preference', 'updated_at'])

    next_url = request.POST.get('next', request.META.get('HTTP_REFERER', '/'))
    return redirect(next_url)
