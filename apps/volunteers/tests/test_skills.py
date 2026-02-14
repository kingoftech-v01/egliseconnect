"""Tests for skills matrix matching: models, service, views."""
import pytest
from django.test import Client

from apps.core.constants import Roles, SkillProficiency
from apps.members.tests.factories import MemberFactory, MemberWithUserFactory
from apps.volunteers.models import Skill, VolunteerSkill
from apps.volunteers.tests.factories import (
    VolunteerPositionFactory, SkillFactory, VolunteerSkillFactory,
)
from apps.volunteers.services_skills import SkillMatchingService

pytestmark = pytest.mark.django_db


class TestSkillModel:
    """Tests for Skill model."""

    def test_str_returns_name(self):
        skill = SkillFactory(name='Piano')
        assert str(skill) == 'Piano'

    def test_unique_name(self):
        SkillFactory(name='Guitare')
        with pytest.raises(Exception):
            SkillFactory(name='Guitare')


class TestVolunteerSkillModel:
    """Tests for VolunteerSkill model."""

    def test_str_contains_member_and_skill(self):
        vs = VolunteerSkillFactory()
        result = str(vs)
        assert vs.member.full_name in result
        assert vs.skill.name in result

    def test_unique_member_skill(self):
        member = MemberFactory()
        skill = SkillFactory()
        VolunteerSkillFactory(member=member, skill=skill)
        with pytest.raises(Exception):
            VolunteerSkillFactory(member=member, skill=skill)

    def test_proficiency_levels(self):
        vs = VolunteerSkillFactory(proficiency_level=SkillProficiency.EXPERT)
        assert vs.proficiency_level == 'expert'


class TestSkillMatchingService:
    """Tests for SkillMatchingService."""

    def test_suggest_volunteers_empty_requirements(self):
        position = VolunteerPositionFactory(skills_required='')
        result = SkillMatchingService.suggest_volunteers_for_position(position)
        assert result == []

    def test_suggest_volunteers_with_matching_skills(self):
        skill = SkillFactory(name='Piano')
        member = MemberFactory()
        VolunteerSkillFactory(member=member, skill=skill)
        position = VolunteerPositionFactory(skills_required='Piano, Chant')
        result = SkillMatchingService.suggest_volunteers_for_position(position)
        assert len(result) == 1
        assert result[0]['member'] == member
        assert 'Piano' in result[0]['matching_skills']

    def test_suggest_volunteers_no_match(self):
        SkillFactory(name='Danse')
        position = VolunteerPositionFactory(skills_required='Piano')
        result = SkillMatchingService.suggest_volunteers_for_position(position)
        assert len(result) == 0

    def test_skill_gap_analysis_empty(self):
        position = VolunteerPositionFactory(skills_required='')
        result = SkillMatchingService.skill_gap_analysis(position)
        assert result['required_skills'] == []

    def test_skill_gap_analysis_all_covered(self):
        skill = SkillFactory(name='Piano')
        VolunteerSkillFactory(skill=skill)
        position = VolunteerPositionFactory(skills_required='Piano')
        result = SkillMatchingService.skill_gap_analysis(position)
        assert 'piano' in result['covered_skills']
        assert result['missing_skills'] == []

    def test_skill_gap_analysis_missing(self):
        position = VolunteerPositionFactory(skills_required='Piano, Guitare')
        result = SkillMatchingService.skill_gap_analysis(position)
        assert len(result['missing_skills']) == 2


class TestSkillsViews:
    """Tests for skills frontend views."""

    def test_skills_list_requires_login(self):
        client = Client()
        response = client.get('/volunteers/skills/')
        assert response.status_code == 302

    def test_skills_list_get(self):
        user = MemberWithUserFactory(role=Roles.VOLUNTEER).user
        client = Client()
        client.force_login(user)
        response = client.get('/volunteers/skills/')
        assert response.status_code == 200

    def test_skills_profile_get(self):
        user = MemberWithUserFactory(role=Roles.VOLUNTEER).user
        client = Client()
        client.force_login(user)
        response = client.get('/volunteers/skills/profile/')
        assert response.status_code == 200

    def test_add_skill_to_profile(self):
        user = MemberWithUserFactory(role=Roles.VOLUNTEER).user
        skill = SkillFactory()
        client = Client()
        client.force_login(user)
        response = client.post('/volunteers/skills/profile/', {
            'skill': skill.pk,
            'proficiency_level': SkillProficiency.INTERMEDIATE,
        })
        assert response.status_code == 302
        assert VolunteerSkill.objects.filter(member=user.member_profile, skill=skill).exists()

    def test_staff_can_create_skill(self):
        user = MemberWithUserFactory(role=Roles.PASTOR).user
        client = Client()
        client.force_login(user)
        response = client.post('/volunteers/skills/', {
            'name': 'New Skill',
            'category': 'Music',
            'description': 'Test skill',
        })
        assert response.status_code == 302
        assert Skill.objects.filter(name='New Skill').exists()
