"""Global search frontend view with AJAX autocomplete."""
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect

from apps.core.services_search import GlobalSearchService


@login_required
def search_view(request):
    """Global search across members, events, groups, and help requests."""
    if not hasattr(request.user, 'member_profile'):
        return redirect('/onboarding/dashboard/')

    query = request.GET.get('q', '').strip()

    service = GlobalSearchService(request.user)
    results = service.search(query)
    total_count = service.get_total_count(results)

    context = {
        'query': query,
        'results': results,
        'total_count': total_count,
        'page_title': f'Recherche: {query}' if query else 'Recherche',
    }
    return render(request, 'core/search_results.html', context)


@login_required
def search_autocomplete(request):
    """AJAX endpoint for search typeahead/autocomplete suggestions."""
    if not hasattr(request.user, 'member_profile'):
        return JsonResponse({'suggestions': []})

    query = request.GET.get('q', '').strip()
    service = GlobalSearchService(request.user)
    suggestions = service.search_autocomplete(query)

    return JsonResponse({'suggestions': suggestions})
