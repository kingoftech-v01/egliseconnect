"""Service for volunteer skill matching and gap analysis."""
from django.db.models import Count, Q

from .models import VolunteerSkill, VolunteerPosition, Skill


class SkillMatchingService:
    """Match volunteers to positions based on skills."""

    @staticmethod
    def suggest_volunteers_for_position(position):
        """
        Suggest volunteers who have skills matching a position's requirements.

        Parses the position's skills_required text field and matches against
        volunteer skill records.

        Returns:
            list of dicts: [{member, matching_skills, match_count}, ...]
        """
        if not position.skills_required:
            return []

        # Parse skills_required (comma-separated text)
        required_keywords = [
            s.strip().lower()
            for s in position.skills_required.split(',')
            if s.strip()
        ]

        if not required_keywords:
            return []

        # Build Q filter for matching skill names
        skill_q = Q()
        for keyword in required_keywords:
            skill_q |= Q(skill__name__icontains=keyword)

        # Find volunteers with matching skills
        matches = (
            VolunteerSkill.objects.filter(skill_q, is_active=True)
            .select_related('member', 'skill')
            .order_by('member__last_name', 'member__first_name')
        )

        # Group by member
        member_map = {}
        for vs in matches:
            mid = vs.member_id
            if mid not in member_map:
                member_map[mid] = {
                    'member': vs.member,
                    'matching_skills': [],
                    'match_count': 0,
                }
            member_map[mid]['matching_skills'].append(vs.skill.name)
            member_map[mid]['match_count'] += 1

        # Sort by match count descending
        results = sorted(member_map.values(), key=lambda x: x['match_count'], reverse=True)
        return results

    @staticmethod
    def skill_gap_analysis(position):
        """
        Analyze the gap between required skills for a position and available volunteers.

        Returns:
            dict: {required_skills: [...], covered_skills: [...], missing_skills: [...]}
        """
        if not position.skills_required:
            return {
                'required_skills': [],
                'covered_skills': [],
                'missing_skills': [],
            }

        required_keywords = [
            s.strip().lower()
            for s in position.skills_required.split(',')
            if s.strip()
        ]

        # Find all skills in DB matching these keywords
        covered = set()
        for keyword in required_keywords:
            if VolunteerSkill.objects.filter(
                skill__name__icontains=keyword,
                is_active=True,
            ).exists():
                covered.add(keyword)

        missing = [k for k in required_keywords if k not in covered]

        return {
            'required_skills': required_keywords,
            'covered_skills': list(covered),
            'missing_skills': missing,
        }
