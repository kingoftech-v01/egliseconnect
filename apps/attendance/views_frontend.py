"""Frontend views for attendance check-in system."""
import json
from datetime import datetime, timedelta

from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from apps.core.constants import Roles, CheckInMethod, AttendanceSessionType
from .models import (
    MemberQRCode, AttendanceSession, AttendanceRecord, AbsenceAlert,
    ChildCheckIn, KioskConfig, NFCTag, AttendanceStreak,
    GeoFence, VisitorInfo,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Original Views
# ═══════════════════════════════════════════════════════════════════════════════

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

        # Update attendance streak
        _update_member_streak(qr.member, session.date)

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
@require_POST
def process_checkin_ajax(request):
    """Process QR check-in via AJAX, return JSON for continuous scanning."""
    if not hasattr(request.user, 'member_profile'):
        return JsonResponse({'status': 'error', 'message': 'Profil requis.'}, status=403)
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR, Roles.GROUP_LEADER]:
        return JsonResponse({'status': 'error', 'message': 'Accès refusé.'}, status=403)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = request.POST

    qr_code = data.get('qr_code', '').strip()
    session_id = data.get('session_id', '')

    if not qr_code or not session_id:
        return JsonResponse({'status': 'error', 'message': 'Code QR ou session manquant.'})

    try:
        qr = MemberQRCode.objects.select_related('member').get(code=qr_code)
    except MemberQRCode.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Code QR invalide.'})

    if not qr.is_valid:
        return JsonResponse({'status': 'error', 'message': 'Code QR expiré.'})

    try:
        session = AttendanceSession.objects.get(pk=session_id)
    except AttendanceSession.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Session introuvable.'})

    if not session.is_open:
        return JsonResponse({'status': 'error', 'message': 'Cette session est fermée.'})

    record, created = AttendanceRecord.objects.get_or_create(
        session=session,
        member=qr.member,
        defaults={
            'checked_in_by': request.user.member_profile,
            'method': CheckInMethod.QR_SCAN,
        }
    )

    if created:
        _update_member_streak(qr.member, session.date)
        if session.scheduled_lesson:
            from apps.onboarding.services import OnboardingService
            OnboardingService.mark_lesson_attended(
                session.scheduled_lesson,
                request.user.member_profile
            )
        return JsonResponse({
            'status': 'success',
            'member_name': qr.member.full_name,
            'message': f'{qr.member.full_name} enregistré(e) avec succès!',
            'checked_in_at': timezone.now().strftime('%H:%M'),
        })
    else:
        return JsonResponse({
            'status': 'duplicate',
            'member_name': qr.member.full_name,
            'message': f'{qr.member.full_name} est déjà enregistré(e).',
        })


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
    ninety_days_ago = timezone.now().date() - timedelta(days=90)
    total_sessions_90d = AttendanceSession.objects.filter(
        date__gte=ninety_days_ago
    ).count()
    attended_90d = records_qs.filter(
        session__date__gte=ninety_days_ago
    ).count()
    attendance_rate = round((attended_90d / total_sessions_90d * 100), 1) if total_sessions_90d > 0 else 0

    # Streak data (item 22)
    from .services import EngagementScoringService
    streak_data = EngagementScoringService.get_attendance_streak(member)

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
        'current_streak': streak_data['current_streak'],
        'longest_streak': streak_data['longest_streak'],
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

    from apps.events.models import Event
    events = Event.objects.filter(is_published=True, is_cancelled=False).order_by('-start_datetime')[:50]

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

        # Item 58: Link session to existing event
        event_id = request.POST.get('event_id', '')
        if event_id:
            try:
                session.event = Event.objects.get(pk=event_id)
            except Event.DoesNotExist:
                pass
        else:
            session.event = None

        session.save()
        messages.success(request, _('Session modifiée.'))
        return redirect('/attendance/sessions/' + str(pk) + '/')

    context = {
        'session': session,
        'session_types': AttendanceSessionType.CHOICES,
        'events': events,
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
                    _update_member_streak(member, session.date)
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


# ═══════════════════════════════════════════════════════════════════════════════
# P1: Child Check-In/Check-Out (items 1-6)
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def child_checkin(request):
    """Check in a child to a session."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR, Roles.GROUP_LEADER]:
        messages.error(request, _('Accès refusé.'))
        return redirect('/')

    sessions = AttendanceSession.objects.filter(
        date=timezone.now().date(),
        is_open=True,
    )

    if request.method == 'POST':
        child_id = request.POST.get('child_id', '')
        session_id = request.POST.get('session_id', '')
        parent_member_id = request.POST.get('parent_member_id', '')

        if child_id and session_id and parent_member_id:
            from apps.members.models import Child, Member
            try:
                child = Child.objects.get(pk=child_id)
                session = AttendanceSession.objects.get(pk=session_id, is_open=True)
                parent = Member.objects.get(pk=parent_member_id)

                # Check for existing check-in
                existing = ChildCheckIn.objects.filter(
                    child=child,
                    session=session,
                    check_out_time__isnull=True,
                ).first()

                if existing:
                    messages.warning(request, _('%(name)s est déjà enregistré(e).') % {'name': child.full_name})
                else:
                    checkin = ChildCheckIn.objects.create(
                        child=child,
                        parent_member=parent,
                        session=session,
                    )
                    messages.success(
                        request,
                        _('%(name)s enregistré(e). Code de sécurité: %(code)s') % {
                            'name': child.full_name,
                            'code': checkin.security_code,
                        }
                    )
                    return redirect('/attendance/child/receipt/' + str(checkin.pk) + '/')
            except (Child.DoesNotExist, AttendanceSession.DoesNotExist, Member.DoesNotExist):
                messages.error(request, _('Enfant, session ou parent introuvable.'))

    # Get families with children
    from apps.members.models import Child
    children = Child.objects.filter(is_active=True).select_related('family').order_by('last_name')

    from apps.members.models import Member
    members = Member.objects.filter(is_active=True).order_by('last_name')

    context = {
        'sessions': sessions,
        'children': children,
        'members': members,
        'page_title': _('Enregistrement enfant'),
    }
    return render(request, 'attendance/child_checkin.html', context)


@login_required
def child_checkin_receipt(request, pk):
    """Display receipt with security code after child check-in."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')

    checkin = get_object_or_404(ChildCheckIn, pk=pk)
    child = checkin.child

    context = {
        'checkin': checkin,
        'child': child,
        'has_allergies': bool(child.allergies),
        'has_medical_notes': bool(child.medical_notes),
        'page_title': _('Reçu - Enregistrement enfant'),
    }
    return render(request, 'attendance/child_receipt.html', context)


@login_required
def child_checkout(request):
    """Check out a child using security code."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')

    if request.method == 'POST':
        security_code = request.POST.get('security_code', '').strip()

        if not security_code:
            messages.error(request, _('Code de sécurité requis.'))
            return render(request, 'attendance/child_checkout.html', {
                'page_title': _('Retrait enfant'),
            })

        try:
            checkin = ChildCheckIn.objects.select_related('child', 'parent_member').get(
                security_code=security_code,
                check_out_time__isnull=True,
            )
            checkin.check_out_time = timezone.now()
            checkin.checked_out_by = request.user.member_profile
            checkin.save()
            messages.success(
                request,
                _('%(name)s a été retiré(e) avec succès.') % {'name': checkin.child.full_name}
            )
            return redirect('/attendance/child/checkin/')
        except ChildCheckIn.DoesNotExist:
            messages.error(request, _('Code de sécurité invalide ou enfant déjà retiré.'))

    context = {
        'page_title': _('Retrait enfant'),
    }
    return render(request, 'attendance/child_checkout.html', context)


@login_required
def child_checkin_history(request):
    """View child check-in/check-out history."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Accès refusé.'))
        return redirect('/')

    checkins = ChildCheckIn.objects.select_related(
        'child', 'parent_member', 'session'
    ).order_by('-check_in_time')

    paginator = Paginator(checkins, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'checkins': page_obj,
        'page_title': _('Historique enfants'),
    }
    return render(request, 'attendance/child_history.html', context)


# ═══════════════════════════════════════════════════════════════════════════════
# P1: Kiosk Self-Check-In (items 7-13)
# ═══════════════════════════════════════════════════════════════════════════════

def kiosk_home(request, kiosk_id):
    """Kiosk home screen - standalone template, no base.html."""
    kiosk = get_object_or_404(KioskConfig, pk=kiosk_id, is_active=True)

    sessions = AttendanceSession.objects.filter(
        date=timezone.now().date(),
        is_open=True,
    )

    context = {
        'kiosk': kiosk,
        'sessions': sessions,
    }
    return render(request, 'attendance/kiosk_home.html', context)


def kiosk_search(request, kiosk_id):
    """AJAX endpoint: search members by name for kiosk check-in."""
    kiosk = get_object_or_404(KioskConfig, pk=kiosk_id, is_active=True)

    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'results': []})

    from apps.members.models import Member
    members = Member.objects.filter(
        is_active=True,
    ).filter(
        models_q_name_search(query)
    ).order_by('last_name', 'first_name')[:10]

    results = []
    for m in members:
        results.append({
            'id': str(m.pk),
            'full_name': m.full_name,
            'member_number': m.member_number,
            'photo_url': m.photo.url if m.photo else None,
        })

    return JsonResponse({'results': results})


def kiosk_checkin(request, kiosk_id):
    """Process a check-in from the kiosk."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    kiosk = get_object_or_404(KioskConfig, pk=kiosk_id, is_active=True)

    member_id = request.POST.get('member_id', '')
    qr_code = request.POST.get('qr_code', '')
    session_id = request.POST.get('session_id', '') or str(kiosk.session_id or '')

    if not session_id:
        return JsonResponse({'error': 'Aucune session active'}, status=400)

    try:
        session = AttendanceSession.objects.get(pk=session_id, is_open=True)
    except AttendanceSession.DoesNotExist:
        return JsonResponse({'error': 'Session invalide ou fermée'}, status=400)

    member = None

    if member_id:
        from apps.members.models import Member
        try:
            member = Member.objects.get(pk=member_id, is_active=True)
        except Member.DoesNotExist:
            return JsonResponse({'error': 'Membre introuvable'}, status=400)
    elif qr_code:
        try:
            qr = MemberQRCode.objects.select_related('member').get(code=qr_code)
            if not qr.is_valid:
                return JsonResponse({'error': 'Code QR expiré'}, status=400)
            member = qr.member
        except MemberQRCode.DoesNotExist:
            return JsonResponse({'error': 'Code QR invalide'}, status=400)

    if not member:
        return JsonResponse({'error': 'Membre ou code QR requis'}, status=400)

    record, created = AttendanceRecord.objects.get_or_create(
        session=session,
        member=member,
        defaults={
            'method': CheckInMethod.KIOSK,
        }
    )

    if created:
        _update_member_streak(member, session.date)
        return JsonResponse({
            'success': True,
            'member_name': member.full_name,
            'member_photo': member.photo.url if member.photo else None,
            'message': f'{member.full_name} enregistré(e)',
        })
    else:
        return JsonResponse({
            'warning': True,
            'member_name': member.full_name,
            'message': f'{member.full_name} est déjà enregistré(e)',
        })


def kiosk_family_checkin(request, kiosk_id):
    """Check in entire family at kiosk."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    kiosk = get_object_or_404(KioskConfig, pk=kiosk_id, is_active=True)

    family_id = request.POST.get('family_id', '')
    session_id = request.POST.get('session_id', '') or str(kiosk.session_id or '')
    member_ids_raw = request.POST.getlist('member_ids', [])

    if not session_id:
        return JsonResponse({'error': 'Aucune session active'}, status=400)

    try:
        session = AttendanceSession.objects.get(pk=session_id, is_open=True)
    except AttendanceSession.DoesNotExist:
        return JsonResponse({'error': 'Session invalide ou fermée'}, status=400)

    from apps.members.models import Family
    try:
        family = Family.objects.get(pk=family_id)
    except Family.DoesNotExist:
        return JsonResponse({'error': 'Famille introuvable'}, status=400)

    from .services import FamilyCheckInService

    if member_ids_raw:
        # Check in only selected members
        from apps.members.models import Member
        checked_in = []
        already_checked = []
        for mid in member_ids_raw:
            try:
                member = Member.objects.get(pk=mid, family=family, is_active=True)
                record, created = AttendanceRecord.objects.get_or_create(
                    session=session,
                    member=member,
                    defaults={'method': CheckInMethod.KIOSK}
                )
                if created:
                    _update_member_streak(member, session.date)
                    checked_in.append(member.full_name)
                else:
                    already_checked.append(member.full_name)
            except Member.DoesNotExist:
                pass
    else:
        # Check in all family members
        results = FamilyCheckInService.check_in_family(family, session)
        checked_in = [m.full_name for m, created in results if created]
        already_checked = [m.full_name for m, created in results if not created]
        for m, created in results:
            if created:
                _update_member_streak(m, session.date)

    return JsonResponse({
        'success': True,
        'checked_in': checked_in,
        'already_checked': already_checked,
        'family_name': family.name,
    })


def kiosk_family_search(request, kiosk_id):
    """AJAX endpoint: search families by name for kiosk check-in."""
    kiosk = get_object_or_404(KioskConfig, pk=kiosk_id, is_active=True)

    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'results': []})

    from apps.members.models import Family
    families = Family.objects.filter(
        is_active=True,
        name__icontains=query,
    ).order_by('name')[:10]

    results = []
    for f in families:
        members = list(f.members.filter(is_active=True).values_list('first_name', 'last_name', 'id'))
        results.append({
            'id': str(f.pk),
            'name': f.name,
            'members': [
                {'id': str(m[2]), 'name': f'{m[0]} {m[1]}'}
                for m in members
            ],
        })

    return JsonResponse({'results': results})


@login_required
def kiosk_admin(request, kiosk_id):
    """Admin configuration page for a kiosk (requires PIN)."""
    kiosk = get_object_or_404(KioskConfig, pk=kiosk_id)

    # Check PIN via POST
    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'verify_pin':
            pin = request.POST.get('admin_pin', '')
            if pin == kiosk.admin_pin:
                request.session[f'kiosk_admin_{kiosk_id}'] = True
            else:
                messages.error(request, _('PIN invalide.'))
                return render(request, 'attendance/kiosk_pin.html', {
                    'kiosk': kiosk,
                })

        elif request.session.get(f'kiosk_admin_{kiosk_id}'):
            if action == 'update_session':
                session_id = request.POST.get('session_id', '')
                if session_id:
                    try:
                        kiosk.session = AttendanceSession.objects.get(pk=session_id)
                    except AttendanceSession.DoesNotExist:
                        kiosk.session = None
                else:
                    kiosk.session = None
                kiosk.save()
                messages.success(request, _('Session mise à jour.'))

    if not request.session.get(f'kiosk_admin_{kiosk_id}'):
        return render(request, 'attendance/kiosk_pin.html', {
            'kiosk': kiosk,
        })

    sessions = AttendanceSession.objects.filter(
        date=timezone.now().date(),
        is_open=True,
    )

    context = {
        'kiosk': kiosk,
        'sessions': sessions,
        'page_title': _('Administration kiosque'),
    }
    return render(request, 'attendance/kiosk_admin.html', context)


# ═══════════════════════════════════════════════════════════════════════════════
# P1: Attendance Analytics (items 14-19)
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def analytics_dashboard(request):
    """Analytics dashboard with Chart.js integration."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Accès refusé.'))
        return redirect('/')

    from .services import AttendanceAnalyticsService

    # Trends data
    weekly_trends = AttendanceAnalyticsService.get_attendance_trends('weekly', 12)
    monthly_trends = AttendanceAnalyticsService.get_attendance_trends('monthly', 52)

    # Average by type
    avg_by_type = AttendanceAnalyticsService.get_average_attendance_by_type()

    # Growth indicators
    growth = AttendanceAnalyticsService.get_growth_indicators()

    # Seasonal trends
    seasonal = AttendanceAnalyticsService.get_seasonal_trends()

    # Duration report
    duration_report = AttendanceAnalyticsService.get_session_duration_report()

    # Prepare Chart.js data
    trend_labels = [t['period'].strftime('%d/%m') for t in weekly_trends]
    trend_data = [t['count'] for t in weekly_trends]

    seasonal_labels = [
        ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun',
         'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc'][s['month'] - 1]
        for s in seasonal
    ]
    seasonal_data = [s['avg_attendance'] for s in seasonal]

    type_labels = []
    type_data = []
    type_display = dict(AttendanceSessionType.CHOICES)
    for stype, avg in avg_by_type.items():
        type_labels.append(str(type_display.get(stype, stype)))
        type_data.append(avg)

    context = {
        'growth': growth,
        'duration_report': duration_report,
        'trend_labels': json.dumps(trend_labels),
        'trend_data': json.dumps(trend_data),
        'seasonal_labels': json.dumps(seasonal_labels),
        'seasonal_data': json.dumps(seasonal_data),
        'type_labels': json.dumps(type_labels),
        'type_data': json.dumps(type_data),
        'page_title': _('Analytiques de présence'),
    }
    return render(request, 'attendance/analytics_dashboard.html', context)


@login_required
def analytics_trends_api(request):
    """JSON endpoint for attendance trends chart data."""
    if not hasattr(request.user, 'member_profile'):
        return JsonResponse({'error': 'No profile'}, status=403)
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        return JsonResponse({'error': 'Access denied'}, status=403)

    from .services import AttendanceAnalyticsService

    period = request.GET.get('period', 'weekly')
    weeks = int(request.GET.get('weeks', 12))

    trends = AttendanceAnalyticsService.get_attendance_trends(period, weeks)

    return JsonResponse({
        'labels': [t['period'].strftime('%Y-%m-%d') for t in trends],
        'data': [t['count'] for t in trends],
    })


@login_required
def member_attendance_rate_api(request, member_id):
    """JSON endpoint for a member's attendance rate chart data."""
    if not hasattr(request.user, 'member_profile'):
        return JsonResponse({'error': 'No profile'}, status=403)
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        return JsonResponse({'error': 'Access denied'}, status=403)

    from apps.members.models import Member
    from .services import AttendanceAnalyticsService

    member = get_object_or_404(Member, pk=member_id)
    days = int(request.GET.get('days', 90))
    stats = AttendanceAnalyticsService.get_member_attendance_rate(member, days)

    return JsonResponse(stats)


# ═══════════════════════════════════════════════════════════════════════════════
# P1: Frontend Refinements (items 20-24)
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def member_search_api(request):
    """AJAX endpoint: search members by name for scanner page manual search."""
    if not hasattr(request.user, 'member_profile'):
        return JsonResponse({'error': 'No profile'}, status=403)
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR, Roles.GROUP_LEADER]:
        return JsonResponse({'error': 'Access denied'}, status=403)

    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'results': []})

    from apps.members.models import Member
    members = Member.objects.filter(
        is_active=True,
    ).filter(
        models_q_name_search(query)
    ).order_by('last_name', 'first_name')[:10]

    results = []
    for m in members:
        results.append({
            'id': str(m.pk),
            'full_name': m.full_name,
            'member_number': m.member_number,
            'photo_url': m.photo.url if m.photo else None,
        })

    return JsonResponse({'results': results})


# ═══════════════════════════════════════════════════════════════════════════════
# P2: Family Check-In (items 25-27)
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def family_checkin(request):
    """Household check-in flow."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR, Roles.GROUP_LEADER]:
        messages.error(request, _('Accès refusé.'))
        return redirect('/')

    sessions = AttendanceSession.objects.filter(
        date=timezone.now().date(),
        is_open=True,
    )

    if request.method == 'POST':
        family_id = request.POST.get('family_id', '')
        session_id = request.POST.get('session_id', '')
        member_ids = request.POST.getlist('member_ids')

        if family_id and session_id:
            from apps.members.models import Family, Member
            try:
                family = Family.objects.get(pk=family_id)
                session = AttendanceSession.objects.get(pk=session_id, is_open=True)

                checked_in_names = []
                for mid in member_ids:
                    try:
                        member = Member.objects.get(pk=mid, family=family)
                        record, created = AttendanceRecord.objects.get_or_create(
                            session=session,
                            member=member,
                            defaults={
                                'checked_in_by': request.user.member_profile,
                                'method': CheckInMethod.MANUAL,
                            }
                        )
                        if created:
                            checked_in_names.append(member.full_name)
                            _update_member_streak(member, session.date)
                    except Member.DoesNotExist:
                        pass

                if checked_in_names:
                    names_str = ', '.join(checked_in_names)
                    messages.success(
                        request,
                        _('Enregistré: %(names)s') % {'names': names_str}
                    )
                else:
                    messages.info(request, _('Aucun nouveau membre enregistré.'))

            except (Family.DoesNotExist, AttendanceSession.DoesNotExist):
                messages.error(request, _('Famille ou session introuvable.'))

    from apps.members.models import Family
    families = Family.objects.filter(is_active=True).order_by('name')

    context = {
        'sessions': sessions,
        'families': families,
        'page_title': _('Enregistrement famille'),
    }
    return render(request, 'attendance/family_checkin.html', context)


@login_required
def family_attendance_summary(request, family_id):
    """View family attendance summary."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Accès refusé.'))
        return redirect('/')

    from apps.members.models import Family
    from .services import FamilyCheckInService

    family = get_object_or_404(Family, pk=family_id)
    summary = FamilyCheckInService.get_family_attendance_summary(family)

    context = {
        'family': family,
        'summary': summary,
        'page_title': _('Présence famille: %(name)s') % {'name': family.name},
    }
    return render(request, 'attendance/family_summary.html', context)


# ═══════════════════════════════════════════════════════════════════════════════
# P2: NFC/Tap Check-In (items 28-32)
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def nfc_register(request):
    """Register a new NFC tag for a member (admin only)."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Accès refusé.'))
        return redirect('/')

    if request.method == 'POST':
        member_id = request.POST.get('member_id', '')
        tag_id = request.POST.get('tag_id', '')

        if member_id and tag_id:
            from apps.members.models import Member
            try:
                member = Member.objects.get(pk=member_id)
                # Check if member already has an NFC tag
                existing = NFCTag.objects.filter(member=member).first()
                if existing:
                    existing.tag_id = tag_id
                    existing.save()
                    messages.success(request, _('Tag NFC mis à jour pour %(name)s.') % {'name': member.full_name})
                else:
                    NFCTag.objects.create(member=member, tag_id=tag_id)
                    messages.success(request, _('Tag NFC enregistré pour %(name)s.') % {'name': member.full_name})
            except Member.DoesNotExist:
                messages.error(request, _('Membre introuvable.'))

    from apps.members.models import Member
    members = Member.objects.filter(is_active=True).order_by('last_name')
    nfc_tags = NFCTag.objects.select_related('member').order_by('-registered_at')

    context = {
        'members': members,
        'nfc_tags': nfc_tags,
        'page_title': _('Tags NFC'),
    }
    return render(request, 'attendance/nfc_register.html', context)


@login_required
def nfc_reader_config(request):
    """NFC reader configuration page."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Accès refusé.'))
        return redirect('/')

    sessions = AttendanceSession.objects.filter(
        date=timezone.now().date(),
        is_open=True,
    )

    context = {
        'sessions': sessions,
        'page_title': _('Lecteur NFC'),
    }
    return render(request, 'attendance/nfc_reader.html', context)


# ═══════════════════════════════════════════════════════════════════════════════
# P2: Check-Out Time Tracking (items 37-40)
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def checkout_member(request, pk):
    """Check out a member from a session."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR, Roles.GROUP_LEADER]:
        messages.error(request, _('Accès refusé.'))
        return redirect('/')

    if request.method == 'POST':
        record = get_object_or_404(AttendanceRecord, pk=pk)
        if record.checked_out_at is None:
            record.checked_out_at = timezone.now()
            record.save()
            messages.success(
                request,
                _('%(name)s a été marqué(e) comme sorti(e).') % {'name': record.member.full_name}
            )
        else:
            messages.warning(request, _('Ce membre est déjà marqué comme sorti.'))
        return redirect('/attendance/sessions/' + str(record.session.pk) + '/')

    return redirect('/attendance/sessions/')


# ═══════════════════════════════════════════════════════════════════════════════
# P3: Geo-Fenced Check-In (items 43-46)
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def geo_checkin(request):
    """GPS-based check-in endpoint."""
    if not hasattr(request.user, 'member_profile'):
        return JsonResponse({'error': 'No profile'}, status=403)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            lat = float(data.get('latitude', 0))
            lng = float(data.get('longitude', 0))
            session_id = data.get('session_id', '')
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'error': 'Données invalides'}, status=400)

        if not session_id:
            return JsonResponse({'error': 'Session requise'}, status=400)

        # Find matching geo-fence
        fences = GeoFence.objects.filter(is_active=True)
        within_fence = False
        for fence in fences:
            if fence.is_within_fence(lat, lng):
                within_fence = True
                break

        if not within_fence:
            return JsonResponse({
                'error': 'Vous n\'êtes pas dans la zone de check-in'
            }, status=400)

        try:
            session = AttendanceSession.objects.get(pk=session_id, is_open=True)
        except AttendanceSession.DoesNotExist:
            return JsonResponse({'error': 'Session invalide'}, status=400)

        member = request.user.member_profile
        record, created = AttendanceRecord.objects.get_or_create(
            session=session,
            member=member,
            defaults={
                'method': CheckInMethod.GEO,
            }
        )

        if created:
            _update_member_streak(member, session.date)
            return JsonResponse({
                'success': True,
                'message': 'Présence enregistrée par géolocalisation',
            })
        else:
            return JsonResponse({
                'warning': True,
                'message': 'Déjà enregistré(e)',
            })

    return JsonResponse({'error': 'POST required'}, status=405)


# ═══════════════════════════════════════════════════════════════════════════════
# P3: Attendance Prediction (items 47-49)
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def prediction_dashboard(request):
    """Attendance prediction and resource planning view."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Accès refusé.'))
        return redirect('/')

    from .services import AttendancePredictionService

    predictions = {}
    recommendations = {}
    comparisons = {}

    for stype, label in AttendanceSessionType.CHOICES:
        predictions[stype] = AttendancePredictionService.predict_attendance(stype)
        recommendations[stype] = AttendancePredictionService.get_resource_recommendations(stype)
        comparisons[stype] = AttendancePredictionService.get_actual_vs_predicted(stype)

    type_display = dict(AttendanceSessionType.CHOICES)

    context = {
        'predictions': predictions,
        'recommendations': recommendations,
        'type_display': type_display,
        'page_title': _('Prédictions de présence'),
    }
    return render(request, 'attendance/prediction_dashboard.html', context)


# ═══════════════════════════════════════════════════════════════════════════════
# P3: Visitor Follow-Up (items 50-54)
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def visitor_list(request):
    """List all visitors with follow-up status."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Accès refusé.'))
        return redirect('/')

    visitors = VisitorInfo.objects.select_related('session', 'follow_up_assigned_to').order_by('-created_at')

    paginator = Paginator(visitors, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'visitors': page_obj,
        'page_title': _('Visiteurs'),
    }
    return render(request, 'attendance/visitor_list.html', context)


@login_required
def visitor_create(request):
    """Capture visitor information."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR, Roles.GROUP_LEADER]:
        messages.error(request, _('Accès refusé.'))
        return redirect('/')

    from .forms import VisitorInfoForm

    if request.method == 'POST':
        form = VisitorInfoForm(request.POST)
        if form.is_valid():
            visitor = form.save()
            messages.success(request, _('Visiteur %(name)s enregistré.') % {'name': visitor.name})
            return redirect('/attendance/visitors/')
    else:
        # Pre-fill session if today's session exists
        today_session = AttendanceSession.objects.filter(
            date=timezone.now().date(), is_open=True
        ).first()
        form = VisitorInfoForm(initial={'session': today_session})

    context = {
        'form': form,
        'page_title': _('Nouveau visiteur'),
    }
    return render(request, 'attendance/visitor_form.html', context)


@login_required
def visitor_followup(request, pk):
    """Mark visitor follow-up as completed."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Accès refusé.'))
        return redirect('/')

    visitor = get_object_or_404(VisitorInfo, pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'assign':
            assignee_id = request.POST.get('assignee_id', '')
            if assignee_id:
                from apps.members.models import Member
                try:
                    assignee = Member.objects.get(pk=assignee_id)
                    visitor.follow_up_assigned_to = assignee
                    visitor.save()
                    messages.success(request, _('Suivi assigné à %(name)s.') % {'name': assignee.full_name})
                except Member.DoesNotExist:
                    messages.error(request, _('Membre introuvable.'))
        elif action == 'complete':
            visitor.follow_up_completed = True
            visitor.follow_up_completed_at = timezone.now()
            visitor.save()
            messages.success(request, _('Suivi marqué comme complété.'))
        elif action == 'notes':
            visitor.notes = request.POST.get('notes', '')
            visitor.save()
            messages.success(request, _('Notes mises à jour.'))

    return redirect('/attendance/visitors/')


# ═══════════════════════════════════════════════════════════════════════════════
# P3: Small Fixes (items 55-60)
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def absence_alert_list(request):
    """List absence alerts with acknowledgment UI."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Accès refusé.'))
        return redirect('/')

    alerts = AbsenceAlert.objects.select_related('member', 'acknowledged_by').order_by(
        'acknowledged_by',  # unacknowledged first (NULL)
        '-consecutive_absences',
    )

    context = {
        'alerts': alerts,
        'page_title': _("Alertes d'absence"),
    }
    return render(request, 'attendance/absence_alert_list.html', context)


@login_required
@require_POST
def acknowledge_alert(request, pk):
    """Acknowledge an absence alert."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Accès refusé.'))
        return redirect('/')

    alert = get_object_or_404(AbsenceAlert, pk=pk)
    if not alert.acknowledged_by:
        alert.acknowledged_by = request.user.member_profile
        alert.acknowledged_at = timezone.now()
        notes = request.POST.get('notes', '')
        if notes:
            alert.notes = notes
        alert.save()
        messages.success(request, _('Alerte reconnue.'))

    return redirect('/attendance/alerts/')


# ═══════════════════════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════════════════════

def _update_member_streak(member, attendance_date):
    """Update attendance streak for a member after check-in."""
    streak, _ = AttendanceStreak.objects.get_or_create(member=member)
    streak.update_streak(attendance_date)


def models_q_name_search(query):
    """Build Q object for member name search."""
    from django.db.models import Q
    parts = query.split()
    q = Q()
    for part in parts:
        q &= (Q(first_name__icontains=part) | Q(last_name__icontains=part))
    return q
