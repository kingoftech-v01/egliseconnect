"""Communication Frontend Views."""
from django.db.models import Count, Q, Sum, Avg
from django.db.models.functions import TruncDate
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.constants import (
    Roles, NewsletterStatus, NotificationType, AutomationTrigger,
    AutomationStatus, ABTestStatus,
)
from apps.members.models import Member

from .models import (
    Newsletter, Notification, NotificationPreference,
    SMSMessage, SMSTemplate, SMSOptOut, EmailTemplate,
    Automation, AutomationStep, AutomationEnrollment, ABTest,
    DirectMessage, GroupChat, GroupChatMessage, PushSubscription,
    NewsletterRecipient,
)
from .forms import (
    NewsletterForm, SMSComposeForm, SMSTemplateForm, EmailTemplateForm,
    AutomationForm, AutomationStepForm, DirectMessageForm, GroupChatForm,
    GroupChatMessageForm,
)


# ─── Helpers ─────────────────────────────────────────────────────────────────────


def _is_staff(request):
    """Check if user has staff-level role (pastor or admin)."""
    if hasattr(request.user, "member_profile"):
        return request.user.member_profile.role in [Roles.PASTOR, Roles.ADMIN]
    return request.user.is_staff


def _get_member(request):
    """Get the current user's member profile or None."""
    if hasattr(request.user, 'member_profile'):
        return request.user.member_profile
    return None


# ─── Newsletter views ────────────────────────────────────────────────────────────


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
            messages.error(request, _("Acces refuse."))
            return redirect('/')
    elif not request.user.is_staff:
        messages.error(request, _("Acces refuse."))
        return redirect('/')

    if request.method == 'POST':
        form = NewsletterForm(request.POST)
        if form.is_valid():
            newsletter = form.save(commit=False)
            if hasattr(request.user, 'member_profile'):
                newsletter.created_by = request.user.member_profile
            newsletter.save()
            messages.success(request, _('Infolettre creee.'))
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
        messages.success(request, _('Preferences mises a jour.'))

    context = {'prefs': prefs, 'page_title': _('Preferences de notification')}
    return render(request, 'communication/preferences.html', context)

@login_required
def newsletter_edit(request, pk):
    """Edit an existing newsletter (staff only). Only drafts can be edited."""
    if not _is_staff(request):
        messages.error(request, _("Acces refuse."))
        return redirect("/")

    newsletter = get_object_or_404(Newsletter, pk=pk)

    if newsletter.status != NewsletterStatus.DRAFT:
        messages.error(request, _("Seules les infolettres en brouillon peuvent etre modifiees."))
        return redirect("frontend:communication:newsletter_detail", pk=newsletter.pk)

    if request.method == "POST":
        form = NewsletterForm(request.POST, instance=newsletter)
        if form.is_valid():
            form.save()
            messages.success(request, _("Infolettre mise a jour."))
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
        messages.error(request, _("Acces refuse."))
        return redirect("/")

    newsletter = get_object_or_404(Newsletter, pk=pk)

    if request.method == "POST":
        newsletter.delete()
        messages.success(request, _("Infolettre supprimee."))
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
        messages.error(request, _("Acces refuse."))
        return redirect("/")

    newsletter = get_object_or_404(Newsletter, pk=pk)

    if request.method != "POST":
        return redirect("frontend:communication:newsletter_detail", pk=newsletter.pk)

    if newsletter.status not in [NewsletterStatus.DRAFT, NewsletterStatus.SCHEDULED]:
        messages.error(request, _("Cette infolettre ne peut pas etre envoyee."))
        return redirect("frontend:communication:newsletter_detail", pk=newsletter.pk)

    action = request.POST.get("action", "send")

    if action == "schedule":
        scheduled_for = request.POST.get("scheduled_for")
        if scheduled_for:
            newsletter.scheduled_for = scheduled_for
            newsletter.status = NewsletterStatus.SCHEDULED
            newsletter.save(update_fields=["scheduled_for", "status", "updated_at"])
            messages.success(request, _("Infolettre planifiee."))
        else:
            messages.error(request, _("Veuillez specifier une date de planification."))
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
        messages.success(request, _("Infolettre envoyee."))

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

    messages.success(request, _("Toutes les notifications ont ete marquees comme lues."))
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


# ─── SMS Views ───────────────────────────────────────────────────────────────────


@login_required
def sms_compose(request):
    """Compose and send an SMS (staff only)."""
    if not _is_staff(request):
        messages.error(request, _("Acces refuse."))
        return redirect("/")

    if request.method == 'POST':
        form = SMSComposeForm(request.POST)
        if form.is_valid():
            sms = form.save(commit=False)
            member = _get_member(request)
            if member:
                sms.sent_by = member
            sms.save()

            from .services_sms import TwilioSMSService
            service = TwilioSMSService()
            service.send_sms(sms)

            messages.success(request, _('SMS envoye.'))
            return redirect('/communication/sms/')
    else:
        form = SMSComposeForm()

    templates = SMSTemplate.objects.filter(is_active=True)
    context = {
        'form': form,
        'templates': templates,
        'page_title': _('Composer un SMS'),
    }
    return render(request, 'communication/sms_compose.html', context)


@login_required
def sms_list(request):
    """List sent SMS messages (staff only)."""
    if not _is_staff(request):
        messages.error(request, _("Acces refuse."))
        return redirect("/")

    sms_messages = SMSMessage.objects.all()
    paginator = Paginator(sms_messages, 20)
    page = request.GET.get('page', 1)
    sms_page = paginator.get_page(page)

    context = {
        'sms_messages': sms_page,
        'page_title': _('Messages SMS'),
    }
    return render(request, 'communication/sms_list.html', context)


@login_required
def sms_template_list(request):
    """List SMS templates (staff only)."""
    if not _is_staff(request):
        messages.error(request, _("Acces refuse."))
        return redirect("/")

    templates = SMSTemplate.objects.all()
    context = {
        'templates': templates,
        'page_title': _('Modeles SMS'),
    }
    return render(request, 'communication/sms_template_list.html', context)


@login_required
def sms_template_create(request):
    """Create an SMS template (staff only)."""
    if not _is_staff(request):
        messages.error(request, _("Acces refuse."))
        return redirect("/")

    if request.method == 'POST':
        form = SMSTemplateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Modele SMS cree.'))
            return redirect('/communication/sms/templates/')
    else:
        form = SMSTemplateForm()

    context = {
        'form': form,
        'page_title': _('Nouveau modele SMS'),
    }
    return render(request, 'communication/sms_template_form.html', context)


@login_required
def sms_template_edit(request, pk):
    """Edit an SMS template (staff only)."""
    if not _is_staff(request):
        messages.error(request, _("Acces refuse."))
        return redirect("/")

    template = get_object_or_404(SMSTemplate, pk=pk)

    if request.method == 'POST':
        form = SMSTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, _('Modele SMS mis a jour.'))
            return redirect('/communication/sms/templates/')
    else:
        form = SMSTemplateForm(instance=template)

    context = {
        'form': form,
        'template': template,
        'page_title': _('Modifier le modele SMS'),
    }
    return render(request, 'communication/sms_template_form.html', context)


# ─── Email Template Views ───────────────────────────────────────────────────────


@login_required
def email_template_list(request):
    """List email templates (staff only)."""
    if not _is_staff(request):
        messages.error(request, _("Acces refuse."))
        return redirect("/")

    templates = EmailTemplate.objects.all()
    context = {
        'templates': templates,
        'page_title': _('Modeles de courriel'),
    }
    return render(request, 'communication/email_template_list.html', context)


@login_required
def email_template_create(request):
    """Create an email template (staff only)."""
    if not _is_staff(request):
        messages.error(request, _("Acces refuse."))
        return redirect("/")

    if request.method == 'POST':
        form = EmailTemplateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Modele de courriel cree.'))
            return redirect('/communication/email-templates/')
    else:
        form = EmailTemplateForm()

    context = {
        'form': form,
        'page_title': _('Nouveau modele de courriel'),
    }
    return render(request, 'communication/email_template_form.html', context)


@login_required
def email_template_edit(request, pk):
    """Edit an email template (staff only)."""
    if not _is_staff(request):
        messages.error(request, _("Acces refuse."))
        return redirect("/")

    template = get_object_or_404(EmailTemplate, pk=pk)

    if request.method == 'POST':
        form = EmailTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, _('Modele de courriel mis a jour.'))
            return redirect('/communication/email-templates/')
    else:
        form = EmailTemplateForm(instance=template)

    context = {
        'form': form,
        'template': template,
        'page_title': _('Modifier le modele de courriel'),
    }
    return render(request, 'communication/email_template_form.html', context)


@login_required
def email_template_preview(request, pk):
    """Preview an email template with sample data (staff only)."""
    if not _is_staff(request):
        messages.error(request, _("Acces refuse."))
        return redirect("/")

    template = get_object_or_404(EmailTemplate, pk=pk)

    # Sample merge fields for preview
    sample_context = {
        'member_name': 'Jean Dupont',
        'event_title': 'Culte du dimanche',
        'church_name': 'EgliseConnect',
    }

    subject = template.subject_template
    body = template.body_html_template
    for key, value in sample_context.items():
        subject = subject.replace('{{' + key + '}}', value)
        body = body.replace('{{' + key + '}}', value)

    context = {
        'template': template,
        'preview_subject': subject,
        'preview_body': body,
        'page_title': _('Apercu du modele'),
    }
    return render(request, 'communication/email_template_preview.html', context)


# ─── Push Notification Views ────────────────────────────────────────────────────


@login_required
def push_test(request):
    """Push notification test page for admin."""
    if not _is_staff(request):
        messages.error(request, _("Acces refuse."))
        return redirect("/")

    if request.method == 'POST':
        title = request.POST.get('title', 'Test')
        body = request.POST.get('body', 'Ceci est un test.')
        target = request.POST.get('target', 'self')

        from .services_push import WebPushService
        service = WebPushService()

        if target == 'all':
            count = service.send_to_all(title, body)
            messages.success(request, _('Notification push envoyee a %d abonnes.') % count)
        else:
            member = _get_member(request)
            if member:
                count = service.send_to_member(member, title, body)
                messages.success(request, _('Notification push envoyee (%d abonnements).') % count)
            else:
                messages.error(request, _('Profil membre requis.'))

        return redirect('/communication/push/test/')

    subscription_count = PushSubscription.objects.filter(is_active=True).count()
    context = {
        'page_title': _('Test de notification push'),
        'subscription_count': subscription_count,
    }
    return render(request, 'communication/push_test.html', context)


# ─── Automation Views ────────────────────────────────────────────────────────────


@login_required
def automation_list(request):
    """List all automations (staff only)."""
    if not _is_staff(request):
        messages.error(request, _("Acces refuse."))
        return redirect("/")

    automations = Automation.objects.all().annotate(
        enrollment_count=Count('enrollments'),
        active_count=Count('enrollments', filter=Q(enrollments__status=AutomationStatus.ACTIVE)),
        completed_count=Count('enrollments', filter=Q(enrollments__status=AutomationStatus.COMPLETED)),
    )

    context = {
        'automations': automations,
        'page_title': _('Automatisations'),
    }
    return render(request, 'communication/automation_list.html', context)


@login_required
def automation_create(request):
    """Create a new automation (staff only)."""
    if not _is_staff(request):
        messages.error(request, _("Acces refuse."))
        return redirect("/")

    if request.method == 'POST':
        form = AutomationForm(request.POST)
        if form.is_valid():
            automation = form.save(commit=False)
            member = _get_member(request)
            if member:
                automation.created_by = member
            automation.save()
            messages.success(request, _('Automatisation creee.'))
            return redirect('/communication/automations/%s/' % automation.pk)
    else:
        form = AutomationForm()

    context = {
        'form': form,
        'page_title': _('Nouvelle automatisation'),
    }
    return render(request, 'communication/automation_form.html', context)


@login_required
def automation_detail(request, pk):
    """Detail view for an automation with steps and enrollment stats."""
    if not _is_staff(request):
        messages.error(request, _("Acces refuse."))
        return redirect("/")

    automation = get_object_or_404(Automation, pk=pk)
    steps = automation.steps.order_by('order')
    enrollments = automation.enrollments.all().select_related('member')

    stats = {
        'total': enrollments.count(),
        'active': enrollments.filter(status=AutomationStatus.ACTIVE).count(),
        'completed': enrollments.filter(status=AutomationStatus.COMPLETED).count(),
        'cancelled': enrollments.filter(status=AutomationStatus.CANCELLED).count(),
    }

    context = {
        'automation': automation,
        'steps': steps,
        'enrollments': enrollments[:20],
        'stats': stats,
        'page_title': automation.name,
    }
    return render(request, 'communication/automation_detail.html', context)


@login_required
def automation_step_add(request, pk):
    """Add a step to an automation (staff only)."""
    if not _is_staff(request):
        messages.error(request, _("Acces refuse."))
        return redirect("/")

    automation = get_object_or_404(Automation, pk=pk)

    if request.method == 'POST':
        form = AutomationStepForm(request.POST)
        if form.is_valid():
            step = form.save(commit=False)
            step.automation = automation
            step.save()
            messages.success(request, _('Etape ajoutee.'))
            return redirect('/communication/automations/%s/' % automation.pk)
    else:
        # Default order = next order
        next_order = (automation.steps.count())
        form = AutomationStepForm(initial={'order': next_order})

    context = {
        'form': form,
        'automation': automation,
        'page_title': _('Ajouter une etape'),
    }
    return render(request, 'communication/automation_step_form.html', context)


# ─── Analytics Dashboard ─────────────────────────────────────────────────────────


@login_required
def analytics_dashboard(request):
    """Communication analytics dashboard (staff only)."""
    if not _is_staff(request):
        messages.error(request, _("Acces refuse."))
        return redirect("/")

    # Newsletter stats
    newsletters = Newsletter.objects.filter(status=NewsletterStatus.SENT)
    total_sent = newsletters.count()
    total_recipients = newsletters.aggregate(total=Sum('recipients_count'))['total'] or 0
    total_opens = newsletters.aggregate(total=Sum('opened_count'))['total'] or 0
    avg_open_rate = (total_opens / total_recipients * 100) if total_recipients > 0 else 0

    # Recent newsletters with open rates
    recent_newsletters = newsletters.order_by('-sent_at')[:10]

    # Subscriber growth (members with email over time)
    subscriber_growth = Member.objects.filter(
        email__isnull=False,
    ).exclude(email='').annotate(
        date=TruncDate('created_at'),
    ).values('date').annotate(
        count=Count('id'),
    ).order_by('date')[:30]

    # SMS stats
    sms_total = SMSMessage.objects.count()
    sms_delivered = SMSMessage.objects.filter(status='delivered').count()
    sms_failed = SMSMessage.objects.filter(status='failed').count()

    # Automation stats
    automation_total = Automation.objects.count()
    automation_active_enrollments = AutomationEnrollment.objects.filter(
        status=AutomationStatus.ACTIVE,
    ).count()

    # Engagement trends (newsletters sent per week for last 8 weeks)
    eight_weeks_ago = timezone.now() - timezone.timedelta(weeks=8)
    engagement_data = newsletters.filter(
        sent_at__gte=eight_weeks_ago,
    ).annotate(
        date=TruncDate('sent_at'),
    ).values('date').annotate(
        recipients=Sum('recipients_count'),
        opens=Sum('opened_count'),
    ).order_by('date')

    context = {
        'page_title': _('Tableau de bord analytique'),
        'total_sent': total_sent,
        'total_recipients': total_recipients,
        'total_opens': total_opens,
        'avg_open_rate': round(avg_open_rate, 1),
        'recent_newsletters': recent_newsletters,
        'subscriber_growth': list(subscriber_growth),
        'sms_total': sms_total,
        'sms_delivered': sms_delivered,
        'sms_failed': sms_failed,
        'automation_total': automation_total,
        'automation_active_enrollments': automation_active_enrollments,
        'engagement_data': list(engagement_data),
    }
    return render(request, 'communication/analytics_dashboard.html', context)


# ─── A/B Test Views ──────────────────────────────────────────────────────────────


@login_required
def abtest_results(request, pk):
    """View A/B test results for a newsletter (staff only)."""
    if not _is_staff(request):
        messages.error(request, _("Acces refuse."))
        return redirect("/")

    abtest = get_object_or_404(ABTest, pk=pk)

    # Calculate rates
    total_a = abtest.variant_a_opens + abtest.variant_a_clicks
    total_b = abtest.variant_b_opens + abtest.variant_b_clicks

    context = {
        'abtest': abtest,
        'total_a': total_a,
        'total_b': total_b,
        'page_title': _('Resultats du test A/B'),
    }
    return render(request, 'communication/abtest_results.html', context)


# ─── Direct Messaging Views ─────────────────────────────────────────────────────


@login_required
def message_inbox(request):
    """View inbox for direct messages."""
    member = _get_member(request)
    if not member:
        messages.error(request, _("Profil requis."))
        return redirect("/")

    received = DirectMessage.objects.filter(recipient=member).select_related('sender')
    sent = DirectMessage.objects.filter(sender=member).select_related('recipient')

    tab = request.GET.get('tab', 'inbox')

    if tab == 'sent':
        msg_list = sent
    else:
        msg_list = received

    paginator = Paginator(msg_list, 20)
    page = request.GET.get('page', 1)
    messages_page = paginator.get_page(page)

    context = {
        'messages_list': messages_page,
        'tab': tab,
        'page_title': _('Messagerie'),
    }
    return render(request, 'communication/message_inbox.html', context)


@login_required
def message_compose(request):
    """Compose a new direct message."""
    member = _get_member(request)
    if not member:
        messages.error(request, _("Profil requis."))
        return redirect("/")

    if request.method == 'POST':
        form = DirectMessageForm(request.POST)
        if form.is_valid():
            dm = form.save(commit=False)
            dm.sender = member
            dm.save()
            messages.success(request, _('Message envoye.'))
            return redirect('/communication/messages/')
    else:
        initial = {}
        recipient_id = request.GET.get('to')
        if recipient_id:
            initial['recipient'] = recipient_id
        form = DirectMessageForm(initial=initial)

    context = {
        'form': form,
        'page_title': _('Nouveau message'),
    }
    return render(request, 'communication/message_compose.html', context)


@login_required
def message_detail(request, pk):
    """View a single message and mark it as read."""
    member = _get_member(request)
    if not member:
        messages.error(request, _("Profil requis."))
        return redirect("/")

    dm = get_object_or_404(DirectMessage, pk=pk)

    # Only sender or recipient can view
    if dm.sender != member and dm.recipient != member:
        messages.error(request, _("Acces refuse."))
        return redirect('/communication/messages/')

    # Mark as read if recipient
    if dm.recipient == member and not dm.read_at:
        dm.read_at = timezone.now()
        dm.save(update_fields=['read_at', 'updated_at'])

    context = {
        'dm': dm,
        'page_title': _('Message'),
    }
    return render(request, 'communication/message_detail.html', context)


# ─── Group Chat Views ───────────────────────────────────────────────────────────


@login_required
def group_chat_list(request):
    """List group chats the member belongs to."""
    member = _get_member(request)
    if not member:
        messages.error(request, _("Profil requis."))
        return redirect("/")

    chats = GroupChat.objects.filter(members=member)

    context = {
        'chats': chats,
        'page_title': _('Discussions de groupe'),
    }
    return render(request, 'communication/group_chat_list.html', context)


@login_required
def group_chat_create(request):
    """Create a new group chat (staff only)."""
    if not _is_staff(request):
        messages.error(request, _("Acces refuse."))
        return redirect("/")

    member = _get_member(request)

    if request.method == 'POST':
        form = GroupChatForm(request.POST)
        if form.is_valid():
            chat = form.save(commit=False)
            chat.created_by = member
            chat.save()
            form.save_m2m()
            # Ensure creator is a member
            if member:
                chat.members.add(member)
            messages.success(request, _('Discussion de groupe creee.'))
            return redirect('/communication/group-chats/%s/' % chat.pk)
    else:
        form = GroupChatForm()

    context = {
        'form': form,
        'page_title': _('Nouvelle discussion de groupe'),
    }
    return render(request, 'communication/group_chat_form.html', context)


@login_required
def group_chat_detail(request, pk):
    """View and post to a group chat."""
    member = _get_member(request)
    if not member:
        messages.error(request, _("Profil requis."))
        return redirect("/")

    chat = get_object_or_404(GroupChat, pk=pk)

    # Check membership
    if not chat.members.filter(pk=member.pk).exists() and not _is_staff(request):
        messages.error(request, _("Vous n'etes pas membre de cette discussion."))
        return redirect('/communication/group-chats/')

    if request.method == 'POST':
        form = GroupChatMessageForm(request.POST)
        if form.is_valid():
            GroupChatMessage.objects.create(
                chat=chat,
                sender=member,
                body=form.cleaned_data['body'],
            )
            return redirect('/communication/group-chats/%s/' % chat.pk)
    else:
        form = GroupChatMessageForm()

    chat_messages = chat.messages.select_related('sender').order_by('sent_at')

    context = {
        'chat': chat,
        'chat_messages': chat_messages,
        'form': form,
        'page_title': chat.name,
    }
    return render(request, 'communication/group_chat_detail.html', context)


# ─── Social Media Stubs ─────────────────────────────────────────────────────────


@login_required
def social_media_dashboard(request):
    """Social media integration dashboard (stub)."""
    if not _is_staff(request):
        messages.error(request, _("Acces refuse."))
        return redirect("/")

    context = {
        'page_title': _('Reseaux sociaux'),
        'facebook_connected': False,
        'instagram_connected': False,
        'whatsapp_connected': False,
    }
    return render(request, 'communication/social_media_dashboard.html', context)
