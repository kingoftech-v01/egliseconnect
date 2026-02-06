"""Frontend views for attendance check-in system."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
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
        'sessions': sessions,
        'page_title': _('Scanner QR'),
    }
    return render(request, 'attendance/scanner.html', context)


@login_required
def create_session(request):
    """Create a new attendance session."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Accès refusé.'))
        return redirect('/')

    if request.method == 'POST':
        name = request.POST.get('name', '')
        session_type = request.POST.get('session_type', AttendanceSessionType.WORSHIP)

        if name:
            session = AttendanceSession.objects.create(
                name=name,
                session_type=session_type,
                date=timezone.now().date(),
                start_time=timezone.now().time(),
                opened_by=request.user.member_profile,
            )
            messages.success(request, _('Session créée.'))
            return redirect('frontend:attendance:scanner')

    context = {
        'session_types': AttendanceSessionType.CHOICES,
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
    """List all attendance sessions."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Accès refusé.'))
        return redirect('/')

    sessions = AttendanceSession.objects.all().order_by('-date')

    context = {
        'sessions': sessions,
        'page_title': _('Sessions de présence'),
    }
    return render(request, 'attendance/session_list.html', context)


@login_required
def session_detail(request, pk):
    """Detail of an attendance session with records."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Accès refusé.'))
        return redirect('/')

    session = get_object_or_404(AttendanceSession, pk=pk)
    records = session.records.select_related('member').order_by('-checked_in_at')

    context = {
        'session': session,
        'records': records,
        'page_title': session.name,
    }
    return render(request, 'attendance/session_detail.html', context)


@login_required
def my_history(request):
    """Member's own attendance history."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('frontend:members:member_create')

    member = request.user.member_profile
    records = AttendanceRecord.objects.filter(
        member=member
    ).select_related('session').order_by('-checked_in_at')

    context = {
        'records': records,
        'member': member,
        'page_title': _('Mon historique de présence'),
    }
    return render(request, 'attendance/my_history.html', context)
