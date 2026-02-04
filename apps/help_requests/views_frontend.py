"""Help Requests frontend views."""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from apps.core.mixins import PastorRequiredMixin
from .models import HelpRequest, HelpRequestCategory
from .forms import HelpRequestForm, HelpRequestCommentForm, HelpRequestAssignForm


@login_required
def request_create(request):
    """Create a new help request."""
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
    """List all help requests (pastor/admin only)."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in ['pastor', 'admin']:
        messages.error(request, "Accès non autorisé.")
        return redirect('frontend:help_requests:my_requests')

    queryset = HelpRequest.objects.select_related(
        'member', 'category', 'assigned_to'
    ).order_by('-created_at')

    # Apply filters
    status_filter = request.GET.get('status')
    urgency_filter = request.GET.get('urgency')
    category_filter = request.GET.get('category')

    if status_filter:
        queryset = queryset.filter(status=status_filter)
    if urgency_filter:
        queryset = queryset.filter(urgency=urgency_filter)
    if category_filter:
        queryset = queryset.filter(category_id=category_filter)

    categories = HelpRequestCategory.objects.filter(is_active=True)

    return render(request, 'help_requests/request_list.html', {
        'requests': queryset,
        'categories': categories,
        'current_status': status_filter,
        'current_urgency': urgency_filter,
        'current_category': category_filter,
    })


@login_required
def request_detail(request, pk):
    """View help request details."""
    member = getattr(request.user, 'member_profile', None)
    if not member:
        messages.error(request, "Profil membre requis.")
        return redirect('frontend:members:member_list')

    help_request = get_object_or_404(HelpRequest, pk=pk)

    # Check access permissions
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

    # Get comments (filter internal for non-staff)
    comments = help_request.comments.select_related('author')
    if member.role not in ['pastor', 'admin']:
        comments = comments.filter(is_internal=False)

    comment_form = HelpRequestCommentForm()
    assign_form = HelpRequestAssignForm() if member.role in ['pastor', 'admin'] else None

    return render(request, 'help_requests/request_detail.html', {
        'help_request': help_request,
        'comments': comments,
        'comment_form': comment_form,
        'assign_form': assign_form,
        'can_manage': member.role in ['pastor', 'admin'],
    })


@login_required
def my_requests(request):
    """List current user's help requests."""
    member = getattr(request.user, 'member_profile', None)
    if not member:
        messages.error(request, "Profil membre requis.")
        return redirect('frontend:members:member_list')

    queryset = HelpRequest.objects.filter(member=member).select_related(
        'category', 'assigned_to'
    ).order_by('-created_at')

    return render(request, 'help_requests/my_requests.html', {
        'requests': queryset,
    })


@login_required
def request_update(request, pk):
    """Update help request status (pastor/admin only)."""
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
                messages.success(request, f"Demande assignée à {assignee.full_name}.")

        elif action == 'resolve':
            notes = request.POST.get('resolution_notes', '')
            help_request.mark_resolved(notes)
            messages.success(request, "Demande marquée comme résolue.")

        elif action == 'close':
            help_request.status = 'closed'
            help_request.save()
            messages.success(request, "Demande fermée.")

    return redirect('frontend:help_requests:request_detail', pk=pk)


@login_required
def request_comment(request, pk):
    """Add comment to a help request."""
    member = getattr(request.user, 'member_profile', None)
    if not member:
        messages.error(request, "Profil membre requis.")
        return redirect('frontend:members:member_list')

    help_request = get_object_or_404(HelpRequest, pk=pk)

    # Check access
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

            # Only staff can create internal comments
            if comment.is_internal and member.role not in ['pastor', 'admin']:
                comment.is_internal = False

            comment.save()
            messages.success(request, "Commentaire ajouté.")

    return redirect('frontend:help_requests:request_detail', pk=pk)
