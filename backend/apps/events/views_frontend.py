"""Events frontend views — events, rooms, bookings, kiosk, calendar export,
templates, waitlist, volunteer needs, photos, surveys."""
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt

from apps.core.constants import Roles, RSVPStatus, EventType, BookingStatus, VolunteerSignupStatus

from .models import (
    Event, EventRSVP, Room, RoomBooking, EventTemplate,
    RegistrationForm, RegistrationEntry,
    EventWaitlist, EventVolunteerNeed, EventVolunteerSignup,
    EventPhoto, EventSurvey, SurveyResponse,
)
from .forms import (
    EventForm, RSVPForm, RoomForm, RoomBookingForm,
    EventTemplateForm, EventFromTemplateForm, EventVolunteerNeedForm,
    EventPhotoForm, EventSurveyForm,
)
from .services_facility import FacilityService
from .services_calendar import CalendarService


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

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


def _is_staff(request):
    """Check if the current user is admin or pastor."""
    if not hasattr(request.user, 'member_profile'):
        return False
    return request.user.member_profile.role in [Roles.ADMIN, Roles.PASTOR]


def _require_staff(request):
    """Return redirect if not staff, else None."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if not _is_staff(request):
        messages.error(request, _('Accès refusé.'))
        return redirect('/')
    return None


# ──────────────────────────────────────────────────────────────────────────────
# Event CRUD
# ──────────────────────────────────────────────────────────────────────────────

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
    """Display event details, full attendee list, calendar links, and user RSVP status."""
    event = get_object_or_404(Event, pk=pk)
    user_rsvp = None
    is_staff = False

    if hasattr(request.user, 'member_profile'):
        user_rsvp = EventRSVP.objects.filter(event=event, member=request.user.member_profile).first()
        is_staff = request.user.member_profile.role in [Roles.ADMIN, Roles.PASTOR]

    # Full attendee list (no limit)
    all_attendees = event.rsvps.filter(status=RSVPStatus.CONFIRMED).select_related('member')

    # All attendees with any RSVP status
    all_rsvps = event.rsvps.select_related('member').order_by('status')

    # Calendar links
    google_url = CalendarService.google_calendar_url(event)
    outlook_url = CalendarService.outlook_calendar_url(event)

    # Volunteer needs
    volunteer_needs = event.volunteer_needs.all()

    # Waitlist
    waitlist_entries = event.waitlist_entries.order_by('position')

    # Photos
    photos = event.photos.filter(is_approved=True)

    context = {
        'event': event,
        'user_rsvp': user_rsvp,
        'attendees': all_attendees,
        'all_rsvps': all_rsvps,
        'is_staff': is_staff,
        'page_title': event.title,
        'google_calendar_url': google_url,
        'outlook_calendar_url': outlook_url,
        'volunteer_needs': volunteer_needs,
        'waitlist_entries': waitlist_entries,
        'photos': photos,
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

        # If event is full and user is trying to confirm, add to waitlist
        if (event.is_full and rsvp_status == RSVPStatus.CONFIRMED
                and not EventRSVP.objects.filter(event=event, member=member).exists()):
            # Add to waitlist instead
            position = event.waitlist_entries.count() + 1
            EventWaitlist.objects.get_or_create(
                event=event, member=member,
                defaults={'position': position},
            )
            messages.info(request, _("L'événement est complet. Vous avez été ajouté à la liste d'attente (position %d).") % position)
            return redirect('frontend:events:event_detail', pk=pk)

        rsvp, created = EventRSVP.objects.update_or_create(
            event=event,
            member=member,
            defaults={'status': rsvp_status, 'guests': guests}
        )

        # If RSVP is cancelled/declined, promote from waitlist
        if rsvp_status == RSVPStatus.DECLINED:
            _promote_from_waitlist(event)

        messages.success(request, _('RSVP enregistré.'))

    return redirect('frontend:events:event_detail', pk=pk)


def _promote_from_waitlist(event):
    """Promote the next person from the waitlist when a spot opens."""
    if event.is_full:
        return
    next_entry = event.waitlist_entries.filter(promoted_at__isnull=True).order_by('position').first()
    if next_entry:
        EventRSVP.objects.update_or_create(
            event=event,
            member=next_entry.member,
            defaults={'status': RSVPStatus.CONFIRMED, 'guests': 0},
        )
        next_entry.promoted_at = timezone.now()
        next_entry.save(update_fields=['promoted_at', 'updated_at'])


@login_required
def event_cancel(request, pk):
    """Cancel an event (staff only, sets is_cancelled=True)."""
    denied = _require_staff(request)
    if denied:
        return denied

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
    denied = _require_staff(request)
    if denied:
        return denied

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save()
            # Auto-create attendance session for the event
            from apps.attendance.models import AttendanceSession
            from apps.core.constants import AttendanceSessionType, EventType
            session_type_map = {
                EventType.WORSHIP: AttendanceSessionType.WORSHIP,
                EventType.TRAINING: AttendanceSessionType.LESSON,
            }
            AttendanceSession.objects.create(
                name=event.title,
                session_type=session_type_map.get(event.event_type, AttendanceSessionType.EVENT),
                date=event.start_datetime.date(),
                start_time=event.start_datetime.time(),
                end_time=event.end_datetime.time() if event.end_datetime else None,
                event=event,
                opened_by=getattr(request.user, 'member_profile', None),
            )
            # Generate recurring instances if applicable
            if event.is_recurring and event.recurrence_frequency:
                from .services_recurrence import RecurrenceService
                RecurrenceService.generate_instances(event)
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
    denied = _require_staff(request)
    if denied:
        return denied

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
    denied = _require_staff(request)
    if denied:
        return denied

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


# ──────────────────────────────────────────────────────────────────────────────
# Calendar Export / .ics
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def event_ics_download(request, pk):
    """Download a single event as .ics file."""
    event = get_object_or_404(Event, pk=pk)
    ical_data = CalendarService.generate_ical_event(event)
    response = HttpResponse(ical_data, content_type='text/calendar; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{event.title}.ics"'
    return response


@login_required
def event_ics_feed(request):
    """Full iCal feed of published events for calendar subscription."""
    events = Event.objects.filter(is_published=True, is_cancelled=False).order_by('start_datetime')
    ical_data = CalendarService.generate_ical_feed(events)
    response = HttpResponse(ical_data, content_type='text/calendar; charset=utf-8')
    response['Content-Disposition'] = 'inline; filename="egliseconnect.ics"'
    return response


# ──────────────────────────────────────────────────────────────────────────────
# Room CRUD
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def room_list(request):
    """Display all rooms."""
    rooms = Room.objects.all()
    context = {
        'rooms': rooms,
        'page_title': _('Salles'),
        'is_staff': _is_staff(request),
    }
    return render(request, 'events/room_list.html', context)


@login_required
def room_create(request):
    """Create a new room (staff only)."""
    denied = _require_staff(request)
    if denied:
        return denied

    if request.method == 'POST':
        form = RoomForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, _('Salle créée avec succès.'))
            return redirect('/events/rooms/')
    else:
        form = RoomForm()

    context = {
        'form': form,
        'page_title': _('Nouvelle salle'),
    }
    return render(request, 'events/room_form.html', context)


@login_required
def room_update(request, pk):
    """Update a room (staff only)."""
    denied = _require_staff(request)
    if denied:
        return denied

    room = get_object_or_404(Room, pk=pk)

    if request.method == 'POST':
        form = RoomForm(request.POST, request.FILES, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, _('Salle modifiée avec succès.'))
            return redirect('/events/rooms/')
    else:
        form = RoomForm(instance=room)

    context = {
        'form': form,
        'room': room,
        'page_title': _('Modifier la salle'),
    }
    return render(request, 'events/room_form.html', context)


@login_required
def room_delete(request, pk):
    """Delete a room (staff only)."""
    denied = _require_staff(request)
    if denied:
        return denied

    room = get_object_or_404(Room, pk=pk)
    if request.method == 'POST':
        room.delete()
        messages.success(request, _('Salle supprimée.'))
        return redirect('/events/rooms/')

    context = {
        'room': room,
        'page_title': _('Supprimer la salle'),
    }
    return render(request, 'events/room_delete.html', context)


@login_required
def room_calendar(request, pk):
    """Show booking calendar for a room."""
    room = get_object_or_404(Room, pk=pk)
    bookings = FacilityService.get_room_bookings(room)
    context = {
        'room': room,
        'bookings': bookings,
        'page_title': f'Calendrier - {room.name}',
        'is_staff': _is_staff(request),
    }
    return render(request, 'events/room_calendar.html', context)


# ──────────────────────────────────────────────────────────────────────────────
# Room Booking
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def booking_list(request):
    """Display all bookings (staff sees all, others see own)."""
    if _is_staff(request):
        bookings = RoomBooking.objects.all().select_related('room', 'booked_by', 'event')
    else:
        member = getattr(request.user, 'member_profile', None)
        bookings = RoomBooking.objects.filter(booked_by=member).select_related('room', 'event') if member else RoomBooking.objects.none()

    context = {
        'bookings': bookings,
        'page_title': _('Réservations'),
        'is_staff': _is_staff(request),
    }
    return render(request, 'events/booking_list.html', context)


@login_required
def booking_create(request):
    """Create a new room booking."""
    if request.method == 'POST':
        form = RoomBookingForm(request.POST)
        if form.is_valid():
            room = form.cleaned_data['room']
            start = form.cleaned_data['start_datetime']
            end = form.cleaned_data['end_datetime']
            member = getattr(request.user, 'member_profile', None)
            booking, error = FacilityService.book_room(
                room=room,
                start_datetime=start,
                end_datetime=end,
                booked_by=member,
                event=form.cleaned_data.get('event'),
                notes=form.cleaned_data.get('notes', ''),
            )
            if error:
                messages.error(request, error)
            else:
                messages.success(request, _('Réservation créée avec succès.'))
                return redirect('/events/bookings/')
    else:
        form = RoomBookingForm()

    context = {
        'form': form,
        'page_title': _('Nouvelle réservation'),
    }
    return render(request, 'events/booking_form.html', context)


@login_required
def booking_action(request, pk, action):
    """Approve, reject, or cancel a booking (staff only)."""
    denied = _require_staff(request)
    if denied:
        return denied

    booking = get_object_or_404(RoomBooking, pk=pk)
    if request.method == 'POST':
        if action == 'approve':
            ok, err = FacilityService.approve_booking(booking)
        elif action == 'reject':
            ok, err = FacilityService.reject_booking(booking)
        elif action == 'cancel':
            ok, err = FacilityService.cancel_booking(booking)
        else:
            messages.error(request, _('Action invalide.'))
            return redirect('/events/bookings/')

        if err:
            messages.error(request, err)
        else:
            messages.success(request, _('Action effectuée.'))

    return redirect('/events/bookings/')


# ──────────────────────────────────────────────────────────────────────────────
# Kiosk Check-In
# ──────────────────────────────────────────────────────────────────────────────

@csrf_exempt
def kiosk_checkin(request, pk):
    """Touch-friendly kiosk check-in page. No login required."""
    event = get_object_or_404(Event, pk=pk)

    search_results = []
    checked_in = False
    search_query = ''

    if request.method == 'POST':
        search_query = request.POST.get('search', '').strip()
        member_id = request.POST.get('member_id')

        if member_id:
            # Check in the member
            from apps.members.models import Member
            try:
                member = Member.objects.get(pk=member_id)
                rsvp, created = EventRSVP.objects.update_or_create(
                    event=event,
                    member=member,
                    defaults={'status': RSVPStatus.CONFIRMED},
                )
                checked_in = True
                # Also create attendance record if event has a session
                from apps.attendance.models import AttendanceSession, AttendanceRecord
                from apps.core.constants import CheckInMethod
                att_session = AttendanceSession.objects.filter(
                    event=event, is_open=True
                ).first()
                if att_session:
                    AttendanceRecord.objects.get_or_create(
                        session=att_session,
                        member=member,
                        defaults={'method': CheckInMethod.KIOSK},
                    )
                messages.success(request, _('%(name)s a été enregistré(e).') % {'name': member.full_name})
            except Exception:
                messages.error(request, _('Membre introuvable.'))
        elif search_query:
            from apps.members.models import Member
            search_results = Member.objects.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )[:20]

    attendee_count = event.rsvps.filter(status=RSVPStatus.CONFIRMED).count()

    context = {
        'event': event,
        'search_results': search_results,
        'search_query': search_query,
        'checked_in': checked_in,
        'attendee_count': attendee_count,
        'page_title': f'Kiosque - {event.title}',
    }
    return render(request, 'events/kiosk_checkin.html', context)


# ──────────────────────────────────────────────────────────────────────────────
# Event Templates
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def template_list(request):
    """List all event templates."""
    templates = EventTemplate.objects.all()
    context = {
        'templates': templates,
        'page_title': _("Modèles d'événements"),
        'is_staff': _is_staff(request),
    }
    return render(request, 'events/template_list.html', context)


@login_required
def template_create(request):
    """Create a new event template (staff only)."""
    denied = _require_staff(request)
    if denied:
        return denied

    if request.method == 'POST':
        form = EventTemplateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Modèle créé avec succès.'))
            return redirect('/events/templates/')
    else:
        form = EventTemplateForm()

    context = {
        'form': form,
        'page_title': _('Nouveau modèle'),
    }
    return render(request, 'events/template_form.html', context)


@login_required
def event_create_from_template(request):
    """Create an event from a template (staff only)."""
    denied = _require_staff(request)
    if denied:
        return denied

    if request.method == 'POST':
        form = EventFromTemplateForm(request.POST)
        if form.is_valid():
            template = form.cleaned_data['template']
            start = form.cleaned_data['start_datetime']
            title = form.cleaned_data.get('title_override') or template.name

            end = start
            if template.default_duration:
                end = start + template.default_duration

            event = Event.objects.create(
                title=title,
                description=template.default_description,
                event_type=template.event_type,
                start_datetime=start,
                end_datetime=end,
                max_attendees=template.default_capacity,
                location=template.default_location,
                requires_rsvp=template.requires_rsvp,
                is_published=True,
            )
            messages.success(request, _('Événement créé depuis le modèle.'))
            return redirect(f'/events/{event.pk}/')
    else:
        form = EventFromTemplateForm()

    context = {
        'form': form,
        'page_title': _('Créer depuis un modèle'),
    }
    return render(request, 'events/event_from_template.html', context)


# ──────────────────────────────────────────────────────────────────────────────
# Waitlist
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def waitlist_view(request, pk):
    """View waitlist for an event."""
    event = get_object_or_404(Event, pk=pk)
    entries = event.waitlist_entries.order_by('position').select_related('member')
    context = {
        'event': event,
        'entries': entries,
        'page_title': f"Liste d'attente - {event.title}",
        'is_staff': _is_staff(request),
    }
    return render(request, 'events/waitlist.html', context)


@login_required
def waitlist_join(request, pk):
    """Join the waitlist for an event."""
    event = get_object_or_404(Event, pk=pk)
    if not hasattr(request.user, 'member_profile'):
        messages.error(request, _("Profil membre requis."))
        return redirect('frontend:events:event_detail', pk=pk)

    member = request.user.member_profile
    if request.method == 'POST':
        if EventWaitlist.objects.filter(event=event, member=member).exists():
            messages.info(request, _("Vous êtes déjà sur la liste d'attente."))
        else:
            position = event.waitlist_entries.count() + 1
            EventWaitlist.objects.create(event=event, member=member, position=position)
            messages.success(request, _("Ajouté à la liste d'attente (position %d).") % position)

    return redirect('frontend:events:event_detail', pk=pk)


@login_required
def waitlist_promote(request, pk, entry_pk):
    """Promote a waitlist entry to confirmed RSVP (staff only)."""
    denied = _require_staff(request)
    if denied:
        return denied

    entry = get_object_or_404(EventWaitlist, pk=entry_pk, event_id=pk)
    if request.method == 'POST':
        EventRSVP.objects.update_or_create(
            event=entry.event, member=entry.member,
            defaults={'status': RSVPStatus.CONFIRMED},
        )
        entry.promoted_at = timezone.now()
        entry.save(update_fields=['promoted_at', 'updated_at'])
        messages.success(request, _('Membre promu depuis la liste d\'attente.'))

    return redirect(f'/events/{pk}/waitlist/')


# ──────────────────────────────────────────────────────────────────────────────
# Volunteer Needs
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def volunteer_needs_view(request, pk):
    """View and manage volunteer needs for an event."""
    event = get_object_or_404(Event, pk=pk)
    needs = event.volunteer_needs.all()
    is_staff = _is_staff(request)
    form = EventVolunteerNeedForm() if is_staff else None

    context = {
        'event': event,
        'needs': needs,
        'form': form,
        'page_title': f'Bénévoles - {event.title}',
        'is_staff': is_staff,
    }
    return render(request, 'events/volunteer_needs.html', context)


@login_required
def volunteer_need_create(request, pk):
    """Add a volunteer need to an event (staff only)."""
    denied = _require_staff(request)
    if denied:
        return denied

    event = get_object_or_404(Event, pk=pk)
    if request.method == 'POST':
        form = EventVolunteerNeedForm(request.POST)
        if form.is_valid():
            need = form.save(commit=False)
            need.event = event
            need.save()
            messages.success(request, _('Besoin de bénévole ajouté.'))

    return redirect(f'/events/{pk}/volunteers/')


@login_required
def volunteer_signup(request, pk, need_pk):
    """Sign up for a volunteer position."""
    event = get_object_or_404(Event, pk=pk)
    need = get_object_or_404(EventVolunteerNeed, pk=need_pk, event=event)

    if not hasattr(request.user, 'member_profile'):
        messages.error(request, _("Profil membre requis."))
        return redirect(f'/events/{pk}/volunteers/')

    member = request.user.member_profile
    if request.method == 'POST':
        signup, created = EventVolunteerSignup.objects.get_or_create(
            need=need, member=member,
            defaults={'status': VolunteerSignupStatus.PENDING},
        )
        if created:
            messages.success(request, _('Inscription au poste de bénévole enregistrée.'))
        else:
            messages.info(request, _('Vous êtes déjà inscrit(e) à ce poste.'))

    return redirect(f'/events/{pk}/volunteers/')


# ──────────────────────────────────────────────────────────────────────────────
# Photo Gallery
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def photo_gallery(request, pk):
    """View photo gallery for an event."""
    event = get_object_or_404(Event, pk=pk)
    is_staff = _is_staff(request)

    if is_staff:
        photos = event.photos.all()
    else:
        photos = event.photos.filter(is_approved=True)

    form = EventPhotoForm()

    context = {
        'event': event,
        'photos': photos,
        'form': form,
        'page_title': f'Photos - {event.title}',
        'is_staff': is_staff,
    }
    return render(request, 'events/photo_gallery.html', context)


@login_required
def photo_upload(request, pk):
    """Upload a photo to an event."""
    event = get_object_or_404(Event, pk=pk)

    if request.method == 'POST':
        form = EventPhotoForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            photo.event = event
            if hasattr(request.user, 'member_profile'):
                photo.uploaded_by = request.user.member_profile
            # Auto-approve for staff
            if _is_staff(request):
                photo.is_approved = True
            photo.save()
            messages.success(request, _('Photo téléversée avec succès.'))
        else:
            messages.error(request, _('Erreur lors du téléversement.'))

    return redirect(f'/events/{pk}/photos/')


@login_required
def photo_approve(request, pk, photo_pk):
    """Approve a photo (staff only)."""
    denied = _require_staff(request)
    if denied:
        return denied

    photo = get_object_or_404(EventPhoto, pk=photo_pk, event_id=pk)
    if request.method == 'POST':
        photo.is_approved = True
        photo.save(update_fields=['is_approved', 'updated_at'])
        messages.success(request, _('Photo approuvée.'))

    return redirect(f'/events/{pk}/photos/')


# ──────────────────────────────────────────────────────────────────────────────
# Surveys
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def survey_builder(request, pk):
    """Create/edit a survey for an event (staff only)."""
    denied = _require_staff(request)
    if denied:
        return denied

    event = get_object_or_404(Event, pk=pk)
    survey = event.surveys.first()

    if request.method == 'POST':
        if survey:
            form = EventSurveyForm(request.POST, instance=survey)
        else:
            form = EventSurveyForm(request.POST)
        if form.is_valid():
            s = form.save(commit=False)
            s.event = event
            s.save()
            messages.success(request, _('Sondage enregistré.'))
            return redirect(f'/events/{pk}/survey/')
    else:
        if survey:
            form = EventSurveyForm(instance=survey)
        else:
            form = EventSurveyForm(initial={'event': event})

    context = {
        'event': event,
        'survey': survey,
        'form': form,
        'page_title': f'Sondage - {event.title}',
    }
    return render(request, 'events/survey_builder.html', context)


@login_required
def survey_respond(request, pk, survey_pk):
    """Submit a survey response."""
    event = get_object_or_404(Event, pk=pk)
    survey = get_object_or_404(EventSurvey, pk=survey_pk, event=event)

    if not hasattr(request.user, 'member_profile'):
        messages.error(request, _("Profil membre requis."))
        return redirect(f'/events/{pk}/')

    member = request.user.member_profile

    if request.method == 'POST':
        answers = {}
        for key, value in request.POST.items():
            if key.startswith('q_'):
                answers[key] = value
        SurveyResponse.objects.update_or_create(
            survey=survey, member=member,
            defaults={'answers_json': answers},
        )
        messages.success(request, _('Merci pour votre réponse.'))
        return redirect(f'/events/{pk}/')

    context = {
        'event': event,
        'survey': survey,
        'page_title': f'Répondre - {survey.title}',
    }
    return render(request, 'events/survey_respond.html', context)


@login_required
def survey_results(request, pk, survey_pk):
    """View survey results (staff only)."""
    denied = _require_staff(request)
    if denied:
        return denied

    event = get_object_or_404(Event, pk=pk)
    survey = get_object_or_404(EventSurvey, pk=survey_pk, event=event)
    responses = survey.responses.all().select_related('member')

    context = {
        'event': event,
        'survey': survey,
        'responses': responses,
        'response_count': responses.count(),
        'page_title': f'Résultats - {survey.title}',
    }
    return render(request, 'events/survey_results.html', context)
