"""Tests for Member Engagement Score model, service, and views."""
import pytest
from datetime import date

from apps.core.constants import Roles
from apps.members.models import MemberEngagementScore

from .factories import (
    UserFactory,
    MemberFactory,
    PastorFactory,
    AdminMemberFactory,
    GroupFactory,
    GroupMembershipFactory,
    MemberEngagementScoreFactory,
)


@pytest.mark.django_db
class TestMemberEngagementScoreModel:
    """Tests for MemberEngagementScore model."""

    def test_create_score(self):
        """MemberEngagementScore creation with required fields."""
        score = MemberEngagementScoreFactory()
        assert score.id is not None
        assert score.member is not None
        assert score.total_score >= 0

    def test_level_high(self):
        """Level returns 'Très engagé' for score >= 80."""
        score = MemberEngagementScoreFactory(total_score=85)
        assert score.level == 'Très engagé'

    def test_level_moderate(self):
        """Level returns 'Modéré' for score >= 40."""
        score = MemberEngagementScoreFactory(total_score=55)
        assert score.level == 'Modéré'

    def test_level_low(self):
        """Level returns 'Faible' for score >= 20."""
        score = MemberEngagementScoreFactory(total_score=25)
        assert score.level == 'Faible'

    def test_one_to_one_with_member(self):
        """Each member can have only one engagement score."""
        member = MemberFactory()
        MemberEngagementScoreFactory(member=member)
        with pytest.raises(Exception):
            MemberEngagementScoreFactory(member=member)


@pytest.mark.django_db
class TestEngagementScoreService:
    """Tests for EngagementScoreService."""

    def test_calculate_for_member(self):
        """Calculate engagement score for a single member."""
        from apps.members.services_engagement import EngagementScoreService
        member = MemberFactory()
        GroupMembershipFactory(member=member)
        score = EngagementScoreService.calculate_for_member(member)
        assert score is not None
        assert score.total_score >= 0
        assert score.member == member

    def test_calculate_for_member_updates(self):
        """Recalculating updates existing score."""
        from apps.members.services_engagement import EngagementScoreService
        member = MemberFactory()
        score1 = EngagementScoreService.calculate_for_member(member)
        score2 = EngagementScoreService.calculate_for_member(member)
        assert score1.pk == score2.pk

    def test_calculate_for_all(self):
        """Calculate scores for all active members."""
        from apps.members.services_engagement import EngagementScoreService
        MemberFactory()
        MemberFactory()
        scores = EngagementScoreService.calculate_for_all()
        assert len(scores) >= 2

    def test_group_score_component(self):
        """Group score increases with group memberships."""
        from apps.members.services_engagement import EngagementScoreService
        member_no_groups = MemberFactory()
        member_with_groups = MemberFactory()
        GroupMembershipFactory(member=member_with_groups)
        GroupMembershipFactory(member=member_with_groups)

        score_no = EngagementScoreService.calculate_for_member(member_no_groups)
        score_with = EngagementScoreService.calculate_for_member(member_with_groups)
        assert score_with.group_score >= score_no.group_score


@pytest.fixture(autouse=True)
def _setup_templates(settings, tmp_path):
    """Create minimal template stubs."""
    members_dir = tmp_path / 'members'
    members_dir.mkdir()
    template_names = [
        'engagement_dashboard.html',
    ]
    for name in template_names:
        (members_dir / name).write_text('{{ page_title|default:"test" }}')
    settings.TEMPLATES = [
        {
            **settings.TEMPLATES[0],
            'DIRS': [str(tmp_path)] + [
                str(d) for d in settings.TEMPLATES[0].get('DIRS', [])
            ],
        }
    ]


@pytest.fixture
def staff_user():
    """Staff member with linked user account."""
    user = UserFactory()
    member = PastorFactory(user=user)
    return user, member


@pytest.fixture
def admin_user():
    """Admin member with linked user account."""
    user = UserFactory()
    member = AdminMemberFactory(user=user)
    return user, member


@pytest.fixture
def regular_user():
    """Regular member with linked user account."""
    user = UserFactory()
    member = MemberFactory(user=user, role=Roles.MEMBER)
    return user, member


@pytest.mark.django_db
class TestEngagementViews:
    """Tests for engagement views."""

    def test_dashboard_staff(self, client, staff_user):
        """Staff can view engagement dashboard."""
        user, member = staff_user
        MemberEngagementScoreFactory()
        client.force_login(user)
        response = client.get('/members/engagement/')
        assert response.status_code == 200

    def test_dashboard_denied_regular(self, client, regular_user):
        """Non-staff redirected from engagement dashboard."""
        user, member = regular_user
        client.force_login(user)
        response = client.get('/members/engagement/')
        assert response.status_code == 302

    def test_recalculate(self, client, admin_user):
        """Admin can trigger recalculation."""
        user, member = admin_user
        MemberFactory()
        client.force_login(user)
        response = client.post('/members/engagement/recalculate/')
        assert response.status_code == 302

    def test_recalculate_denied_regular(self, client, regular_user):
        """Non-admin redirected from recalculate."""
        user, member = regular_user
        client.force_login(user)
        response = client.post('/members/engagement/recalculate/')
        assert response.status_code == 302
