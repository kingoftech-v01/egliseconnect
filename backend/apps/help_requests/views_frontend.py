"""Help Requests frontend views."""
from datetime import date, timedelta

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count
from django.utils import timezone

from apps.core.constants import (
    Roles, HelpRequestStatus, HelpRequestUrgency,
    CareStatus, PrayerRequestStatus, BenevolenceStatus, MealTrainStatus,
)
from apps.core.mixins import PastorRequiredMixin
from .models import (
    HelpRequest, HelpRequestCategory, HelpRequestComment,
    PastoralCare, PrayerRequest, CareTeam, CareTeamMember,
    BenevolenceRequest, BenevolenceFund,
    MealTrain, MealSignup,
    CrisisProtocol, CrisisResource,
)
from .forms import (
    HelpRequestForm, HelpRequestCommentForm, HelpRequestAssignForm,
    HelpRequestCategoryForm,
    PastoralCareForm, PastoralCareUpdateForm,
    PrayerRequestForm, AnonymousPrayerRequestForm, PrayerRequestTestimonyForm,
    CareTeamForm, CareTeamMemberForm,
    BenevolenceRequestForm, BenevolenceApprovalForm, BenevolenceFundForm,
    MealTrainForm, MealSignupForm,
    CrisisProtocolForm, CrisisResourceForm,
)


# ═══════════════════════════════════════════════════════════════════════════════
# EXISTING HELP REQUEST VIEWS (with refinements from P1)
# ═══════════════════════════════════════════════════════════════════════════════


@login_required
def request_create(request):
    member = getattr(request.user, 'member_profile', None)
    if not member:
        messages.error(request, "Profil membre requis.")
        return redirect('frontend:members:member_list')

    if request.method == 'POST':
        form = HelpRequestForm(request.POST)
        if form.is_valid():
            help_request = form.save(commit=False)
            help_request.member = member
            help_request.save()
            messages.success(request, f"Demande {help_request.request_number} créée avec succès.")
            return redirect('frontend:help_requests:request_detail', pk=help_request.pk)
    else:
        form = HelpRequestForm()

    categories = HelpRequestCategory.objects.filter(is_active=True)

    return render(request, 'help_requests/request_create.html', {
        'form': form,
        'categories': categories,
    })


@login_required
def request_list(request):
    """Pastor/admin only."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in ['pastor', 'admin']:
        messages.error(request, "Accès non autorisé.")
        return redirect('frontend:help_requests:my_requests')

    queryset = HelpRequest.objects.select_related(
        'member', 'category', 'assigned_to'
    ).order_by('-created_at')

    status_filter = request.GET.get('status')
    urgency_filter = request.GET.get('urgency')
    category_filter = request.GET.get('category')
    search_query = request.GET.get('q', '').strip()

    if status_filter:
        queryset = queryset.filter(status=status_filter)
    if urgency_filter:
        queryset = queryset.filter(urgency=urgency_filter)
    if category_filter:
        queryset = queryset.filter(category_id=category_filter)
    if search_query:
        queryset = queryset.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )

    # Statistics summary
    all_requests = HelpRequest.objects.all()
    stats = {
        'open': all_requests.filter(status=HelpRequestStatus.NEW).count(),
        'in_progress': all_requests.filter(status=HelpRequestStatus.IN_PROGRESS).count(),
        'resolved': all_requests.filter(status=HelpRequestStatus.RESOLVED).count(),
    }

    categories = HelpRequestCategory.objects.filter(is_active=True)

    return render(request, 'help_requests/request_list.html', {
        'requests': queryset,
        'categories': categories,
        'current_status': status_filter,
        'current_urgency': urgency_filter,
        'current_category': category_filter,
        'search_query': search_query,
        'stats': stats,
    })


@login_required
def request_detail(request, pk):
    member = getattr(request.user, 'member_profile', None)
    if not member:
        messages.error(request, "Profil membre requis.")
        return redirect('frontend:members:member_list')

    help_request = get_object_or_404(HelpRequest, pk=pk)

    # Group leaders can view their members' non-confidential requests
    is_group_member = False
    if member.role == 'group_leader':
        from apps.members.models import GroupMembership
        group_member_ids = GroupMembership.objects.filter(
            group__leader=member
        ).values_list('member_id', flat=True)
        is_group_member = help_request.member_id in set(group_member_ids)

    can_view = (
        help_request.member == member or
        member.role in ['pastor', 'admin'] or
        (member.role == 'group_leader' and is_group_member and not help_request.is_confidential)
    )

    if not can_view:
        messages.error(request, "Accès non autorisé à cette demande.")
        return redirect('frontend:help_requests:my_requests')

    comments = help_request.comments.select_related('author')
    if member.role not in ['pastor', 'admin']:
        comments = comments.filter(is_internal=False)

    comment_form = HelpRequestCommentForm()
    assign_form = HelpRequestAssignForm() if member.role in ['pastor', 'admin'] else None
    can_manage = member.role in ['pastor', 'admin']

    # Can close: staff can close, or owner can close if resolved
    can_close = (
        can_manage and help_request.status not in ['closed']
    ) or (
        help_request.member == member
        and help_request.status == HelpRequestStatus.RESOLVED
    )

    # Status timeline
    timeline = []
    timeline.append({
        'status': 'Créée',
        'date': help_request.created_at,
        'active': True,
    })
    if help_request.assigned_to:
        timeline.append({
            'status': 'Assignée',
            'date': help_request.updated_at if help_request.status in ['in_progress', 'resolved', 'closed'] else None,
            'active': help_request.status in ['in_progress', 'resolved', 'closed'],
        })
    if help_request.status in ['resolved', 'closed']:
        timeline.append({
            'status': 'Résolue',
            'date': help_request.resolved_at,
            'active': True,
        })
    if help_request.status == 'closed':
        timeline.append({
            'status': 'Fermée',
            'date': help_request.updated_at,
            'active': True,
        })

    return render(request, 'help_requests/request_detail.html', {
        'help_request': help_request,
        'comments': comments,
        'comment_form': comment_form,
        'assign_form': assign_form,
        'can_manage': can_manage,
        'can_close': can_close,
        'timeline': timeline,
    })


@login_required
def my_requests(request):
    member = getattr(request.user, 'member_profile', None)
    if not member:
        messages.error(request, "Profil membre requis.")
        return redirect('frontend:members:member_list')

    queryset = HelpRequest.objects.filter(member=member).select_related(
        'category', 'assigned_to'
    ).order_by('-created_at')

    paginator = Paginator(queryset, 20)
    page = request.GET.get('page', 1)
    requests_page = paginator.get_page(page)

    return render(request, 'help_requests/my_requests.html', {
        'requests': requests_page,
    })


@login_required
def request_update(request, pk):
    """Pastor/admin only."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in ['pastor', 'admin']:
        messages.error(request, "Accès non autorisé.")
        return redirect('frontend:help_requests:my_requests')

    help_request = get_object_or_404(HelpRequest, pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'assign':
            form = HelpRequestAssignForm(request.POST)
            if form.is_valid():
                from apps.members.models import Member
                assignee = Member.objects.get(id=form.cleaned_data['assigned_to'])
                help_request.assign_to(assignee)
                # Send notification on status change
                _notify_status_change(help_request, 'assigned', member)
                messages.success(request, f"Demande assignée à {assignee.full_name}.")

        elif action == 'resolve':
            notes = request.POST.get('resolution_notes', '')
            help_request.mark_resolved(notes)
            _notify_status_change(help_request, 'resolved', member)
            messages.success(request, "Demande marquée comme résolue.")

        elif action == 'close':
            help_request.status = 'closed'
            help_request.save()
            _notify_status_change(help_request, 'closed', member)
            messages.success(request, "Demande fermée.")

    return redirect('frontend:help_requests:request_detail', pk=pk)


@login_required
def request_comment(request, pk):
    member = getattr(request.user, 'member_profile', None)
    if not member:
        messages.error(request, "Profil membre requis.")
        return redirect('frontend:members:member_list')

    help_request = get_object_or_404(HelpRequest, pk=pk)

    can_comment = (
        help_request.member == member or
        member.role in ['pastor', 'admin']
    )

    if not can_comment:
        messages.error(request, "Vous ne pouvez pas commenter cette demande.")
        return redirect('frontend:help_requests:my_requests')

    if request.method == 'POST':
        form = HelpRequestCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.help_request = help_request
            comment.author = member

            # Non-staff cannot create internal comments
            if comment.is_internal and member.role not in ['pastor', 'admin']:
                comment.is_internal = False

            comment.save()
            messages.success(request, "Commentaire ajouté.")

    return redirect('frontend:help_requests:request_detail', pk=pk)


# ─── Category CRUD (P1) ──────────────────────────────────────────────────────


@login_required
def category_list(request):
    """List help request categories (admin only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in ['pastor', 'admin']:
        messages.error(request, "Accès non autorisé.")
        return redirect('/help-requests/')

    categories = HelpRequestCategory.all_objects.all().order_by('order', 'name')

    return render(request, 'help_requests/category_list.html', {
        'categories': categories,
        'page_title': 'Catégories de demandes',
    })


@login_required
def category_create(request):
    """Create a new help request category (admin only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in ['pastor', 'admin']:
        messages.error(request, "Accès non autorisé.")
        return redirect('/help-requests/')

    if request.method == 'POST':
        form = HelpRequestCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Catégorie créée avec succès.")
            return redirect('/help-requests/categories/')
    else:
        form = HelpRequestCategoryForm()

    return render(request, 'help_requests/category_form.html', {
        'form': form,
        'page_title': 'Nouvelle catégorie',
    })


@login_required
def category_edit(request, pk):
    """Edit a help request category (admin only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in ['pastor', 'admin']:
        messages.error(request, "Accès non autorisé.")
        return redirect('/help-requests/')

    category = get_object_or_404(HelpRequestCategory.all_objects, pk=pk)

    if request.method == 'POST':
        form = HelpRequestCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Catégorie mise à jour.")
            return redirect('/help-requests/categories/')
    else:
        form = HelpRequestCategoryForm(instance=category)

    return render(request, 'help_requests/category_form.html', {
        'form': form,
        'category': category,
        'page_title': 'Modifier la catégorie',
    })


@login_required
def category_delete(request, pk):
    """Delete a help request category (admin only, POST confirmation)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in ['pastor', 'admin']:
        messages.error(request, "Accès non autorisé.")
        return redirect('/help-requests/')

    category = get_object_or_404(HelpRequestCategory.all_objects, pk=pk)

    if request.method == 'POST':
        # Check if category has associated requests
        request_count = HelpRequest.objects.filter(category=category).count()
        if request_count > 0:
            # Deactivate instead of deleting
            category.is_active = False
            category.save(update_fields=['is_active', 'updated_at'])
            messages.success(request, f"Catégorie désactivée ({request_count} demande(s) associée(s)).")
        else:
            category.delete()
            messages.success(request, "Catégorie supprimée.")
        return redirect('/help-requests/categories/')

    request_count = HelpRequest.objects.filter(category=category).count()

    return render(request, 'help_requests/category_delete.html', {
        'category': category,
        'request_count': request_count,
        'page_title': 'Supprimer la catégorie',
    })


# ═══════════════════════════════════════════════════════════════════════════════
# P1: PASTORAL CARE VIEWS
# ═══════════════════════════════════════════════════════════════════════════════


@login_required
def care_dashboard(request):
    """Dashboard for pastors: open cases, upcoming follow-ups, overdue items."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in ['pastor', 'admin']:
        messages.error(request, "Accès non autorisé.")
        return redirect('/help-requests/')

    today = date.today()

    open_cases = PastoralCare.objects.filter(
        status=CareStatus.OPEN
    ).select_related('member', 'assigned_to').order_by('-date')

    upcoming_followups = PastoralCare.objects.filter(
        status__in=[CareStatus.OPEN, CareStatus.FOLLOW_UP],
        follow_up_date__gte=today,
        follow_up_date__lte=today + timedelta(days=14),
    ).select_related('member', 'assigned_to').order_by('follow_up_date')

    overdue = PastoralCare.objects.filter(
        status__in=[CareStatus.OPEN, CareStatus.FOLLOW_UP],
        follow_up_date__lt=today,
    ).select_related('member', 'assigned_to').order_by('follow_up_date')

    # Aggregate stats
    total_open = PastoralCare.objects.filter(status=CareStatus.OPEN).count()
    total_follow_up = PastoralCare.objects.filter(status=CareStatus.FOLLOW_UP).count()
    closed_this_month = PastoralCare.objects.filter(
        status=CareStatus.CLOSED,
        updated_at__month=today.month,
        updated_at__year=today.year,
    ).count()

    # Care type breakdown
    care_type_breakdown = PastoralCare.objects.values('care_type').annotate(
        count=Count('id')
    ).order_by('-count')

    return render(request, 'help_requests/care_dashboard.html', {
        'open_cases': open_cases,
        'upcoming_followups': upcoming_followups,
        'overdue': overdue,
        'total_open': total_open,
        'total_follow_up': total_follow_up,
        'closed_this_month': closed_this_month,
        'care_type_breakdown': care_type_breakdown,
        'page_title': 'Tableau de bord pastoral',
    })


@login_required
def care_create(request):
    """Log a new pastoral care visit."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in ['pastor', 'admin']:
        messages.error(request, "Accès non autorisé.")
        return redirect('/help-requests/')

    if request.method == 'POST':
        form = PastoralCareForm(request.POST)
        if form.is_valid():
            care = form.save(commit=False)
            care.created_by = member
            care.save()
            messages.success(request, "Visite pastorale enregistrée.")
            return redirect('/help-requests/care/')
    else:
        form = PastoralCareForm()

    return render(request, 'help_requests/care_form.html', {
        'form': form,
        'page_title': 'Nouvelle visite pastorale',
    })


@login_required
def care_detail(request, pk):
    """View a pastoral care record."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in ['pastor', 'admin']:
        messages.error(request, "Accès non autorisé.")
        return redirect('/help-requests/')

    care = get_object_or_404(PastoralCare, pk=pk)

    return render(request, 'help_requests/care_detail.html', {
        'care': care,
        'page_title': f'Visite: {care.get_care_type_display()}',
    })


@login_required
def care_update(request, pk):
    """Update notes and follow-up date on a care visit."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in ['pastor', 'admin']:
        messages.error(request, "Accès non autorisé.")
        return redirect('/help-requests/')

    care = get_object_or_404(PastoralCare, pk=pk)

    if request.method == 'POST':
        form = PastoralCareUpdateForm(request.POST, instance=care)
        if form.is_valid():
            form.save()
            messages.success(request, "Visite mise à jour.")
            return redirect('/help-requests/care/')
    else:
        form = PastoralCareUpdateForm(instance=care)

    return render(request, 'help_requests/care_form.html', {
        'form': form,
        'care': care,
        'page_title': 'Modifier la visite',
    })


@login_required
def care_calendar(request):
    """Calendar view of scheduled visits and follow-ups by date."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in ['pastor', 'admin']:
        messages.error(request, "Accès non autorisé.")
        return redirect('/help-requests/')

    today = date.today()
    start = today - timedelta(days=today.weekday())  # Monday
    end = start + timedelta(days=27)  # 4 weeks

    visits = PastoralCare.objects.filter(
        date__date__gte=start,
        date__date__lte=end,
    ).select_related('member', 'assigned_to').order_by('date')

    follow_ups = PastoralCare.objects.filter(
        follow_up_date__gte=start,
        follow_up_date__lte=end,
        status__in=[CareStatus.OPEN, CareStatus.FOLLOW_UP],
    ).select_related('member', 'assigned_to').order_by('follow_up_date')

    return render(request, 'help_requests/care_calendar.html', {
        'visits': visits,
        'follow_ups': follow_ups,
        'start_date': start,
        'end_date': end,
        'page_title': 'Calendrier pastoral',
    })


# ═══════════════════════════════════════════════════════════════════════════════
# P1: PRAYER REQUEST VIEWS
# ═══════════════════════════════════════════════════════════════════════════════


@login_required
def prayer_request_create(request):
    """Logged-in member submits a prayer request."""
    member = getattr(request.user, 'member_profile', None)
    if not member:
        messages.error(request, "Profil membre requis.")
        return redirect('frontend:members:member_list')

    if request.method == 'POST':
        form = PrayerRequestForm(request.POST)
        if form.is_valid():
            prayer = form.save(commit=False)
            prayer.member = member
            prayer.is_approved = True  # Auto-approve logged-in submissions
            prayer.save()
            # Notify prayer team
            _notify_prayer_team(prayer)
            messages.success(request, "Demande de prière soumise.")
            return redirect('/help-requests/prayer/wall/')
    else:
        form = PrayerRequestForm()

    return render(request, 'help_requests/prayer_form.html', {
        'form': form,
        'page_title': 'Nouvelle demande de prière',
    })


def prayer_request_anonymous(request):
    """Public-facing anonymous prayer request form (no login required)."""
    if request.method == 'POST':
        # Simple rate limiting: check session for last submission
        last_submit = request.session.get('last_prayer_submit')
        if last_submit:
            from datetime import datetime
            last_dt = datetime.fromisoformat(last_submit)
            if (timezone.now() - timezone.make_aware(last_dt) if timezone.is_naive(last_dt) else timezone.now() - last_dt).total_seconds() < 60:
                messages.warning(request, "Veuillez attendre avant de soumettre une autre demande.")
                return redirect('/help-requests/prayer/anonymous/')

        form = AnonymousPrayerRequestForm(request.POST)
        if form.is_valid():
            prayer = form.save(commit=False)
            prayer.is_anonymous = True
            prayer.is_public = True
            prayer.is_approved = False  # Needs moderation
            prayer.save()
            request.session['last_prayer_submit'] = timezone.now().isoformat()
            messages.success(request, "Demande de prière soumise. Elle sera visible après modération.")
            return redirect('/help-requests/prayer/anonymous/done/')
    else:
        form = AnonymousPrayerRequestForm()

    return render(request, 'help_requests/prayer_anonymous.html', {
        'form': form,
        'page_title': 'Demande de prière anonyme',
    })


def prayer_anonymous_done(request):
    """Confirmation page after anonymous prayer submission."""
    return render(request, 'help_requests/prayer_anonymous_done.html', {
        'page_title': 'Merci',
    })


@login_required
def prayer_wall(request):
    """Public prayer wall: display approved, non-anonymous, public requests."""
    prayers = PrayerRequest.objects.filter(
        is_public=True,
        is_approved=True,
    ).select_related('member').order_by('-created_at')

    return render(request, 'help_requests/prayer_wall.html', {
        'prayers': prayers,
        'page_title': 'Mur de prière',
    })


@login_required
def prayer_request_detail(request, pk):
    """Detail view for a prayer request."""
    prayer = get_object_or_404(PrayerRequest, pk=pk)
    member = getattr(request.user, 'member_profile', None)

    can_manage = member and member.role in ['pastor', 'admin']
    is_owner = member and prayer.member == member

    return render(request, 'help_requests/prayer_detail.html', {
        'prayer': prayer,
        'can_manage': can_manage,
        'is_owner': is_owner,
        'page_title': prayer.title,
    })


@login_required
def prayer_mark_answered(request, pk):
    """Mark a prayer request as answered with optional testimony."""
    member = getattr(request.user, 'member_profile', None)
    prayer = get_object_or_404(PrayerRequest, pk=pk)

    is_owner = member and prayer.member == member
    can_manage = member and member.role in ['pastor', 'admin']

    if not (is_owner or can_manage):
        messages.error(request, "Accès non autorisé.")
        return redirect('/help-requests/prayer/wall/')

    if request.method == 'POST':
        form = PrayerRequestTestimonyForm(request.POST)
        if form.is_valid():
            prayer.mark_answered(testimony=form.cleaned_data.get('testimony', ''))
            messages.success(request, "Prière marquée comme exaucée.")
            return redirect(f'/help-requests/prayer/{pk}/')
    else:
        form = PrayerRequestTestimonyForm()

    return render(request, 'help_requests/prayer_answered.html', {
        'form': form,
        'prayer': prayer,
        'page_title': 'Prière exaucée',
    })


@login_required
def prayer_moderation(request):
    """Moderation queue for anonymous prayer requests (pastor/admin)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in ['pastor', 'admin']:
        messages.error(request, "Accès non autorisé.")
        return redirect('/help-requests/')

    pending = PrayerRequest.objects.filter(
        is_approved=False,
    ).order_by('-created_at')

    return render(request, 'help_requests/prayer_moderation.html', {
        'pending': pending,
        'page_title': 'Modération des demandes de prière',
    })


@login_required
def prayer_moderate_action(request, pk):
    """Approve or reject an anonymous prayer request."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in ['pastor', 'admin']:
        messages.error(request, "Accès non autorisé.")
        return redirect('/help-requests/')

    prayer = get_object_or_404(PrayerRequest, pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            prayer.is_approved = True
            prayer.save(update_fields=['is_approved', 'updated_at'])
            messages.success(request, "Demande approuvée.")
        elif action == 'reject':
            prayer.is_approved = False
            prayer.status = PrayerRequestStatus.CLOSED
            prayer.save(update_fields=['is_approved', 'status', 'updated_at'])
            messages.success(request, "Demande rejetée.")

    return redirect('/help-requests/prayer/moderation/')


# ═══════════════════════════════════════════════════════════════════════════════
# P1: CARE TEAM VIEWS
# ═══════════════════════════════════════════════════════════════════════════════


@login_required
def care_team_list(request):
    """List care teams (pastor/admin)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in ['pastor', 'admin']:
        messages.error(request, "Accès non autorisé.")
        return redirect('/help-requests/')

    teams = CareTeam.objects.select_related('leader').prefetch_related('memberships__member')

    return render(request, 'help_requests/care_team_list.html', {
        'teams': teams,
        'page_title': 'Équipes de soins',
    })


@login_required
def care_team_create(request):
    """Create a new care team."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in ['pastor', 'admin']:
        messages.error(request, "Accès non autorisé.")
        return redirect('/help-requests/')

    if request.method == 'POST':
        form = CareTeamForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Équipe créée.")
            return redirect('/help-requests/care/teams/')
    else:
        form = CareTeamForm()

    return render(request, 'help_requests/care_team_form.html', {
        'form': form,
        'page_title': 'Nouvelle équipe de soins',
    })


@login_required
def care_team_detail(request, pk):
    """View care team details and members."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in ['pastor', 'admin']:
        messages.error(request, "Accès non autorisé.")
        return redirect('/help-requests/')

    team = get_object_or_404(CareTeam, pk=pk)
    memberships = team.memberships.select_related('member')

    # Add member form
    member_form = CareTeamMemberForm(initial={'team': team})

    return render(request, 'help_requests/care_team_detail.html', {
        'team': team,
        'memberships': memberships,
        'member_form': member_form,
        'page_title': team.name,
    })


@login_required
def care_team_add_member(request, pk):
    """Add a member to a care team."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in ['pastor', 'admin']:
        messages.error(request, "Accès non autorisé.")
        return redirect('/help-requests/')

    team = get_object_or_404(CareTeam, pk=pk)

    if request.method == 'POST':
        form = CareTeamMemberForm(request.POST)
        if form.is_valid():
            membership = form.save(commit=False)
            membership.team = team
            membership.save()
            messages.success(request, "Membre ajouté à l'équipe.")

    return redirect(f'/help-requests/care/teams/{pk}/')


@login_required
def care_team_remove_member(request, pk, member_pk):
    """Remove a member from a care team."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in ['pastor', 'admin']:
        messages.error(request, "Accès non autorisé.")
        return redirect('/help-requests/')

    if request.method == 'POST':
        CareTeamMember.objects.filter(team_id=pk, member_id=member_pk).delete()
        messages.success(request, "Membre retiré de l'équipe.")

    return redirect(f'/help-requests/care/teams/{pk}/')


# ═══════════════════════════════════════════════════════════════════════════════
# P3: BENEVOLENCE FUND VIEWS
# ═══════════════════════════════════════════════════════════════════════════════


@login_required
def benevolence_list(request):
    """List benevolence requests (pastor/admin)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in ['pastor', 'admin']:
        messages.error(request, "Accès non autorisé.")
        return redirect('/help-requests/')

    requests_qs = BenevolenceRequest.objects.select_related(
        'member', 'fund', 'approved_by'
    ).order_by('-created_at')

    status_filter = request.GET.get('status')
    if status_filter:
        requests_qs = requests_qs.filter(status=status_filter)

    funds = BenevolenceFund.objects.all()

    return render(request, 'help_requests/benevolence_list.html', {
        'benevolence_requests': requests_qs,
        'funds': funds,
        'current_status': status_filter,
        'page_title': 'Demandes de bienfaisance',
    })


@login_required
def benevolence_request_create(request):
    """Submit a benevolence request."""
    member = getattr(request.user, 'member_profile', None)
    if not member:
        messages.error(request, "Profil membre requis.")
        return redirect('frontend:members:member_list')

    if request.method == 'POST':
        form = BenevolenceRequestForm(request.POST)
        if form.is_valid():
            benev = form.save(commit=False)
            benev.member = member
            benev.save()
            messages.success(request, "Demande de bienfaisance soumise.")
            return redirect('/help-requests/benevolence/')
    else:
        form = BenevolenceRequestForm()

    return render(request, 'help_requests/benevolence_form.html', {
        'form': form,
        'page_title': 'Nouvelle demande de bienfaisance',
    })


@login_required
def benevolence_detail(request, pk):
    """View benevolence request detail with approval workflow."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in ['pastor', 'admin']:
        messages.error(request, "Accès non autorisé.")
        return redirect('/help-requests/')

    benev = get_object_or_404(BenevolenceRequest, pk=pk)
    approval_form = BenevolenceApprovalForm() if benev.status in [BenevolenceStatus.SUBMITTED, BenevolenceStatus.REVIEWING] else None

    return render(request, 'help_requests/benevolence_detail.html', {
        'benev': benev,
        'approval_form': approval_form,
        'page_title': f'Demande #{str(benev.pk)[:8]}',
    })


@login_required
def benevolence_approve(request, pk):
    """Approve or deny a benevolence request."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in ['pastor', 'admin']:
        messages.error(request, "Accès non autorisé.")
        return redirect('/help-requests/')

    benev = get_object_or_404(BenevolenceRequest, pk=pk)

    if request.method == 'POST':
        form = BenevolenceApprovalForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            if action == 'approve':
                benev.status = BenevolenceStatus.APPROVED
                benev.approved_by = member
                benev.amount_granted = form.cleaned_data.get('amount_granted') or benev.amount_requested
                benev.save()
                messages.success(request, "Demande approuvée.")
            elif action == 'deny':
                benev.status = BenevolenceStatus.DENIED
                benev.approved_by = member
                benev.save()
                messages.success(request, "Demande refusée.")

    return redirect(f'/help-requests/benevolence/{pk}/')


@login_required
def benevolence_disburse(request, pk):
    """Mark a benevolence request as disbursed."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in ['pastor', 'admin']:
        messages.error(request, "Accès non autorisé.")
        return redirect('/help-requests/')

    benev = get_object_or_404(BenevolenceRequest, pk=pk)

    if request.method == 'POST' and benev.status == BenevolenceStatus.APPROVED:
        benev.status = BenevolenceStatus.DISBURSED
        benev.disbursed_at = timezone.now()
        benev.save()
        # Deduct from fund balance
        if benev.fund and benev.amount_granted:
            benev.fund.total_balance -= benev.amount_granted
            benev.fund.save(update_fields=['total_balance', 'updated_at'])
        messages.success(request, "Montant versé.")

    return redirect(f'/help-requests/benevolence/{pk}/')


# ═══════════════════════════════════════════════════════════════════════════════
# P3: MEAL TRAIN VIEWS
# ═══════════════════════════════════════════════════════════════════════════════


@login_required
def meal_train_list(request):
    """List meal trains."""
    member = getattr(request.user, 'member_profile', None)
    if not member:
        messages.error(request, "Profil membre requis.")
        return redirect('frontend:members:member_list')

    trains = MealTrain.objects.select_related('recipient').prefetch_related(
        'signups__volunteer'
    ).order_by('-start_date')

    return render(request, 'help_requests/meal_train_list.html', {
        'trains': trains,
        'page_title': 'Trains de repas',
    })


@login_required
def meal_train_create(request):
    """Create a meal train (pastor/admin)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in ['pastor', 'admin']:
        messages.error(request, "Accès non autorisé.")
        return redirect('/help-requests/')

    if request.method == 'POST':
        form = MealTrainForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Train de repas créé.")
            return redirect('/help-requests/meals/')
    else:
        form = MealTrainForm()

    return render(request, 'help_requests/meal_train_form.html', {
        'form': form,
        'page_title': 'Nouveau train de repas',
    })


@login_required
def meal_train_detail(request, pk):
    """View meal train details and calendar of sign-ups."""
    member = getattr(request.user, 'member_profile', None)
    if not member:
        messages.error(request, "Profil membre requis.")
        return redirect('frontend:members:member_list')

    train = get_object_or_404(MealTrain, pk=pk)
    signups = train.signups.select_related('volunteer').order_by('date')
    signup_form = MealSignupForm() if train.status == MealTrainStatus.ACTIVE else None

    # Build calendar of dates
    from datetime import timedelta as td
    calendar_dates = []
    current = train.start_date
    while current <= train.end_date:
        signup_for_date = signups.filter(date=current).first()
        calendar_dates.append({
            'date': current,
            'signup': signup_for_date,
        })
        current += td(days=1)

    can_manage = member.role in ['pastor', 'admin']

    return render(request, 'help_requests/meal_train_detail.html', {
        'train': train,
        'signups': signups,
        'signup_form': signup_form,
        'calendar_dates': calendar_dates,
        'can_manage': can_manage,
        'page_title': f'Repas pour {train.recipient.full_name}',
    })


@login_required
def meal_train_signup(request, pk):
    """Sign up for a meal train date."""
    member = getattr(request.user, 'member_profile', None)
    if not member:
        messages.error(request, "Profil membre requis.")
        return redirect('frontend:members:member_list')

    train = get_object_or_404(MealTrain, pk=pk)

    if request.method == 'POST' and train.status == MealTrainStatus.ACTIVE:
        form = MealSignupForm(request.POST)
        if form.is_valid():
            signup = form.save(commit=False)
            signup.meal_train = train
            signup.volunteer = member
            signup.save()
            messages.success(request, "Inscription enregistrée. Merci!")

    return redirect(f'/help-requests/meals/{pk}/')


# ═══════════════════════════════════════════════════════════════════════════════
# P3: CRISIS RESPONSE VIEWS
# ═══════════════════════════════════════════════════════════════════════════════


@login_required
def crisis_protocol_list(request):
    """List crisis protocols."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in ['pastor', 'admin']:
        messages.error(request, "Accès non autorisé.")
        return redirect('/help-requests/')

    protocols = CrisisProtocol.objects.all().order_by('title')

    return render(request, 'help_requests/crisis_protocol_list.html', {
        'protocols': protocols,
        'page_title': 'Protocoles de crise',
    })


@login_required
def crisis_protocol_create(request):
    """Create a crisis protocol."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in ['pastor', 'admin']:
        messages.error(request, "Accès non autorisé.")
        return redirect('/help-requests/')

    if request.method == 'POST':
        form = CrisisProtocolForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Protocole créé.")
            return redirect('/help-requests/crisis/protocols/')
    else:
        form = CrisisProtocolForm()

    return render(request, 'help_requests/crisis_protocol_form.html', {
        'form': form,
        'page_title': 'Nouveau protocole',
    })


@login_required
def crisis_protocol_detail(request, pk):
    """View crisis protocol details."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in ['pastor', 'admin']:
        messages.error(request, "Accès non autorisé.")
        return redirect('/help-requests/')

    protocol = get_object_or_404(CrisisProtocol, pk=pk)

    return render(request, 'help_requests/crisis_protocol_detail.html', {
        'protocol': protocol,
        'page_title': protocol.title,
    })


@login_required
def crisis_resource_list(request):
    """List crisis resources."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in ['pastor', 'admin']:
        messages.error(request, "Accès non autorisé.")
        return redirect('/help-requests/')

    resources = CrisisResource.objects.all().order_by('category', 'title')

    return render(request, 'help_requests/crisis_resource_list.html', {
        'resources': resources,
        'page_title': 'Ressources de crise',
    })


@login_required
def crisis_resource_create(request):
    """Create a crisis resource."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in ['pastor', 'admin']:
        messages.error(request, "Accès non autorisé.")
        return redirect('/help-requests/')

    if request.method == 'POST':
        form = CrisisResourceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Ressource créée.")
            return redirect('/help-requests/crisis/resources/')
    else:
        form = CrisisResourceForm()

    return render(request, 'help_requests/crisis_resource_form.html', {
        'form': form,
        'page_title': 'Nouvelle ressource',
    })


@login_required
def crisis_notify(request):
    """Send crisis notification to all care team members."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in ['pastor', 'admin']:
        messages.error(request, "Accès non autorisé.")
        return redirect('/help-requests/')

    if request.method == 'POST':
        title = request.POST.get('title', 'Alerte de crise')
        message_text = request.POST.get('message', '')

        # Notify all care team members
        team_member_ids = CareTeamMember.objects.values_list('member_id', flat=True).distinct()
        from apps.members.models import Member
        from apps.communication.models import Notification
        recipients = Member.objects.filter(id__in=team_member_ids)

        notifications = []
        for recipient in recipients:
            notifications.append(Notification(
                member=recipient,
                title=title,
                message=message_text,
                notification_type='help_request',
                link='/help-requests/crisis/protocols/',
            ))
        Notification.objects.bulk_create(notifications)
        messages.success(request, f"Notification envoyée à {len(notifications)} membres.")
        return redirect('/help-requests/crisis/protocols/')

    return render(request, 'help_requests/crisis_notify.html', {
        'page_title': 'Notification de crise',
    })


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════


def _notify_status_change(help_request, new_status, changed_by):
    """Send notification when a help request status changes."""
    try:
        from apps.communication.models import Notification

        status_labels = {
            'assigned': 'assignée',
            'resolved': 'résolue',
            'closed': 'fermée',
        }
        label = status_labels.get(new_status, new_status)

        # Notify the request owner
        if help_request.member != changed_by:
            Notification.objects.create(
                member=help_request.member,
                title='Mise à jour de votre demande',
                message=f'Votre demande "{help_request.title}" a été {label}.',
                notification_type='help_request',
                link=f'/help-requests/{help_request.pk}/',
            )
    except Exception:
        pass  # Don't break the workflow if notification fails


def _notify_prayer_team(prayer):
    """Notify prayer team members about a new prayer request."""
    try:
        from apps.communication.models import Notification

        # Find all care team members as prayer team
        team_member_ids = CareTeamMember.objects.values_list('member_id', flat=True).distinct()
        from apps.members.models import Member
        recipients = Member.objects.filter(id__in=team_member_ids)

        notifications = []
        for recipient in recipients:
            notifications.append(Notification(
                member=recipient,
                title='Nouvelle demande de prière',
                message=f'Une nouvelle demande de prière a été soumise: "{prayer.title}"',
                notification_type='help_request',
                link='/help-requests/prayer/wall/',
            ))
        if notifications:
            Notification.objects.bulk_create(notifications)
    except Exception:
        pass  # Don't break the workflow if notification fails
