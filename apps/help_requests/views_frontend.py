"""Help Requests frontend views."""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from apps.core.constants import Roles, HelpRequestStatus, HelpRequestUrgency
from apps.core.mixins import PastorRequiredMixin
from .models import HelpRequest, HelpRequestCategory
from .forms import HelpRequestForm, HelpRequestCommentForm, HelpRequestAssignForm, HelpRequestCategoryForm


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
