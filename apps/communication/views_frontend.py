"""Communication Frontend Views."""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.constants import Roles, NewsletterStatus, NotificationType
from apps.members.models import Member

from .models import Newsletter, Notification, NotificationPreference
from .forms import NewsletterForm




def _is_staff(request):
    """Check if user has staff-level role (pastor or admin)."""
    if hasattr(request.user, "member_profile"):
        return request.user.member_profile.role in [Roles.PASTOR, Roles.ADMIN]
    return request.user.is_staff

@login_required
def newsletter_list(request):
    # Staff sees all newsletters, members see only sent ones
    if hasattr(request.user, 'member_profile') and request.user.member_profile.role in [Roles.PASTOR, Roles.ADMIN]:
        newsletters = Newsletter.objects.all()
    else:
        newsletters = Newsletter.objects.filter(status='sent')

    paginator = Paginator(newsletters, 20)
    page = request.GET.get('page', 1)
    newsletters_page = paginator.get_page(page)

    context = {'newsletters': newsletters_page, 'page_title': _('Infolettres')}
    return render(request, 'communication/newsletter_list.html', context)


@login_required
def newsletter_detail(request, pk):
    newsletter = get_object_or_404(Newsletter, pk=pk)
    is_staff = _is_staff(request)
    context = {
        'newsletter': newsletter,
        'page_title': newsletter.subject,
        'is_staff': is_staff,
    }
    return render(request, 'communication/newsletter_detail.html', context)


@login_required
def newsletter_create(request):
    """Staff only."""
    if hasattr(request.user, 'member_profile'):
        if request.user.member_profile.role not in [Roles.PASTOR, Roles.ADMIN]:
            messages.error(request, _("Accès refusé."))
            return redirect('/')
    elif not request.user.is_staff:
        messages.error(request, _("Accès refusé."))
        return redirect('/')

    if request.method == 'POST':
        form = NewsletterForm(request.POST)
        if form.is_valid():
            newsletter = form.save(commit=False)
            if hasattr(request.user, 'member_profile'):
                newsletter.created_by = request.user.member_profile
            newsletter.save()
            messages.success(request, _('Infolettre créée.'))
            return redirect('frontend:communication:newsletter_detail', pk=newsletter.pk)
    else:
        form = NewsletterForm()

    # Calculate recipient count
    recipient_count = _get_recipient_count(form)

    context = {
        'form': form,
        'page_title': _('Nouvelle infolettre'),
        'recipient_count': recipient_count,
    }
    return render(request, 'communication/newsletter_form.html', context)


@login_required
def notification_list(request):
    if not hasattr(request.user, 'member_profile'):
        messages.error(request, _("Profil requis."))
        return redirect('/')

    notifications = Notification.objects.filter(member=request.user.member_profile)

    # Filter by notification_type
    notification_type = request.GET.get('type')
    if notification_type:
        notifications = notifications.filter(notification_type=notification_type)

    paginator = Paginator(notifications, 20)
    page = request.GET.get('page', 1)
    notifications_page = paginator.get_page(page)

    context = {
        'notifications': notifications_page,
        'page_title': _('Notifications'),
        'notification_types': NotificationType.CHOICES,
        'current_type': notification_type,
    }
    return render(request, 'communication/notification_list.html', context)


@login_required
def preferences(request):
    if not hasattr(request.user, 'member_profile'):
        messages.error(request, _("Profil requis."))
        return redirect('/')

    prefs, created = NotificationPreference.objects.get_or_create(member=request.user.member_profile)

    if request.method == 'POST':
        prefs.email_newsletter = request.POST.get('email_newsletter') == 'on'
        prefs.email_events = request.POST.get('email_events') == 'on'
        prefs.email_birthdays = request.POST.get('email_birthdays') == 'on'
        prefs.push_enabled = request.POST.get('push_enabled') == 'on'
        prefs.sms_enabled = request.POST.get('sms_enabled') == 'on'
        prefs.save()
        messages.success(request, _('Préférences mises à jour.'))

    context = {'prefs': prefs, 'page_title': _('Préférences de notification')}
    return render(request, 'communication/preferences.html', context)

@login_required
def newsletter_edit(request, pk):
    """Edit an existing newsletter (staff only). Only drafts can be edited."""
    if not _is_staff(request):
        messages.error(request, _("Accès refusé."))
        return redirect("/")

    newsletter = get_object_or_404(Newsletter, pk=pk)

    if newsletter.status != NewsletterStatus.DRAFT:
        messages.error(request, _("Seules les infolettres en brouillon peuvent être modifiées."))
        return redirect("frontend:communication:newsletter_detail", pk=newsletter.pk)

    if request.method == "POST":
        form = NewsletterForm(request.POST, instance=newsletter)
        if form.is_valid():
            form.save()
            messages.success(request, _("Infolettre mise à jour."))
            return redirect("frontend:communication:newsletter_detail", pk=newsletter.pk)
    else:
        form = NewsletterForm(instance=newsletter)

    recipient_count = _get_recipient_count(form)

    context = {
        "form": form,
        "newsletter": newsletter,
        "page_title": _("Modifier l'infolettre"),
        "recipient_count": recipient_count,
    }
    return render(request, "communication/newsletter_form.html", context)


@login_required
def newsletter_delete(request, pk):
    """Delete a newsletter (staff only, POST confirmation)."""
    if not _is_staff(request):
        messages.error(request, _("Accès refusé."))
        return redirect("/")

    newsletter = get_object_or_404(Newsletter, pk=pk)

    if request.method == "POST":
        newsletter.delete()
        messages.success(request, _("Infolettre supprimée."))
        return redirect("/communication/newsletters/")

    context = {
        "newsletter": newsletter,
        "page_title": _("Supprimer l'infolettre"),
    }
    return render(request, "communication/newsletter_delete.html", context)


@login_required
def newsletter_send(request, pk):
    """Send or schedule a newsletter (staff only, POST)."""
    if not _is_staff(request):
        messages.error(request, _("Accès refusé."))
        return redirect("/")

    newsletter = get_object_or_404(Newsletter, pk=pk)

    if request.method != "POST":
        return redirect("frontend:communication:newsletter_detail", pk=newsletter.pk)

    if newsletter.status not in [NewsletterStatus.DRAFT, NewsletterStatus.SCHEDULED]:
        messages.error(request, _("Cette infolettre ne peut pas être envoyée."))
        return redirect("frontend:communication:newsletter_detail", pk=newsletter.pk)

    action = request.POST.get("action", "send")

    if action == "schedule":
        scheduled_for = request.POST.get("scheduled_for")
        if scheduled_for:
            newsletter.scheduled_for = scheduled_for
            newsletter.status = NewsletterStatus.SCHEDULED
            newsletter.save(update_fields=["scheduled_for", "status", "updated_at"])
            messages.success(request, _("Infolettre planifiée."))
        else:
            messages.error(request, _("Veuillez spécifier une date de planification."))
    else:
        # Send immediately
        newsletter.status = NewsletterStatus.SENT
        newsletter.sent_at = timezone.now()
        # Count recipients
        if newsletter.send_to_all:
            newsletter.recipients_count = Member.objects.filter(
                is_active=True, email__isnull=False
            ).exclude(email="").count()
        else:
            newsletter.recipients_count = Member.objects.filter(
                is_active=True,
                group_memberships__group__in=newsletter.target_groups.all(),
                email__isnull=False,
            ).exclude(email="").distinct().count()
        newsletter.save(update_fields=["status", "sent_at", "recipients_count", "updated_at"])
        messages.success(request, _("Infolettre envoyée."))

    return redirect("frontend:communication:newsletter_detail", pk=newsletter.pk)


@login_required
def mark_all_read(request):
    """Mark all notifications as read (POST only)."""
    if request.method != "POST":
        return redirect("/communication/notifications/")

    if not hasattr(request.user, "member_profile"):
        messages.error(request, _("Profil requis."))
        return redirect("/")

    Notification.objects.filter(
        member=request.user.member_profile,
        is_read=False,
    ).update(is_read=True, read_at=timezone.now())

    messages.success(request, _("Toutes les notifications ont été marquées comme lues."))
    return redirect("/communication/notifications/")


def _get_recipient_count(form):
    """Calculate approximate recipient count based on form data."""
    try:
        if form.is_bound and form.is_valid():
            if form.cleaned_data.get("send_to_all", True):
                return Member.objects.filter(
                    is_active=True, email__isnull=False
                ).exclude(email="").count()
            else:
                groups = form.cleaned_data.get("target_groups")
                if groups:
                    return Member.objects.filter(
                        is_active=True,
                        group_memberships__group__in=groups,
                        email__isnull=False,
                    ).exclude(email="").distinct().count()
        else:
            # Default: count all active members with email
            return Member.objects.filter(
                is_active=True, email__isnull=False
            ).exclude(email="").count()
    except Exception:
        return 0
    return 0
