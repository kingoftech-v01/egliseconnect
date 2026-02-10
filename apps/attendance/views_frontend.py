"""Frontend views for attendance check-in system."""
from datetime import datetime
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.constants import Roles, CheckInMethod, AttendanceSessionType
from .models import MemberQRCode, AttendanceSession, AttendanceRecord


@login_required
def my_qr(request):
    """Display the member's personal QR code."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('frontend:members:member_create')

    member = request.user.member_profile

    if not member.can_use_qr:
        messages.error(request, _('Votre QR code n\'est pas disponible avec votre statut actuel.'))
        return redirect('frontend:onboarding:dashboard')

    qr, created = MemberQRCode.objects.get_or_create(member=member)

    # Regenerate if expired
    if not qr.is_valid:
        qr.regenerate()

    context = {
        'qr': qr,
        'member': member,
        'page_title': _('Mon code QR'),
    }
    return render(request, 'attendance/my_qr.html', context)


@login_required
def scanner(request):
    """QR code scanner page for admins/staff."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR, Roles.GROUP_LEADER]:
        messages.error(request, _('Accès refusé.'))
        return redirect('/')

    # Get or create today's sessions
    sessions = AttendanceSession.objects.filter(
        date=timezone.now().date(),
        is_open=True,
    )

    context = {
        'active_sessions': sessions,
        'sessions': sessions,
        'page_title': _('Scanner QR'),
    }
    return render(request, 'attendance/scanner.html', context)


@login_required
def create_session(request):
    """Create a new attendance session with optional event link."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Accès refusé.'))
        return redirect('/')

    from apps.events.models import Event
    events = Event.objects.filter(is_published=True, is_cancelled=False).order_by('-start_datetime')[:50]

    if request.method == 'POST':
        name = request.POST.get('name', '')
        session_type = request.POST.get('session_type', AttendanceSessionType.WORSHIP)

        if name:
            date_str = request.POST.get('date', '')
            start_time_str = request.POST.get('start_time', '')
            end_time_str = request.POST.get('end_time', '')

            # Parse date
            if date_str:
                session_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            else:
                session_date = timezone.now().date()

            # Validate date is not in the past
            if session_date < timezone.now().date():
                messages.error(request, _('La date ne peut pas être dans le passé.'))
                context = {
                    'session_types': AttendanceSessionType.CHOICES,
                    'events': events,
                    'page_title': _('Nouvelle session'),
                }
                return render(request, 'attendance/create_session.html', context)

            # Parse start_time
            if start_time_str:
                start_time = datetime.strptime(start_time_str, '%H:%M').time()
            else:
                start_time = timezone.now().time()

            # Parse end_time
            if end_time_str:
                end_time = datetime.strptime(end_time_str, '%H:%M').time()
            else:
                end_time = None

            duration = request.POST.get('duration_minutes', '')
            event_id = request.POST.get('event_id', '')
            linked_event = None
            if event_id:
                try:
                    linked_event = Event.objects.get(pk=event_id)
                except Event.DoesNotExist:
                    pass

            session = AttendanceSession.objects.create(
                name=name,
                session_type=session_type,
                date=session_date,
                start_time=start_time,
                end_time=end_time,
                duration_minutes=int(duration) if duration else None,
                event=linked_event,
                opened_by=request.user.member_profile,
            )
            messages.success(request, _('Session créée.'))
            return redirect('frontend:attendance:scanner')

    context = {
        'session_types': AttendanceSessionType.CHOICES,
        'events': events,
        'page_title': _('Nouvelle session'),
    }
    return render(request, 'attendance/create_session.html', context)

@login_required
def process_checkin(request):
    """Process a QR code scan (called from scanner page via POST)."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR, Roles.GROUP_LEADER]:
        messages.error(request, _('Accès refusé.'))
        return redirect('/')

    if request.method != 'POST':
        return redirect('frontend:attendance:scanner')

    qr_code = request.POST.get('qr_code', '').strip()
    session_id = request.POST.get('session_id', '')

    if not qr_code or not session_id:
        messages.error(request, _('Code QR ou session manquant.'))
        return redirect('frontend:attendance:scanner')

    # Validate QR code
    try:
        qr = MemberQRCode.objects.select_related('member').get(code=qr_code)
    except MemberQRCode.DoesNotExist:
        messages.error(request, _('Code QR invalide.'))
        return redirect('frontend:attendance:scanner')

    if not qr.is_valid:
        messages.error(request, _('Code QR expiré.'))
        return redirect('frontend:attendance:scanner')

    session = get_object_or_404(AttendanceSession, pk=session_id)

    if not session.is_open:
        messages.error(request, _('Cette session est fermée.'))
        return redirect('frontend:attendance:scanner')

    # Create attendance record
    record, created = AttendanceRecord.objects.get_or_create(
        session=session,
        member=qr.member,
        defaults={
            'checked_in_by': request.user.member_profile,
            'method': CheckInMethod.QR_SCAN,
        }
    )

    if created:
        messages.success(
            request,
            _('%(name)s enregistré(e) avec succès!') % {'name': qr.member.full_name}
        )

        # If this session is linked to a lesson, mark attendance
        if session.scheduled_lesson:
            from apps.onboarding.services import OnboardingService
            OnboardingService.mark_lesson_attended(
                session.scheduled_lesson,
                request.user.member_profile
            )
    else:
        messages.warning(
            request,
            _('%(name)s est déjà enregistré(e).') % {'name': qr.member.full_name}
        )

    return redirect('frontend:attendance:scanner')


@login_required
def session_list(request):
    """List all attendance sessions with filter by type and date range."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Accès refusé.'))
        return redirect('/')

    sessions_qs = AttendanceSession.objects.all().order_by('-date')

    # Filter by session type
    session_type = request.GET.get('session_type')
    if session_type:
        sessions_qs = sessions_qs.filter(session_type=session_type)

    # Filter by date range
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        sessions_qs = sessions_qs.filter(date__gte=date_from)
    if date_to:
        sessions_qs = sessions_qs.filter(date__lte=date_to)

    paginator = Paginator(sessions_qs, 25)
    page_number = request.GET.get('page')
    sessions = paginator.get_page(page_number)

    context = {
        'sessions': sessions,
        'session_types': AttendanceSessionType.CHOICES,
        'selected_type': session_type or '',
        'date_from': date_from or '',
        'date_to': date_to or '',
        'page_title': _('Sessions de présence'),
    }
    return render(request, 'attendance/session_list.html', context)


@login_required
def session_detail(request, pk):
    """Detail of an attendance session with records and CSV export."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Accès refusé.'))
        return redirect('/')

    session = get_object_or_404(AttendanceSession, pk=pk)
    records = session.records.select_related('member').order_by('-checked_in_at')

    # CSV export
    if request.GET.get('export') == 'csv':
        from apps.core.export import export_queryset_csv
        return export_queryset_csv(
            records,
            fields=[
                lambda r: r.member.full_name,
                lambda r: r.member.email,
                'method',
                lambda r: r.checked_in_at.strftime('%H:%M'),
            ],
            filename=f'presence_{session.name}_{session.date}',
            headers=['Membre', 'Email', 'Méthode', 'Heure'],
        )

    from apps.members.models import Member
    members = Member.objects.filter(role__in=['member', 'admin', 'pastor']).order_by('first_name')

    context = {
        'session': session,
        'attendance_records': records,
        'members': members,
        'page_title': session.name,
    }
    return render(request, 'attendance/session_detail.html', context)


@login_required
def my_history(request):
    """Member's own attendance history with statistics."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('frontend:members:member_create')

    member = request.user.member_profile
    records_qs = AttendanceRecord.objects.filter(
        member=member
    ).select_related('session').order_by('-checked_in_at')

    total_count = records_qs.count()

    # Statistics: total sessions in last 90 days vs attended
    from datetime import timedelta
    ninety_days_ago = timezone.now().date() - timedelta(days=90)
    total_sessions_90d = AttendanceSession.objects.filter(
        date__gte=ninety_days_ago
    ).count()
    attended_90d = records_qs.filter(
        session__date__gte=ninety_days_ago
    ).count()
    attendance_rate = round((attended_90d / total_sessions_90d * 100), 1) if total_sessions_90d > 0 else 0

    paginator = Paginator(records_qs, 25)
    page_number = request.GET.get('page')
    attendance_records = paginator.get_page(page_number)

    context = {
        'attendance_records': attendance_records,
        'total_count': total_count,
        'member': member,
        'total_sessions_90d': total_sessions_90d,
        'attended_90d': attended_90d,
        'attendance_rate': attendance_rate,
        'page_title': _('Mon historique de présence'),
    }
    return render(request, 'attendance/my_history.html', context)


@login_required
def edit_session(request, pk):
    """Edit an existing attendance session."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Accès refusé.'))
        return redirect('/')
    session = get_object_or_404(AttendanceSession, pk=pk)
    if request.method == 'POST':
        session.name = request.POST.get('name', session.name)
        session.session_type = request.POST.get('session_type', session.session_type)
        date_str = request.POST.get('date', '')
        if date_str:
            session.date = datetime.strptime(date_str, '%Y-%m-%d').date()
        start_time_str = request.POST.get('start_time', '')
        if start_time_str:
            session.start_time = datetime.strptime(start_time_str, '%H:%M').time()
        end_time_str = request.POST.get('end_time', '')
        if end_time_str:
            session.end_time = datetime.strptime(end_time_str, '%H:%M').time()
        else:
            session.end_time = None
        duration = request.POST.get('duration_minutes', '')
        session.duration_minutes = int(duration) if duration else None
        session.save()
        messages.success(request, _('Session modifiée.'))
        return redirect('/attendance/sessions/' + str(pk) + '/')
    context = {
        'session': session,
        'session_types': AttendanceSessionType.CHOICES,
        'page_title': _('Modifier la session'),
    }
    return render(request, 'attendance/edit_session.html', context)


@login_required
def toggle_session(request, pk):
    """Toggle a session open/closed."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Accès refusé.'))
        return redirect('/')
    if request.method == 'POST':
        session = get_object_or_404(AttendanceSession, pk=pk)
        session.is_open = not session.is_open
        session.save()
        status = _('ouverte') if session.is_open else _('fermée')
        messages.success(request, _('Session %(status)s.') % {'status': status})
    return redirect('/attendance/sessions/' + str(pk) + '/')


@login_required
def delete_session(request, pk):
    """Delete an attendance session."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Accès refusé.'))
        return redirect('/')
    session = get_object_or_404(AttendanceSession, pk=pk)
    if request.method == 'POST':
        session.delete()
        messages.success(request, _('Session supprimée.'))
        return redirect('/attendance/sessions/')
    context = {
        'session': session,
        'page_title': _('Supprimer la session'),
    }
    return render(request, 'attendance/delete_session.html', context)


@login_required
def add_manual_record(request, pk):
    """Add a manual attendance record to a session."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR, Roles.GROUP_LEADER]:
        messages.error(request, _('Accès refusé.'))
        return redirect('/')
    if request.method == 'POST':
        session = get_object_or_404(AttendanceSession, pk=pk)
        member_id = request.POST.get('member_id', '')
        if member_id:
            from apps.members.models import Member
            try:
                member = Member.objects.get(pk=member_id)
                record, created = AttendanceRecord.objects.get_or_create(
                    session=session,
                    member=member,
                    defaults={
                        'checked_in_by': request.user.member_profile,
                        'method': CheckInMethod.MANUAL,
                    }
                )
                if created:
                    messages.success(request, _('%(name)s ajouté(e).') % {'name': member.full_name})
                else:
                    messages.warning(request, _('%(name)s est déjà enregistré(e).') % {'name': member.full_name})
            except Member.DoesNotExist:
                messages.error(request, _('Membre introuvable.'))
    return redirect('/attendance/sessions/' + str(pk) + '/')


@login_required
def delete_record(request, pk):
    """Delete an attendance record."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Accès refusé.'))
        return redirect('/')
    if request.method == 'POST':
        record = get_object_or_404(AttendanceRecord, pk=pk)
        session_pk = record.session.pk
        record.delete()
        messages.success(request, _('Enregistrement supprimé.'))
        return redirect('/attendance/sessions/' + str(session_pk) + '/')
    return redirect('/attendance/sessions/')
