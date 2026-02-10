"""Global search frontend view."""
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect

from apps.core.constants import Roles


@login_required
def search_view(request):
    """Global search across members, events, groups, and help requests."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/onboarding/dashboard/')

    query = request.GET.get('q', '').strip()
    member = request.user.member_profile
    is_staff = member.role in Roles.STAFF_ROLES or request.user.is_superuser
    results = {}

    if query and len(query) >= 2:
        from apps.members.models import Member, Group
        from apps.events.models import Event

        # Members search (staff sees all, members see directory-public only)
        member_qs = Member.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(member_number__icontains=query)
        ).filter(is_active=True)

        if not is_staff:
            member_qs = member_qs.filter(
                Q(privacy_settings__visibility='public') |
                Q(pk=member.pk)
            )

        results['members'] = member_qs[:10]

        # Events search
        results['events'] = Event.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query),
            is_active=True,
        )[:10]

        # Groups search
        results['groups'] = Group.objects.filter(
            Q(name__icontains=query),
            is_active=True,
        )[:10]

        # Help requests (staff sees all, members see own)
        if is_staff:
            from apps.help_requests.models import HelpRequest
            results['help_requests'] = HelpRequest.objects.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query),
            )[:10]

    total_count = sum(qs.count() if hasattr(qs, 'count') else len(qs) for qs in results.values())

    context = {
        'query': query,
        'results': results,
        'total_count': total_count,
        'page_title': f'Recherche: {query}' if query else 'Recherche',
    }
    return render(request, 'core/search_results.html', context)
