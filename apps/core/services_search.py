"""Global search service for cross-app searching with role-based filtering."""
from django.db.models import Q, Value, CharField
from django.utils.translation import gettext_lazy as _

from apps.core.constants import Roles


class GlobalSearchService:
    """
    Searches across Members, Events, Donations, Groups, HelpRequests.
    Respects role-based access: staff see everything, members see limited data.
    """

    MIN_QUERY_LENGTH = 2
    MAX_RESULTS_PER_CATEGORY = 10

    def __init__(self, user):
        self.user = user
        self.member = getattr(user, 'member_profile', None)
        self.is_staff = self._check_staff()

    def _check_staff(self) -> bool:
        """Check if user has staff-level access."""
        if self.user.is_superuser or self.user.is_staff:
            return True
        if self.member:
            return self.member.role in Roles.STAFF_ROLES
        return False

    def search(self, query: str) -> dict:
        """
        Execute search across all categories.
        Returns dict of {category: queryset}.
        """
        if not query or len(query) < self.MIN_QUERY_LENGTH:
            return {}

        results = {}

        members = self._search_members(query)
        if members is not None:
            results['members'] = members

        events = self._search_events(query)
        if events is not None:
            results['events'] = events

        groups = self._search_groups(query)
        if groups is not None:
            results['groups'] = groups

        if self.is_staff:
            help_requests = self._search_help_requests(query)
            if help_requests is not None:
                results['help_requests'] = help_requests

            donations = self._search_donations(query)
            if donations is not None:
                results['donations'] = donations

        return results

    def search_autocomplete(self, query: str, limit: int = 8) -> list:
        """
        Quick autocomplete search returning simplified results for AJAX.
        Returns list of dicts with {label, url, category, icon}.
        """
        if not query or len(query) < self.MIN_QUERY_LENGTH:
            return []

        suggestions = []

        # Members
        members = self._search_members(query)
        if members is not None:
            for m in members[:3]:
                suggestions.append({
                    'label': m.full_name,
                    'url': f'/members/{m.pk}/',
                    'category': 'Membre',
                    'icon': 'fa-user',
                })

        # Events
        events = self._search_events(query)
        if events is not None:
            for e in events[:2]:
                suggestions.append({
                    'label': e.title,
                    'url': f'/events/{e.pk}/',
                    'category': 'Événement',
                    'icon': 'fa-calendar',
                })

        # Groups
        groups = self._search_groups(query)
        if groups is not None:
            for g in groups[:2]:
                suggestions.append({
                    'label': g.name,
                    'url': f'/members/groups/{g.pk}/',
                    'category': 'Groupe',
                    'icon': 'fa-layer-group',
                })

        # Help Requests (staff only)
        if self.is_staff:
            help_requests = self._search_help_requests(query)
            if help_requests is not None:
                for hr in help_requests[:1]:
                    suggestions.append({
                        'label': hr.title,
                        'url': f'/help-requests/{hr.pk}/',
                        'category': 'Demande d\'aide',
                        'icon': 'fa-question-circle',
                    })

        return suggestions[:limit]

    def _search_members(self, query: str):
        """Search members by name, email, or member number."""
        from apps.members.models import Member

        qs = Member.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(member_number__icontains=query),
            is_active=True,
        )

        if not self.is_staff and self.member:
            qs = qs.filter(
                Q(privacy_settings__visibility='public') |
                Q(pk=self.member.pk)
            )

        return qs[:self.MAX_RESULTS_PER_CATEGORY]

    def _search_events(self, query: str):
        """Search events by title or description."""
        from apps.events.models import Event

        return Event.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query),
            is_active=True,
        )[:self.MAX_RESULTS_PER_CATEGORY]

    def _search_groups(self, query: str):
        """Search groups by name."""
        from apps.members.models import Group

        return Group.objects.filter(
            Q(name__icontains=query),
            is_active=True,
        )[:self.MAX_RESULTS_PER_CATEGORY]

    def _search_help_requests(self, query: str):
        """Search help requests (staff only)."""
        from apps.help_requests.models import HelpRequest

        return HelpRequest.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query),
        )[:self.MAX_RESULTS_PER_CATEGORY]

    def _search_donations(self, query: str):
        """Search donations by number or donor name (staff only)."""
        from apps.donations.models import Donation

        return Donation.objects.filter(
            Q(donation_number__icontains=query) |
            Q(member__first_name__icontains=query) |
            Q(member__last_name__icontains=query),
        ).select_related('member')[:self.MAX_RESULTS_PER_CATEGORY]

    @staticmethod
    def get_total_count(results: dict) -> int:
        """Count total results across all categories."""
        total = 0
        for qs in results.values():
            if hasattr(qs, 'count'):
                total += len(qs)  # Already sliced, use len
            else:
                total += len(qs)
        return total
