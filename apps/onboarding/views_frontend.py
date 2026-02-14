"""Frontend views for the onboarding process."""
import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from apps.core.constants import MembershipStatus, Roles, InterviewStatus, LessonStatus
from apps.members.models import Member
from .models import (
    TrainingCourse, MemberTraining, ScheduledLesson, Interview,
    InvitationCode, MentorAssignment, MentorCheckIn,
    OnboardingFormField, OnboardingFormResponse,
    WelcomeSequence, WelcomeStep,
    OnboardingDocument, DocumentSignature,
    VisitorFollowUp, OnboardingTrackModel,
    Achievement, MemberAchievement,
)
from .forms import (
    OnboardingProfileForm,
    AdminReviewForm,
    TrainingCourseForm,
    LessonForm,
    ScheduleLessonForm,
    ScheduleInterviewForm,
    InterviewCounterProposeForm,
    InterviewResultForm,
    InvitationCreateForm,
    InvitationAcceptForm,
    InvitationEditForm,
    MentorAssignmentForm,
    MentorCheckInForm,
    OnboardingFormFieldForm,
    WelcomeSequenceForm,
    WelcomeStepForm,
    OnboardingDocumentForm,
    DocumentSignatureForm,
    VisitorFollowUpForm,
    OnboardingTrackForm,
    AchievementForm,
    BulkPipelineActionForm,
)
from .services import OnboardingService


# ─── Helper: admin role check ─────────────────────────────────────────────────

def _is_admin_or_pastor(request):
    """Return True if user has admin/pastor role."""
    if not hasattr(request.user, 'member_profile'):
        return False
    return request.user.member_profile.role in [Roles.ADMIN, Roles.PASTOR]


# ─── Member-facing views ─────────────────────────────────────────────────────

@login_required
def dashboard(request):
    """Route to the correct dashboard based on membership status."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('frontend:members:member_create')

    member = request.user.member_profile

    # If already active, go to main dashboard
    if member.has_full_access:
        return redirect('frontend:reports:dashboard')

    status = member.membership_status
    context = {
        'member': member,
        'page_title': _('Mon parcours'),
        'whats_next': OnboardingService.get_whats_next(member),
        'estimated_completion': OnboardingService.estimate_completion_date(member),
    }

    # Add achievements
    context['achievements'] = MemberAchievement.objects.filter(
        member=member
    ).select_related('achievement')[:5]

    # Add mentor info
    mentor_assignment = MentorAssignment.objects.filter(
        new_member=member, status='active', is_active=True
    ).select_related('mentor').first()
    context['mentor_assignment'] = mentor_assignment

    if status in [MembershipStatus.REGISTERED, MembershipStatus.FORM_PENDING]:
        context['days_remaining'] = member.days_remaining_for_form
        return render(request, 'onboarding/status_registered.html', context)

    elif status == MembershipStatus.FORM_SUBMITTED:
        return render(request, 'onboarding/status_submitted.html', context)

    elif status == MembershipStatus.IN_REVIEW:
        return render(request, 'onboarding/status_submitted.html', context)

    elif status in [MembershipStatus.APPROVED, MembershipStatus.IN_TRAINING]:
        training = MemberTraining.objects.filter(
            member=member, is_active=True
        ).select_related('course').first()
        if training:
            context['training'] = training
            context['course'] = training.course
            context['scheduled_lessons'] = training.scheduled_lessons.select_related(
                'lesson'
            ).order_by('lesson__order')
            context['completed_lessons'] = training.completed_count
            context['total_lessons'] = training.total_count
            total = training.total_count
            completed = training.completed_count
            context['progress_percent'] = int((completed / total) * 100) if total > 0 else 0
        return render(request, 'onboarding/status_in_training.html', context)

    elif status == MembershipStatus.INTERVIEW_SCHEDULED:
        interview = Interview.objects.filter(
            member=member
        ).order_by('-created_at').first()
        context['interview'] = interview
        return render(request, 'onboarding/status_interview.html', context)

    elif status in [MembershipStatus.REJECTED, MembershipStatus.EXPIRED]:
        return render(request, 'onboarding/status_rejected.html', context)

    return render(request, 'onboarding/status_registered.html', context)


@login_required
def onboarding_form(request):
    """The mandatory profile form that must be filled within 30 days."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('frontend:members:member_create')

    member = request.user.member_profile

    if member.membership_status not in [
        MembershipStatus.REGISTERED,
        MembershipStatus.FORM_PENDING,
        MembershipStatus.IN_REVIEW,
    ]:
        messages.info(request, _('Votre formulaire a deja ete soumis.'))
        return redirect('frontend:onboarding:dashboard')

    if member.is_form_expired:
        messages.error(request, _('Le delai de soumission est expire.'))
        return redirect('frontend:onboarding:dashboard')

    # Get custom form fields
    custom_fields = OnboardingFormField.objects.filter(is_active=True).order_by('order')

    if request.method == 'POST':
        form = OnboardingProfileForm(request.POST, request.FILES, instance=member)
        if form.is_valid():
            form.save()

            # Save custom field responses
            for field in custom_fields:
                value = request.POST.get(f'custom_{field.pk}', '')
                file_obj = request.FILES.get(f'custom_file_{field.pk}')
                if value or file_obj:
                    resp, _created = OnboardingFormResponse.objects.update_or_create(
                        member=member, field=field,
                        defaults={'value': value},
                    )
                    if file_obj:
                        resp.file = file_obj
                        resp.save(update_fields=['file', 'updated_at'])

            OnboardingService.submit_form(member)
            messages.success(request, _('Formulaire soumis avec succes! En attente de validation.'))
            return redirect('frontend:onboarding:dashboard')
    else:
        form = OnboardingProfileForm(instance=member)

    # Load existing responses for custom fields
    existing_responses = {}
    for resp in OnboardingFormResponse.objects.filter(member=member):
        existing_responses[str(resp.field_id)] = resp.value

    context = {
        'form': form,
        'member': member,
        'days_remaining': member.days_remaining_for_form,
        'page_title': _("Formulaire d'adhesion"),
        'custom_fields': custom_fields,
        'existing_responses': existing_responses,
    }
    return render(request, 'onboarding/form_complete.html', context)


@login_required
def my_training(request):
    """View current training progress and lesson materials."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('frontend:members:member_create')

    member = request.user.member_profile
    training = MemberTraining.objects.filter(
        member=member, is_active=True
    ).select_related('course').first()

    if not training:
        messages.info(request, _('Aucune formation assignee.'))
        return redirect('frontend:onboarding:dashboard')

    scheduled_lessons = training.scheduled_lessons.select_related(
        'lesson'
    ).order_by('lesson__order')

    total = training.total_count
    completed = training.completed_count

    context = {
        'training': training,
        'scheduled_lessons': scheduled_lessons,
        'completed_lessons': completed,
        'total_lessons': total,
        'progress_percent': int((completed / total) * 100) if total > 0 else 0,
        'course': training.course,
        'member': member,
        'page_title': _('Ma formation'),
    }
    return render(request, 'onboarding/training_detail.html', context)


@login_required
def my_interview(request):
    """View and respond to interview scheduling."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('frontend:members:member_create')

    member = request.user.member_profile
    interview = Interview.objects.filter(
        member=member
    ).order_by('-created_at').first()

    if not interview:
        messages.info(request, _('Aucune interview planifiee.'))
        return redirect('frontend:onboarding:dashboard')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'accept':
            OnboardingService.member_accept_interview(interview)
            messages.success(request, _('Date d\'interview confirmee.'))
            return redirect('frontend:onboarding:dashboard')

        elif action == 'counter':
            form = InterviewCounterProposeForm(request.POST)
            if form.is_valid():
                OnboardingService.member_counter_propose(
                    interview,
                    form.cleaned_data['counter_proposed_date']
                )
                messages.success(request, _('Contre-proposition envoyee.'))
                return redirect('frontend:onboarding:dashboard')
    else:
        form = InterviewCounterProposeForm()

    context = {
        'interview': interview,
        'form': form,
        'member': member,
        'page_title': _('Mon interview'),
    }
    return render(request, 'onboarding/interview_detail.html', context)


# ─── P1: Mentee View (item 4) ────────────────────────────────────────────────

@login_required
def mentee_view(request):
    """View assigned mentor and contact info."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')

    member = request.user.member_profile
    assignment = MentorAssignment.objects.filter(
        new_member=member, status='active', is_active=True
    ).select_related('mentor').first()

    context = {
        'assignment': assignment,
        'member': member,
        'page_title': _('Mon mentor'),
    }
    return render(request, 'onboarding/mentee_view.html', context)


# ─── P1: Mentor Dashboard (item 3) ───────────────────────────────────────────

@login_required
def mentor_dashboard(request):
    """Mentor sees assigned mentees, check-in status, notes."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')

    member = request.user.member_profile
    assignments = MentorAssignment.objects.filter(
        mentor=member, is_active=True
    ).select_related('new_member')

    context = {
        'assignments': assignments,
        'member': member,
        'page_title': _('Tableau de bord mentor'),
    }
    return render(request, 'onboarding/mentor_dashboard.html', context)


@login_required
def mentor_checkin(request, pk):
    """Log a check-in for a mentor assignment."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')

    member = request.user.member_profile
    assignment = get_object_or_404(MentorAssignment, pk=pk)

    # Only the mentor or admin can log check-ins
    if assignment.mentor != member and member.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    if request.method == 'POST':
        form = MentorCheckInForm(request.POST)
        if form.is_valid():
            OnboardingService.log_mentor_checkin(
                assignment=assignment,
                notes=form.cleaned_data['notes'],
                logged_by=member,
            )
            messages.success(request, _('Suivi enregistre.'))
            return redirect('/onboarding/mentor/dashboard/')
    else:
        form = MentorCheckInForm()

    checkins = assignment.check_ins.order_by('-date')

    context = {
        'form': form,
        'assignment': assignment,
        'checkins': checkins,
        'page_title': f'Suivi - {assignment.new_member.full_name}',
    }
    return render(request, 'onboarding/mentor_checkin.html', context)


# ─── P2: Journey Map (item 20) ───────────────────────────────────────────────

@login_required
def journey_map(request):
    """Visual step-by-step progress indicator with icons."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')

    member = request.user.member_profile
    status = member.membership_status

    steps = [
        {'key': 'registered', 'label': 'Inscription', 'icon': 'fas fa-user-plus'},
        {'key': 'form', 'label': 'Formulaire', 'icon': 'fas fa-file-alt'},
        {'key': 'review', 'label': 'Revision', 'icon': 'fas fa-search'},
        {'key': 'training', 'label': 'Formation', 'icon': 'fas fa-graduation-cap'},
        {'key': 'interview', 'label': 'Interview', 'icon': 'fas fa-comments'},
        {'key': 'active', 'label': 'Membre actif', 'icon': 'fas fa-check-circle'},
    ]

    STATUS_MAP = {
        MembershipStatus.REGISTERED: 0,
        MembershipStatus.FORM_PENDING: 0,
        MembershipStatus.FORM_SUBMITTED: 1,
        MembershipStatus.IN_REVIEW: 2,
        MembershipStatus.APPROVED: 3,
        MembershipStatus.IN_TRAINING: 3,
        MembershipStatus.INTERVIEW_SCHEDULED: 4,
        MembershipStatus.ACTIVE: 5,
    }

    current_step = STATUS_MAP.get(status, 0)

    for i, step in enumerate(steps):
        if i < current_step:
            step['status'] = 'completed'
        elif i == current_step:
            step['status'] = 'current'
        else:
            step['status'] = 'pending'

    context = {
        'steps': steps,
        'current_step': current_step,
        'member': member,
        'whats_next': OnboardingService.get_whats_next(member),
        'estimated_completion': OnboardingService.estimate_completion_date(member),
        'page_title': _('Mon parcours'),
    }
    return render(request, 'onboarding/journey_map.html', context)


# ─── P2: Congratulations Page (item 23) ──────────────────────────────────────

@login_required
def congratulations(request):
    """Congratulations page on onboarding completion."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')

    member = request.user.member_profile
    achievements = MemberAchievement.objects.filter(
        member=member
    ).select_related('achievement')

    context = {
        'member': member,
        'achievements': achievements,
        'page_title': _('Felicitations!'),
    }
    return render(request, 'onboarding/congratulations.html', context)


# ─── P2: Document Signing Views (items 30-31) ────────────────────────────────

@login_required
def document_list(request):
    """List documents for the member to sign."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')

    member = request.user.member_profile
    doc_status = OnboardingService.get_member_document_status(member)

    context = {
        'doc_status': doc_status,
        'member': member,
        'page_title': _('Documents a signer'),
    }
    return render(request, 'onboarding/document_list.html', context)


@login_required
def sign_document(request, pk):
    """Sign a specific document."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')

    member = request.user.member_profile
    document = get_object_or_404(OnboardingDocument, pk=pk)

    # Check if already signed
    existing = DocumentSignature.objects.filter(
        document=document, member=member
    ).first()

    if request.method == 'POST' and not existing:
        form = DocumentSignatureForm(request.POST)
        if form.is_valid():
            ip_address = request.META.get('REMOTE_ADDR')
            OnboardingService.sign_document(
                document=document,
                member=member,
                signature_text=form.cleaned_data['signature_text'],
                ip_address=ip_address,
            )
            messages.success(request, _('Document signe avec succes.'))
            return redirect('/onboarding/documents/')
    else:
        form = DocumentSignatureForm()

    context = {
        'document': document,
        'form': form,
        'existing_signature': existing,
        'member': member,
        'page_title': f'Signer - {document.title}',
    }
    return render(request, 'onboarding/sign_document.html', context)


# ─── P3: Achievement Display (item 42) ───────────────────────────────────────

@login_required
def my_achievements(request):
    """Display member's earned achievements."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')

    member = request.user.member_profile
    earned = MemberAchievement.objects.filter(
        member=member
    ).select_related('achievement')

    total_points = sum(a.achievement.points for a in earned)

    context = {
        'earned': earned,
        'total_points': total_points,
        'member': member,
        'page_title': _('Mes accomplissements'),
    }
    return render(request, 'onboarding/my_achievements.html', context)


# ─── P3: Leaderboard (item 43) ───────────────────────────────────────────────

@login_required
def leaderboard(request):
    """Optional leaderboard showing top achievers."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')

    from django.db.models import Sum, Count

    top_members = (
        MemberAchievement.objects
        .values('member__id', 'member__first_name', 'member__last_name')
        .annotate(
            total_points=Sum('achievement__points'),
            badge_count=Count('id'),
        )
        .order_by('-total_points')[:20]
    )

    context = {
        'top_members': top_members,
        'member': request.user.member_profile,
        'page_title': _('Classement'),
    }
    return render(request, 'onboarding/leaderboard.html', context)


# ─── Admin views ─────────────────────────────────────────────────────────────

@login_required
def admin_pipeline(request):
    """Overview of all members in the onboarding pipeline."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    # Search/filter by member name
    search_query = request.GET.get('q', '').strip()

    from django.db.models import Q

    def _apply_search(qs):
        if search_query:
            qs = qs.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )
        return qs

    # Build annotated lists for Kanban columns
    registered_list = list(_apply_search(Member.objects.filter(
        membership_status=MembershipStatus.REGISTERED
    )))
    for m in registered_list:
        m.days_remaining = m.days_remaining_for_form

    submitted_list = list(_apply_search(Member.objects.filter(
        membership_status=MembershipStatus.FORM_SUBMITTED
    )))
    for m in submitted_list:
        m.submitted_date = m.registration_date

    training_list = list(_apply_search(Member.objects.filter(
        membership_status=MembershipStatus.IN_TRAINING
    )))
    for m in training_list:
        t = MemberTraining.objects.filter(member=m, is_active=True).first()
        if t:
            m.progress_percent = t.progress_percentage
            m.completed_lessons = t.completed_count
            m.total_lessons = t.total_count
        else:
            m.progress_percent = 0
            m.completed_lessons = 0
            m.total_lessons = 0

    interview_list = list(_apply_search(Member.objects.filter(
        membership_status=MembershipStatus.INTERVIEW_SCHEDULED
    )))
    for m in interview_list:
        iv = Interview.objects.filter(member=m).order_by('-created_at').first()
        if iv:
            m.interview_date = iv.final_date
            m.interview_badge = 'info' if iv.status == InterviewStatus.PROPOSED else 'success'
            m.interview_status_display = iv.get_status_display()
        else:
            m.interview_date = None
            m.interview_badge = 'secondary'
            m.interview_status_display = 'En attente'

    # P1 item 50: Check for expired/expiring forms
    from django.utils import timezone
    from datetime import timedelta
    expiring_soon = Member.objects.filter(
        membership_status__in=[MembershipStatus.REGISTERED, MembershipStatus.FORM_PENDING],
        form_deadline__lte=timezone.now() + timedelta(days=3),
        form_deadline__gt=timezone.now(),
    ).count()

    context = {
        'registered_list': registered_list,
        'submitted_list': submitted_list,
        'training_list': training_list,
        'interview_list': interview_list,
        'search_query': search_query,
        'expiring_soon': expiring_soon,
        'total_in_process': Member.objects.filter(
            membership_status__in=MembershipStatus.IN_PROCESS
        ).count(),
        'total_active': Member.objects.filter(
            membership_status=MembershipStatus.ACTIVE
        ).count(),
        'total_pending': len(submitted_list),
        'total_interviews': len(interview_list),
        'page_title': _("Pipeline d'adhesion"),
    }
    return render(request, 'onboarding/admin_pipeline.html', context)


@login_required
def admin_review(request, pk):
    """Review a specific member's application."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    member = get_object_or_404(Member, pk=pk)
    admin_member = request.user.member_profile

    # Get training info if exists
    training = MemberTraining.objects.filter(
        member=member, is_active=True
    ).select_related('course').first()

    if request.method == 'POST':
        form = AdminReviewForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']

            if action == 'approve':
                course = form.cleaned_data.get('course')
                if not course:
                    messages.error(request, _('Veuillez selectionner un parcours de formation.'))
                else:
                    OnboardingService.admin_approve(member, admin_member, course)
                    messages.success(request, _('Membre approuve et parcours assigne.'))
                    return redirect('frontend:onboarding:admin_pipeline')

            elif action == 'reject':
                reason = form.cleaned_data.get('reason', '')
                OnboardingService.admin_reject(member, admin_member, reason)
                messages.success(request, _('Membre refuse.'))
                return redirect('frontend:onboarding:admin_pipeline')

            elif action == 'request_changes':
                message = form.cleaned_data.get('reason', '')
                OnboardingService.admin_request_changes(member, admin_member, message)
                messages.success(request, _('Demande de complements envoyee.'))
                return redirect('frontend:onboarding:admin_pipeline')
    else:
        form = AdminReviewForm()

    # Build training progress for template
    training_progress = None
    if training:
        lessons_qs = training.scheduled_lessons.select_related('lesson').order_by('lesson__order')
        training_progress = {
            'completed': training.completed_count,
            'total': training.total_count,
            'percent': training.progress_percentage,
            'lessons': [
                {
                    'order': sl.lesson.order,
                    'title': sl.lesson.title,
                    'scheduled_date': sl.scheduled_date,
                    'status': sl.status,
                }
                for sl in lessons_qs
            ],
        }

    STATUS_BADGES = {
        'registered': 'secondary', 'form_submitted': 'warning',
        'in_review': 'warning', 'approved': 'info',
        'in_training': 'primary', 'interview_scheduled': 'info',
        'active': 'success', 'rejected': 'danger', 'expired': 'dark',
    }

    # Build submission data from member profile
    submission = None
    submission_fields = {}
    if member.form_submitted_at:
        submission = member
        submission_fields = {}
        if member.email:
            submission_fields['Courriel'] = member.email
        if member.phone:
            submission_fields['Telephone'] = member.phone
        if member.birth_date:
            submission_fields['Date de naissance'] = member.birth_date.strftime('%d/%m/%Y')
        if member.address:
            submission_fields['Adresse'] = member.address
        if member.city:
            submission_fields['Ville'] = member.city
        if hasattr(member, 'family_status') and member.family_status:
            submission_fields['Etat civil'] = member.get_family_status_display()
        submission_fields['Formulaire soumis le'] = member.form_submitted_at.strftime('%d/%m/%Y a %H:%M')

    # Get custom field responses
    custom_responses = OnboardingFormResponse.objects.filter(
        member=member
    ).select_related('field')

    # Get interview for quick action links
    interview = Interview.objects.filter(member=member).order_by('-created_at').first()

    # P2: Document signature status
    doc_status = OnboardingService.get_member_document_status(member)

    context = {
        'member': member,
        'training': training,
        'review_form': form,
        'training_progress': training_progress,
        'status_badge': STATUS_BADGES.get(member.membership_status, 'secondary'),
        'status_display': member.get_membership_status_display(),
        'submission': submission,
        'submission_fields': submission_fields,
        'custom_responses': custom_responses,
        'interview': interview,
        'doc_status': doc_status,
        'page_title': f'Revision - {member.full_name}',
    }
    return render(request, 'onboarding/admin_review.html', context)


@login_required
def admin_schedule_interview(request, pk):
    """Schedule an interview for a member who completed training."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    member = get_object_or_404(Member, pk=pk)
    training = MemberTraining.objects.filter(
        member=member, is_completed=True
    ).first()

    if not training:
        messages.error(request, _('Ce membre n\'a pas encore complete sa formation.'))
        return redirect('frontend:onboarding:admin_review', pk=pk)

    if request.method == 'POST':
        form = ScheduleInterviewForm(request.POST)
        if form.is_valid():
            OnboardingService.schedule_interview(
                member=member,
                training=training,
                interviewer=form.cleaned_data['interviewer'],
                proposed_date=form.cleaned_data['proposed_date'],
                location=form.cleaned_data.get('location', ''),
            )
            messages.success(request, _('Interview planifiee.'))
            return redirect('frontend:onboarding:admin_pipeline')
    else:
        form = ScheduleInterviewForm()

    interviewers = Member.objects.filter(
        role__in=[Roles.ADMIN, Roles.PASTOR],
        is_active=True
    )

    context = {
        'member': member,
        'training': training,
        'form': form,
        'interviewers': interviewers,
        'page_title': f'Planifier interview - {member.full_name}',
    }
    return render(request, 'onboarding/admin_schedule_interview.html', context)


@login_required
def admin_interview_result(request, pk):
    """Record the result of an interview."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    interview = get_object_or_404(Interview, pk=pk)

    if request.method == 'POST':
        form = InterviewResultForm(request.POST)
        if form.is_valid():
            passed = form.cleaned_data['passed']
            notes = form.cleaned_data.get('result_notes', '')
            OnboardingService.complete_interview(interview, passed, notes)
            messages.success(request, _('Resultat enregistre.'))
            return redirect('frontend:onboarding:admin_pipeline')
    else:
        form = InterviewResultForm()

    context = {
        'interview': interview,
        'member': interview.member,
        'form': form,
        'page_title': f'Resultat interview - {interview.member.full_name}',
    }
    return render(request, 'onboarding/admin_interview_result.html', context)


@login_required
def admin_schedule_lessons(request, training_pk):
    """Schedule lesson dates for a member's training."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    training = get_object_or_404(
        MemberTraining.objects.select_related('member', 'course'),
        pk=training_pk
    )
    scheduled_lessons = training.scheduled_lessons.select_related('lesson').order_by('lesson__order')

    if request.method == 'POST':
        # Process dates for each lesson
        updated = 0
        for sl in scheduled_lessons:
            date_key = f'date_{sl.pk}'
            location_key = f'location_{sl.pk}'
            if date_key in request.POST and request.POST[date_key]:
                from django.utils.dateparse import parse_datetime
                new_date = parse_datetime(request.POST[date_key])
                if new_date:
                    sl.scheduled_date = new_date
                    sl.location = request.POST.get(location_key, '')
                    sl.save(update_fields=['scheduled_date', 'location', 'updated_at'])
                    # Auto-create or update attendance session for this lesson
                    from apps.attendance.models import AttendanceSession
                    from apps.core.constants import AttendanceSessionType
                    AttendanceSession.objects.update_or_create(
                        scheduled_lesson=sl,
                        defaults={
                            'name': f'{sl.lesson.title} - {training.member.full_name}',
                            'session_type': AttendanceSessionType.LESSON,
                            'date': new_date.date(),
                            'start_time': new_date.time(),
                            'opened_by': request.user.member_profile,
                        }
                    )
                    updated += 1
        if updated:
            messages.success(request, _(f'{updated} lecon(s) planifiee(s).'))
        return redirect('frontend:onboarding:admin_review', pk=training.member.pk)

    context = {
        'training': training,
        'member': training.member,
        'course': training.course,
        'courses': TrainingCourse.objects.filter(is_active=True),
        'scheduled_lessons': scheduled_lessons,
        'lessons': scheduled_lessons,
        'page_title': f'Planifier lecons - {training.member.full_name}',
    }
    return render(request, 'onboarding/admin_schedule_lessons.html', context)


@login_required
def admin_courses(request):
    """Manage training courses."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    courses = TrainingCourse.objects.filter(is_active=True)

    context = {
        'courses': courses,
        'page_title': _('Parcours de formation'),
    }
    return render(request, 'onboarding/admin_courses.html', context)


@login_required
def admin_course_create(request):
    """Create a new training course."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    if request.method == 'POST':
        form = TrainingCourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.created_by = request.user.member_profile
            course.save()
            messages.success(request, _('Parcours cree. Ajoutez maintenant les lecons.'))
            return redirect('frontend:onboarding:admin_course_detail', pk=course.pk)
    else:
        form = TrainingCourseForm()

    context = {
        'form': form,
        'page_title': _('Nouveau parcours'),
    }
    return render(request, 'onboarding/admin_course_form.html', context)


@login_required
def admin_course_detail(request, pk):
    """View and manage lessons for a training course."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    course = get_object_or_404(TrainingCourse, pk=pk)
    lessons = course.lessons.filter(is_active=True).order_by('order')
    next_order = (lessons.last().order + 1) if lessons.exists() else 1

    # Handle adding a new lesson
    if request.method == 'POST':
        form = LessonForm(request.POST, request.FILES)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.course = course
            lesson.save()
            messages.success(request, _('Lecon ajoutee.'))
            return redirect('frontend:onboarding:admin_course_detail', pk=course.pk)
    else:
        form = LessonForm(initial={'order': next_order})

    context = {
        'course': course,
        'lessons': lessons,
        'lesson_form': form,
        'next_order': next_order,
        'page_title': course.name,
    }
    return render(request, 'onboarding/admin_course_detail.html', context)


@login_required
def admin_course_edit(request, pk):
    """Edit an existing training course."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    course = get_object_or_404(TrainingCourse, pk=pk)

    if request.method == 'POST':
        form = TrainingCourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, _('Parcours mis a jour.'))
            return redirect('frontend:onboarding:admin_course_detail', pk=course.pk)
    else:
        form = TrainingCourseForm(instance=course)

    context = {
        'form': form,
        'course': course,
        'page_title': f'Modifier - {course.name}',
    }
    return render(request, 'onboarding/admin_course_form.html', context)


@login_required
def admin_lesson_edit(request, course_pk, pk):
    """Edit an existing lesson."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    from .models import Lesson
    course = get_object_or_404(TrainingCourse, pk=course_pk)
    lesson = get_object_or_404(Lesson, pk=pk, course=course)

    if request.method == 'POST':
        form = LessonForm(request.POST, request.FILES, instance=lesson)
        if form.is_valid():
            form.save()
            messages.success(request, _('Lecon mise a jour.'))
            return redirect('frontend:onboarding:admin_course_detail', pk=course.pk)
    else:
        form = LessonForm(instance=lesson)

    context = {
        'form': form,
        'course': course,
        'lesson': lesson,
        'page_title': f'Modifier - {lesson.title}',
    }
    return render(request, 'onboarding/admin_lesson_form.html', context)


@login_required
def admin_lesson_delete(request, course_pk, pk):
    """Soft-delete a lesson."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    from .models import Lesson
    course = get_object_or_404(TrainingCourse, pk=course_pk)
    lesson = get_object_or_404(Lesson, pk=pk, course=course)

    if request.method == 'POST':
        lesson.is_active = False
        lesson.save(update_fields=['is_active', 'updated_at'])
        messages.success(request, _('Lecon supprimee.'))

    return redirect('frontend:onboarding:admin_course_detail', pk=course.pk)


# ─── P1: Lesson Reordering (item 16) ─────────────────────────────────────────

@login_required
@require_POST
def admin_lesson_reorder(request, course_pk):
    """POST endpoint for drag-and-drop lesson reordering."""
    if not _is_admin_or_pastor(request):
        return JsonResponse({'error': 'Acces refuse'}, status=403)

    import json
    course = get_object_or_404(TrainingCourse, pk=course_pk)

    try:
        data = json.loads(request.body)
        lesson_order = data.get('order', [])
    except (json.JSONDecodeError, AttributeError):
        lesson_order = request.POST.getlist('order')

    if lesson_order:
        OnboardingService.reorder_lessons(course, lesson_order)
        return JsonResponse({'status': 'ok'})

    return JsonResponse({'error': 'No order provided'}, status=400)


# ─── Enhanced Admin Dashboard ─────────────────────────────────────────────────

@login_required
def admin_stats(request):
    """Enhanced statistics dashboard for the onboarding pipeline."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    from .stats import OnboardingStats

    context = {
        'pipeline': OnboardingStats.pipeline_counts(),
        'success_rate': OnboardingStats.success_rate(),
        'avg_days': OnboardingStats.avg_completion_days(),
        'training': OnboardingStats.training_stats(),
        'interviews': OnboardingStats.interview_stats(),
        'attendance': OnboardingStats.attendance_stats(),
        'activity': OnboardingStats.recent_activity(),
        'monthly': OnboardingStats.monthly_registrations(),
        'mentor_stats': OnboardingStats.mentor_stats(),
        'visitor_stats': OnboardingStats.visitor_stats(),
        'page_title': _("Statistiques d'adhesion"),
    }
    return render(request, 'onboarding/admin_stats.html', context)


# ─── Invitation Views ────────────────────────────────────────────────────────

@login_required
def admin_invitations(request):
    """List all invitation codes (admin only)."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('frontend:reports:dashboard')

    member = request.user.member_profile
    if member.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Acces non autorise.'))
        return redirect('frontend:reports:dashboard')

    invitations = InvitationCode.objects.select_related('created_by', 'used_by').all()
    context = {
        'invitations': invitations,
        'page_title': _('Codes d\'invitation'),
    }
    return render(request, 'onboarding/admin_invitations.html', context)


@login_required
def admin_invitation_create(request):
    """Create a new invitation code (admin only)."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('frontend:reports:dashboard')

    member = request.user.member_profile
    if member.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Acces non autorise.'))
        return redirect('frontend:reports:dashboard')

    if request.method == 'POST':
        form = InvitationCreateForm(request.POST)
        if form.is_valid():
            invitation = OnboardingService.create_invitation(
                created_by=member,
                role=form.cleaned_data['role'],
                expires_in_days=form.cleaned_data['expires_in_days'],
                max_uses=form.cleaned_data['max_uses'],
                skip_onboarding=form.cleaned_data['skip_onboarding'],
                note=form.cleaned_data.get('note', ''),
            )
            messages.success(
                request,
                _('Code d\'invitation cree: ') + invitation.code
            )
            return redirect('/onboarding/admin/invitations/')
    else:
        form = InvitationCreateForm()

    context = {
        'form': form,
        'page_title': _('Creer une invitation'),
    }
    return render(request, 'onboarding/admin_invitation_form.html', context)


@login_required
def accept_invitation(request):
    """Allow a member to enter an invitation code."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('frontend:members:member_create')

    member = request.user.member_profile

    if request.method == 'POST':
        form = InvitationAcceptForm(request.POST)
        if form.is_valid():
            invitation = form.invitation
            try:
                OnboardingService.accept_invitation(invitation, member)
                messages.success(
                    request,
                    _('Invitation acceptee! Role assigne: ') + invitation.get_role_display()
                )
                if invitation.skip_onboarding:
                    return redirect('frontend:reports:dashboard')
                return redirect('/onboarding/dashboard/')
            except ValueError as e:
                messages.error(request, str(e))
    else:
        form = InvitationAcceptForm()

    context = {
        'form': form,
        'page_title': _('Utiliser un code d\'invitation'),
    }
    return render(request, 'onboarding/accept_invitation.html', context)


@login_required
def admin_invitation_edit(request, pk):
    """Edit an existing invitation code (admin only)."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('frontend:reports:dashboard')

    member = request.user.member_profile
    if member.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Acces non autorise.'))
        return redirect('frontend:reports:dashboard')

    invitation = get_object_or_404(InvitationCode, pk=pk)

    if request.method == 'POST':
        form = InvitationEditForm(request.POST, instance=invitation)
        if form.is_valid():
            form.save()
            messages.success(request, _('Code d\'invitation mis a jour.'))
            return redirect('/onboarding/admin/invitations/')
    else:
        form = InvitationEditForm(instance=invitation)

    context = {
        'form': form,
        'invitation': invitation,
        'page_title': _('Modifier l\'invitation'),
    }
    return render(request, 'onboarding/admin_invitation_edit.html', context)


@login_required
def admin_invitation_delete(request, pk):
    """Deactivate an invitation code (admin only)."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('frontend:reports:dashboard')

    member = request.user.member_profile
    if member.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Acces non autorise.'))
        return redirect('frontend:reports:dashboard')

    invitation = get_object_or_404(InvitationCode, pk=pk)

    if request.method == 'POST':
        invitation.is_active = False
        invitation.save()
        messages.success(request, _('Code d\'invitation desactive.'))
        return redirect('/onboarding/admin/invitations/')

    context = {
        'invitation': invitation,
        'page_title': _('Desactiver l\'invitation'),
    }
    return render(request, 'onboarding/admin_invitation_delete.html', context)


# ─── P1: Mentor Admin Views (item 2) ─────────────────────────────────────────

@login_required
def admin_mentor_assign(request):
    """Admin assigns a mentor from available member list."""
    if not _is_admin_or_pastor(request):
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    if request.method == 'POST':
        form = MentorAssignmentForm(request.POST)
        if form.is_valid():
            OnboardingService.assign_mentor(
                new_member=form.cleaned_data['new_member'],
                mentor=form.cleaned_data['mentor'],
                notes=form.cleaned_data.get('notes', ''),
            )
            messages.success(request, _('Mentor assigne avec succes.'))
            return redirect('/onboarding/admin/pipeline/')
    else:
        form = MentorAssignmentForm()

    context = {
        'form': form,
        'page_title': _('Assigner un mentor'),
    }
    return render(request, 'onboarding/admin_mentor_assign.html', context)


# ─── P1: Custom Form Field Admin CRUD (items 8) ──────────────────────────────

@login_required
def admin_form_fields(request):
    """List and manage custom form fields."""
    if not _is_admin_or_pastor(request):
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    fields = OnboardingFormField.objects.filter(is_active=True).order_by('order')
    context = {
        'fields': fields,
        'page_title': _('Champs de formulaire personnalises'),
    }
    return render(request, 'onboarding/admin_form_fields.html', context)


@login_required
def admin_form_field_create(request):
    """Create a custom form field."""
    if not _is_admin_or_pastor(request):
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    if request.method == 'POST':
        form = OnboardingFormFieldForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Champ cree.'))
            return redirect('/onboarding/admin/form-fields/')
    else:
        form = OnboardingFormFieldForm()

    context = {
        'form': form,
        'page_title': _('Nouveau champ'),
    }
    return render(request, 'onboarding/admin_form_field_form.html', context)


@login_required
def admin_form_field_edit(request, pk):
    """Edit a custom form field."""
    if not _is_admin_or_pastor(request):
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    field = get_object_or_404(OnboardingFormField, pk=pk)

    if request.method == 'POST':
        form = OnboardingFormFieldForm(request.POST, instance=field)
        if form.is_valid():
            form.save()
            messages.success(request, _('Champ mis a jour.'))
            return redirect('/onboarding/admin/form-fields/')
    else:
        form = OnboardingFormFieldForm(instance=field)

    context = {
        'form': form,
        'field_obj': field,
        'page_title': f'Modifier - {field.label}',
    }
    return render(request, 'onboarding/admin_form_field_form.html', context)


@login_required
def admin_form_field_delete(request, pk):
    """Soft-delete a custom form field."""
    if not _is_admin_or_pastor(request):
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    field = get_object_or_404(OnboardingFormField, pk=pk)

    if request.method == 'POST':
        field.is_active = False
        field.save(update_fields=['is_active', 'updated_at'])
        messages.success(request, _('Champ supprime.'))

    return redirect('/onboarding/admin/form-fields/')


# ─── P1: Form Data Export CSV (item 10) ──────────────────────────────────────

@login_required
def admin_form_export_csv(request):
    """Export custom form responses as CSV."""
    if not _is_admin_or_pastor(request):
        return redirect('/')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="onboarding_form_data.csv"'

    writer = csv.writer(response)
    fields = OnboardingFormField.objects.filter(is_active=True).order_by('order')

    # Header row
    header = ['Membre', 'Courriel'] + [f.label for f in fields]
    writer.writerow(header)

    # Data rows
    members_with_responses = Member.objects.filter(
        form_responses__isnull=False
    ).distinct()

    for member in members_with_responses:
        row = [member.full_name, member.email or '']
        for field in fields:
            resp = OnboardingFormResponse.objects.filter(
                member=member, field=field
            ).first()
            row.append(resp.value if resp else '')
        writer.writerow(row)

    return response


# ─── P1: Welcome Sequence Admin CRUD (item 14) ───────────────────────────────

@login_required
def admin_welcome_sequences(request):
    """List welcome sequences."""
    if not _is_admin_or_pastor(request):
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    sequences = WelcomeSequence.objects.all()
    context = {
        'sequences': sequences,
        'page_title': _('Sequences de bienvenue'),
    }
    return render(request, 'onboarding/admin_welcome_sequences.html', context)


@login_required
def admin_welcome_sequence_create(request):
    """Create a welcome sequence."""
    if not _is_admin_or_pastor(request):
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    if request.method == 'POST':
        form = WelcomeSequenceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Sequence creee.'))
            return redirect('/onboarding/admin/welcome-sequences/')
    else:
        form = WelcomeSequenceForm()

    context = {
        'form': form,
        'page_title': _('Nouvelle sequence'),
    }
    return render(request, 'onboarding/admin_welcome_sequence_form.html', context)


@login_required
def admin_welcome_sequence_detail(request, pk):
    """View and manage steps for a welcome sequence."""
    if not _is_admin_or_pastor(request):
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    sequence = get_object_or_404(WelcomeSequence, pk=pk)
    steps = sequence.steps.filter(is_active=True).order_by('order')

    if request.method == 'POST':
        form = WelcomeStepForm(request.POST)
        if form.is_valid():
            step = form.save(commit=False)
            step.sequence = sequence
            step.save()
            messages.success(request, _('Etape ajoutee.'))
            return redirect(f'/onboarding/admin/welcome-sequences/{sequence.pk}/')
    else:
        form = WelcomeStepForm()

    context = {
        'sequence': sequence,
        'steps': steps,
        'step_form': form,
        'page_title': sequence.name,
    }
    return render(request, 'onboarding/admin_welcome_sequence_detail.html', context)


# ─── P1: Bulk Pipeline Actions (item 17) ─────────────────────────────────────

@login_required
@require_POST
def admin_bulk_action(request):
    """Handle bulk actions on pipeline members."""
    if not _is_admin_or_pastor(request):
        return JsonResponse({'error': 'Acces refuse'}, status=403)

    action = request.POST.get('action', '')
    member_ids_str = request.POST.get('member_ids', '')
    member_ids = [mid.strip() for mid in member_ids_str.split(',') if mid.strip()]

    admin_member = request.user.member_profile

    if not member_ids:
        messages.error(request, _('Aucun membre selectionne.'))
        return redirect('/onboarding/admin/pipeline/')

    if action == 'approve':
        course_pk = request.POST.get('course')
        if not course_pk:
            messages.error(request, _('Veuillez selectionner un parcours.'))
            return redirect('/onboarding/admin/pipeline/')
        course = get_object_or_404(TrainingCourse, pk=course_pk)
        count = OnboardingService.bulk_approve(member_ids, admin_member, course)
        messages.success(request, _(f'{count} membre(s) approuve(s).'))

    elif action == 'send_reminder':
        count = OnboardingService.bulk_send_reminder(member_ids)
        messages.success(request, _(f'{count} rappel(s) envoye(s).'))

    return redirect('/onboarding/admin/pipeline/')


# ─── P2: Visitor Follow-Up Admin Views (item 27) ─────────────────────────────

@login_required
def admin_visitors(request):
    """List visitor follow-ups."""
    if not _is_admin_or_pastor(request):
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    visitors = VisitorFollowUp.objects.select_related('assigned_to', 'member').all()
    context = {
        'visitors': visitors,
        'visitor_stats': OnboardingService.visitor_conversion_stats(),
        'page_title': _('Suivi des visiteurs'),
    }
    return render(request, 'onboarding/admin_visitors.html', context)


@login_required
def admin_visitor_create(request):
    """Create a visitor follow-up."""
    if not _is_admin_or_pastor(request):
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    if request.method == 'POST':
        form = VisitorFollowUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Suivi de visiteur cree.'))
            return redirect('/onboarding/admin/visitors/')
    else:
        form = VisitorFollowUpForm()

    context = {
        'form': form,
        'page_title': _('Nouveau suivi de visiteur'),
    }
    return render(request, 'onboarding/admin_visitor_form.html', context)


# ─── P2: Document Admin Views (items 28-32) ──────────────────────────────────

@login_required
def admin_documents(request):
    """List onboarding documents."""
    if not _is_admin_or_pastor(request):
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    documents = OnboardingDocument.objects.filter(is_active=True)
    context = {
        'documents': documents,
        'page_title': _('Documents d\'integration'),
    }
    return render(request, 'onboarding/admin_documents.html', context)


@login_required
def admin_document_create(request):
    """Create an onboarding document."""
    if not _is_admin_or_pastor(request):
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    if request.method == 'POST':
        form = OnboardingDocumentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Document cree.'))
            return redirect('/onboarding/admin/documents/')
    else:
        form = OnboardingDocumentForm()

    context = {
        'form': form,
        'page_title': _('Nouveau document'),
    }
    return render(request, 'onboarding/admin_document_form.html', context)


@login_required
def admin_document_signatures(request, pk):
    """View all signatures for a document."""
    if not _is_admin_or_pastor(request):
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    document = get_object_or_404(OnboardingDocument, pk=pk)
    signatures = document.signatures.select_related('member').order_by('-signed_at')

    context = {
        'document': document,
        'signatures': signatures,
        'page_title': f'Signatures - {document.title}',
    }
    return render(request, 'onboarding/admin_document_signatures.html', context)


# ─── P3: Track Admin Views (items 35-38) ─────────────────────────────────────

@login_required
def admin_tracks(request):
    """List onboarding tracks."""
    if not _is_admin_or_pastor(request):
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    tracks = OnboardingTrackModel.objects.filter(is_active=True)
    context = {
        'tracks': tracks,
        'page_title': _('Parcours multi-pistes'),
    }
    return render(request, 'onboarding/admin_tracks.html', context)


@login_required
def admin_track_create(request):
    """Create an onboarding track."""
    if not _is_admin_or_pastor(request):
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    if request.method == 'POST':
        form = OnboardingTrackForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Parcours cree.'))
            return redirect('/onboarding/admin/tracks/')
    else:
        form = OnboardingTrackForm()

    context = {
        'form': form,
        'page_title': _('Nouveau parcours multi-piste'),
    }
    return render(request, 'onboarding/admin_track_form.html', context)


@login_required
def admin_track_analytics(request):
    """Track comparison analytics view."""
    if not _is_admin_or_pastor(request):
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    from .stats import OnboardingStats
    track_stats = OnboardingStats.track_comparison()

    context = {
        'track_stats': track_stats,
        'page_title': _('Comparaison des parcours'),
    }
    return render(request, 'onboarding/admin_track_analytics.html', context)


# ─── P3: Achievement Admin Views ─────────────────────────────────────────────

@login_required
def admin_achievements(request):
    """List achievements."""
    if not _is_admin_or_pastor(request):
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    achievements = Achievement.objects.filter(is_active=True)
    context = {
        'achievements': achievements,
        'page_title': _('Accomplissements'),
    }
    return render(request, 'onboarding/admin_achievements.html', context)


@login_required
def admin_achievement_create(request):
    """Create an achievement."""
    if not _is_admin_or_pastor(request):
        messages.error(request, _('Acces refuse.'))
        return redirect('/')

    if request.method == 'POST':
        form = AchievementForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, _('Accomplissement cree.'))
            return redirect('/onboarding/admin/achievements/')
    else:
        form = AchievementForm()

    context = {
        'form': form,
        'page_title': _('Nouvel accomplissement'),
    }
    return render(request, 'onboarding/admin_achievement_form.html', context)
