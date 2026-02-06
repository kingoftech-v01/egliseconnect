"""Communication Frontend Views."""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils.translation import gettext_lazy as _

from apps.core.constants import Roles

from .models import Newsletter, Notification, NotificationPreference
from .forms import NewsletterForm


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
    context = {'newsletter': newsletter, 'page_title': newsletter.subject}
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

    context = {'form': form, 'page_title': _('Nouvelle infolettre')}
    return render(request, 'communication/newsletter_form.html', context)


@login_required
def notification_list(request):
    if not hasattr(request.user, 'member_profile'):
        messages.error(request, _("Profil requis."))
        return redirect('/')

    notifications = Notification.objects.filter(member=request.user.member_profile)
    paginator = Paginator(notifications, 20)
    page = request.GET.get('page', 1)
    notifications_page = paginator.get_page(page)

    context = {'notifications': notifications_page, 'page_title': _('Notifications')}
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
