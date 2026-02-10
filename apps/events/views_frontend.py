"""Events frontend views."""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.constants import Roles, RSVPStatus, EventType

from .models import Event, EventRSVP
from .forms import EventForm, RSVPForm


# Color map for calendar event type coding
EVENT_TYPE_COLORS = {
    EventType.WORSHIP: "#6a5acd",    # Violet
    EventType.GROUP: "#28a745",      # Vert
    EventType.MEAL: "#fd7e14",       # Orange
    EventType.SPECIAL: "#dc3545",    # Rouge
    EventType.MEETING: "#17a2b8",    # Cyan
    EventType.TRAINING: "#007bff",   # Bleu
    EventType.OUTREACH: "#ffc107",   # Jaune
    EventType.OTHER: "#6c757d",      # Gris
}


@login_required
def event_list(request):
    """Display paginated event list with search, type filter, and upcoming/past separation."""
    events = Event.objects.filter(is_published=True, is_cancelled=False).order_by('start_datetime')

    # Search by title
    q = request.GET.get('q', '').strip()
    if q:
        events = events.filter(Q(title__icontains=q) | Q(description__icontains=q))

    # Filter by event type
    event_type = request.GET.get('type')
    if event_type:
        events = events.filter(event_type=event_type)

    # Separate upcoming vs past
    now = timezone.now()
    upcoming = request.GET.get('upcoming')
    past = request.GET.get('past')

    if upcoming:
        events = events.filter(start_datetime__gte=now)
    elif past:
        events = events.filter(start_datetime__lt=now)

    paginator = Paginator(events, 20)
    page = request.GET.get('page', 1)
    events_page = paginator.get_page(page)

    # Count upcoming/past for display
    base_qs = Event.objects.filter(is_published=True, is_cancelled=False)
    if q:
        base_qs = base_qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
    if event_type:
        base_qs = base_qs.filter(event_type=event_type)
    upcoming_count = base_qs.filter(start_datetime__gte=now).count()
    past_count = base_qs.filter(start_datetime__lt=now).count()

    context = {
        'events': events_page,
        'page_title': _('Événements'),
        'event_type_choices': EventType.CHOICES,
        'selected_type': event_type or '',
        'search_query': q,
        'upcoming_count': upcoming_count,
        'past_count': past_count,
        'filter_upcoming': upcoming,
        'filter_past': past,
    }
    return render(request, 'events/event_list.html', context)


@login_required
def event_detail(request, pk):
    """Display event details, full attendee list, and user RSVP status."""
    event = get_object_or_404(Event, pk=pk)
    user_rsvp = None
    is_staff = False

    if hasattr(request.user, 'member_profile'):
        user_rsvp = EventRSVP.objects.filter(event=event, member=request.user.member_profile).first()
        is_staff = request.user.member_profile.role in [Roles.ADMIN, Roles.PASTOR]

    # Full attendee list (no limit)
    all_attendees = event.rsvps.filter(status=RSVPStatus.CONFIRMED).select_related('member')

    context = {
        'event': event,
        'user_rsvp': user_rsvp,
        'attendees': all_attendees,
        'is_staff': is_staff,
        'page_title': event.title,
    }
    return render(request, 'events/event_detail.html', context)


@login_required
def event_rsvp(request, pk):
    """Handle RSVP form submission."""
    event = get_object_or_404(Event, pk=pk)
    if not hasattr(request.user, 'member_profile'):
        messages.error(request, _("Profil membre requis."))
        return redirect('frontend:events:event_detail', pk=pk)

    member = request.user.member_profile

    if request.method == 'POST':
        rsvp_status = request.POST.get('status', RSVPStatus.CONFIRMED)
        try:
            guests = int(request.POST.get('guests', 0))
        except (ValueError, TypeError):
            guests = 0

        rsvp, created = EventRSVP.objects.update_or_create(
            event=event,
            member=member,
            defaults={'status': rsvp_status, 'guests': guests}
        )
        messages.success(request, _('RSVP enregistré.'))

    return redirect('frontend:events:event_detail', pk=pk)


@login_required
def event_cancel(request, pk):
    """Cancel an event (staff only, sets is_cancelled=True)."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Accès refusé.'))
        return redirect('/')

    event = get_object_or_404(Event, pk=pk)

    if request.method == 'POST':
        event.is_cancelled = True
        event.save()
        messages.success(request, _('Événement annulé avec succès.'))
        return redirect(f'/events/{pk}/')

    return redirect(f'/events/{pk}/')


@login_required
def event_calendar(request):
    """Render the calendar page with event type color coding."""
    context = {
        'page_title': _('Calendrier'),
        'event_type_colors': EVENT_TYPE_COLORS,
        'event_type_choices': EventType.CHOICES,
    }
    return render(request, 'events/event_calendar.html', context)


@login_required
def event_create(request):
    """Create a new event (admin/pastor only)."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Accès refusé.'))
        return redirect('/')

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, _('Événement créé avec succès.'))
            return redirect('/events/')
    else:
        form = EventForm()

    context = {
        'form': form,
        'page_title': _('Nouvel événement'),
    }
    return render(request, 'events/event_form.html', context)


@login_required
def event_update(request, pk):
    """Update an existing event (admin/pastor only)."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Accès refusé.'))
        return redirect('/')

    event = get_object_or_404(Event, pk=pk)

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, _('Événement modifié avec succès.'))
            return redirect(f'/events/{pk}/')
    else:
        form = EventForm(instance=event)

    context = {
        'form': form,
        'event': event,
        'page_title': _("Modifier l'événement"),
    }
    return render(request, 'events/event_form.html', context)


@login_required
def event_delete(request, pk):
    """Delete an event (admin/pastor only)."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Accès refusé.'))
        return redirect('/')

    event = get_object_or_404(Event, pk=pk)

    if request.method == 'POST':
        event.delete()
        messages.success(request, _('Événement supprimé.'))
        return redirect('/events/')

    context = {
        'event': event,
        'page_title': _("Supprimer l'événement"),
    }
    return render(request, 'events/event_delete.html', context)
