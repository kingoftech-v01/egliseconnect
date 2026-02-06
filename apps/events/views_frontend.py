"""Events frontend views."""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.constants import Roles, RSVPStatus

from .models import Event, EventRSVP
from .forms import EventForm, RSVPForm


@login_required
def event_list(request):
    """Display paginated event list with optional type and date filters."""
    events = Event.objects.filter(is_published=True, is_cancelled=False).order_by('start_datetime')
    event_type = request.GET.get('type')
    if event_type:
        events = events.filter(event_type=event_type)

    upcoming = request.GET.get('upcoming')
    if upcoming:
        events = events.filter(start_datetime__gte=timezone.now())

    paginator = Paginator(events, 20)
    page = request.GET.get('page', 1)
    events_page = paginator.get_page(page)

    context = {
        'events': events_page,
        'page_title': _('Événements'),
    }
    return render(request, 'events/event_list.html', context)


@login_required
def event_detail(request, pk):
    """Display event details and user's RSVP status."""
    event = get_object_or_404(Event, pk=pk)
    user_rsvp = None
    if hasattr(request.user, 'member_profile'):
        user_rsvp = EventRSVP.objects.filter(event=event, member=request.user.member_profile).first()

    context = {
        'event': event,
        'user_rsvp': user_rsvp,
        'attendees': event.rsvps.filter(status=RSVPStatus.CONFIRMED).select_related('member')[:10],
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
def event_calendar(request):
    """Render the calendar page (data loaded via API)."""
    context = {'page_title': _('Calendrier')}
    return render(request, 'events/event_calendar.html', context)
