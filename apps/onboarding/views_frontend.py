"""Frontend views for the onboarding process."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext_lazy as _

from apps.core.constants import MembershipStatus, Roles, InterviewStatus, LessonStatus
from apps.members.models import Member
from .models import TrainingCourse, MemberTraining, ScheduledLesson, Interview
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
)
from .models import InvitationCode
from .services import OnboardingService


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
    context = {'member': member, 'page_title': _('Mon parcours')}

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
        messages.info(request, _('Votre formulaire a déjà été soumis.'))
        return redirect('frontend:onboarding:dashboard')

    if member.is_form_expired:
        messages.error(request, _('Le délai de soumission est expiré.'))
        return redirect('frontend:onboarding:dashboard')

    if request.method == 'POST':
        form = OnboardingProfileForm(request.POST, request.FILES, instance=member)
        if form.is_valid():
            form.save()
            OnboardingService.submit_form(member)
            messages.success(request, _('Formulaire soumis avec succès! En attente de validation.'))
            return redirect('frontend:onboarding:dashboard')
    else:
        form = OnboardingProfileForm(instance=member)

    context = {
        'form': form,
        'member': member,
        'days_remaining': member.days_remaining_for_form,
        'page_title': _("Formulaire d'adhésion"),
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
        messages.info(request, _('Aucune formation assignée.'))
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
        messages.info(request, _('Aucune interview planifiée.'))
        return redirect('frontend:onboarding:dashboard')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'accept':
            OnboardingService.member_accept_interview(interview)
            messages.success(request, _('Date d\'interview confirmée.'))
            return redirect('frontend:onboarding:dashboard')

        elif action == 'counter':
            form = InterviewCounterProposeForm(request.POST)
            if form.is_valid():
                OnboardingService.member_counter_propose(
                    interview,
                    form.cleaned_data['counter_proposed_date']
                )
                messages.success(request, _('Contre-proposition envoyée.'))
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


# --- Admin views ---

@login_required
def admin_pipeline(request):
    """Overview of all members in the onboarding pipeline."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Accès refusé.'))
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

    context = {
        'registered_list': registered_list,
        'submitted_list': submitted_list,
        'training_list': training_list,
        'interview_list': interview_list,
        'search_query': search_query,
        'total_in_process': Member.objects.filter(
            membership_status__in=MembershipStatus.IN_PROCESS
        ).count(),
        'total_active': Member.objects.filter(
            membership_status=MembershipStatus.ACTIVE
        ).count(),
        'total_pending': len(submitted_list),
        'total_interviews': len(interview_list),
        'page_title': _("Pipeline d'adhésion"),
    }
    return render(request, 'onboarding/admin_pipeline.html', context)


@login_required
def admin_review(request, pk):
    """Review a specific member's application."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Accès refusé.'))
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
                    messages.error(request, _('Veuillez sélectionner un parcours de formation.'))
                else:
                    OnboardingService.admin_approve(member, admin_member, course)
                    messages.success(request, _('Membre approuvé et parcours assigné.'))
                    return redirect('frontend:onboarding:admin_pipeline')

            elif action == 'reject':
                reason = form.cleaned_data.get('reason', '')
                OnboardingService.admin_reject(member, admin_member, reason)
                messages.success(request, _('Membre refusé.'))
                return redirect('frontend:onboarding:admin_pipeline')

            elif action == 'request_changes':
                message = form.cleaned_data.get('reason', '')
                OnboardingService.admin_request_changes(member, admin_member, message)
                messages.success(request, _('Demande de compléments envoyée.'))
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
        submission_fields['Formulaire soumis le'] = member.form_submitted_at.strftime('%d/%m/%Y à %H:%M')

    # Get interview for quick action links
    interview = Interview.objects.filter(member=member).order_by('-created_at').first()

    context = {
        'member': member,
        'training': training,
        'review_form': form,
        'training_progress': training_progress,
        'status_badge': STATUS_BADGES.get(member.membership_status, 'secondary'),
        'status_display': member.get_membership_status_display(),
        'submission': submission,
        'submission_fields': submission_fields,
        'interview': interview,
        'page_title': f'Révision - {member.full_name}',
    }
    return render(request, 'onboarding/admin_review.html', context)


@login_required
def admin_schedule_interview(request, pk):
    """Schedule an interview for a member who completed training."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Accès refusé.'))
        return redirect('/')

    member = get_object_or_404(Member, pk=pk)
    training = MemberTraining.objects.filter(
        member=member, is_completed=True
    ).first()

    if not training:
        messages.error(request, _('Ce membre n\'a pas encore complété sa formation.'))
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
            messages.success(request, _('Interview planifiée.'))
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
        messages.error(request, _('Accès refusé.'))
        return redirect('/')

    interview = get_object_or_404(Interview, pk=pk)

    if request.method == 'POST':
        form = InterviewResultForm(request.POST)
        if form.is_valid():
            passed = form.cleaned_data['passed']
            notes = form.cleaned_data.get('result_notes', '')
            OnboardingService.complete_interview(interview, passed, notes)
            messages.success(request, _('Résultat enregistré.'))
            return redirect('frontend:onboarding:admin_pipeline')
    else:
        form = InterviewResultForm()

    context = {
        'interview': interview,
        'member': interview.member,
        'form': form,
        'page_title': f'Résultat interview - {interview.member.full_name}',
    }
    return render(request, 'onboarding/admin_interview_result.html', context)


@login_required
def admin_schedule_lessons(request, training_pk):
    """Schedule lesson dates for a member's training."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Accès refusé.'))
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
                    updated += 1
        if updated:
            messages.success(request, _(f'{updated} leçon(s) planifiée(s).'))
        return redirect('frontend:onboarding:admin_review', pk=training.member.pk)

    context = {
        'training': training,
        'member': training.member,
        'course': training.course,
        'courses': TrainingCourse.objects.filter(is_active=True),
        'scheduled_lessons': scheduled_lessons,
        'lessons': scheduled_lessons,
        'page_title': f'Planifier leçons - {training.member.full_name}',
    }
    return render(request, 'onboarding/admin_schedule_lessons.html', context)


@login_required
def admin_courses(request):
    """Manage training courses."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Accès refusé.'))
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
        messages.error(request, _('Accès refusé.'))
        return redirect('/')

    if request.method == 'POST':
        form = TrainingCourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.created_by = request.user.member_profile
            course.save()
            messages.success(request, _('Parcours créé. Ajoutez maintenant les leçons.'))
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
        messages.error(request, _('Accès refusé.'))
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
            messages.success(request, _('Leçon ajoutée.'))
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
        messages.error(request, _('Accès refusé.'))
        return redirect('/')

    course = get_object_or_404(TrainingCourse, pk=pk)

    if request.method == 'POST':
        form = TrainingCourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, _('Parcours mis à jour.'))
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
        messages.error(request, _('Accès refusé.'))
        return redirect('/')

    from .models import Lesson
    course = get_object_or_404(TrainingCourse, pk=course_pk)
    lesson = get_object_or_404(Lesson, pk=pk, course=course)

    if request.method == 'POST':
        form = LessonForm(request.POST, request.FILES, instance=lesson)
        if form.is_valid():
            form.save()
            messages.success(request, _('Leçon mise à jour.'))
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
        messages.error(request, _('Accès refusé.'))
        return redirect('/')

    from .models import Lesson
    course = get_object_or_404(TrainingCourse, pk=course_pk)
    lesson = get_object_or_404(Lesson, pk=pk, course=course)

    if request.method == 'POST':
        lesson.is_active = False
        lesson.save(update_fields=['is_active', 'updated_at'])
        messages.success(request, _('Leçon supprimée.'))

    return redirect('frontend:onboarding:admin_course_detail', pk=course.pk)


# --- Enhanced Admin Dashboard ---

@login_required
def admin_stats(request):
    """Enhanced statistics dashboard for the onboarding pipeline."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/')
    if request.user.member_profile.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Accès refusé.'))
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
        'page_title': _("Statistiques d'adhésion"),
    }
    return render(request, 'onboarding/admin_stats.html', context)


@login_required
def admin_invitations(request):
    """List all invitation codes (admin only)."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('frontend:reports:dashboard')

    member = request.user.member_profile
    if member.role not in [Roles.ADMIN, Roles.PASTOR]:
        messages.error(request, _('Accès non autorisé.'))
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
        messages.error(request, _('Accès non autorisé.'))
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
                _('Code d\'invitation créé: ') + invitation.code
            )
            return redirect('/onboarding/admin/invitations/')
    else:
        form = InvitationCreateForm()

    context = {
        'form': form,
        'page_title': _('Créer une invitation'),
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
                    _('Invitation acceptée! Rôle assigné: ') + invitation.get_role_display()
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
        messages.error(request, _('Accès non autorisé.'))
        return redirect('frontend:reports:dashboard')

    invitation = get_object_or_404(InvitationCode, pk=pk)

    if request.method == 'POST':
        form = InvitationEditForm(request.POST, instance=invitation)
        if form.is_valid():
            form.save()
            messages.success(request, _('Code d\'invitation mis à jour.'))
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
        messages.error(request, _('Accès non autorisé.'))
        return redirect('frontend:reports:dashboard')

    invitation = get_object_or_404(InvitationCode, pk=pk)

    if request.method == 'POST':
        invitation.is_active = False
        invitation.save()
        messages.success(request, _('Code d\'invitation désactivé.'))
        return redirect('/onboarding/admin/invitations/')

    context = {
        'invitation': invitation,
        'page_title': _('Désactiver l\'invitation'),
    }
    return render(request, 'onboarding/admin_invitation_delete.html', context)
