"""Tests for Pastoral Care model, views, and tasks."""
import pytest
from datetime import date, timedelta

from apps.core.constants import Roles, CareType, CareStatus
from apps.members.models import PastoralCare

from .factories import (
    UserFactory,
    MemberFactory,
    PastorFactory,
    AdminMemberFactory,
    PastoralCareFactory,
)


@pytest.mark.django_db
class TestPastoralCareModel:
    """Tests for PastoralCare model."""

    def test_create_care(self):
        """Pastoral care creation with required fields."""
        care = PastoralCareFactory()
        assert care.id is not None
        assert care.care_type == CareType.HOME_VISIT

    def test_care_str(self):
        """String representation includes type and member name."""
        care = PastoralCareFactory()
        assert care.member.full_name in str(care)

    def test_is_overdue_true(self):
        """is_overdue returns True when follow-up date is past and still open."""
        care = PastoralCareFactory(
            follow_up_date=date.today() - timedelta(days=5),
            status=CareStatus.OPEN,
        )
        assert care.is_overdue is True

    def test_is_overdue_false_future(self):
        """is_overdue returns False when follow-up date is in the future."""
        care = PastoralCareFactory(
            follow_up_date=date.today() + timedelta(days=5),
            status=CareStatus.OPEN,
        )
        assert care.is_overdue is False

    def test_is_overdue_false_closed(self):
        """is_overdue returns False when case is closed."""
        care = PastoralCareFactory(
            follow_up_date=date.today() - timedelta(days=5),
            status=CareStatus.CLOSED,
        )
        assert care.is_overdue is False

    def test_is_overdue_false_no_date(self):
        """is_overdue returns False when no follow-up date."""
        care = PastoralCareFactory(follow_up_date=None)
        assert care.is_overdue is False

    def test_care_ordering(self):
        """Pastoral care ordered by date descending."""
        care1 = PastoralCareFactory(date=date.today() - timedelta(days=10))
        care2 = PastoralCareFactory(date=date.today())
        cares = list(PastoralCare.objects.all())
        assert cares[0] == care2
        assert cares[1] == care1


@pytest.fixture(autouse=True)
def _setup_templates(settings, tmp_path):
    """Create minimal template stubs."""
    members_dir = tmp_path / 'members'
    members_dir.mkdir()
    template_names = [
        'care_list.html',
        'care_form.html',
        'care_detail.html',
        'care_dashboard.html',
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
def regular_user():
    """Regular member with linked user account."""
    user = UserFactory()
    member = MemberFactory(user=user, role=Roles.MEMBER)
    return user, member


@pytest.mark.django_db
class TestPastoralCareViews:
    """Tests for pastoral care views."""

    def test_care_list_staff(self, client, staff_user):
        """Staff can view care list."""
        user, member = staff_user
        PastoralCareFactory()
        client.force_login(user)
        response = client.get('/members/care/')
        assert response.status_code == 200

    def test_care_list_denied_regular(self, client, regular_user):
        """Non-staff redirected from care list."""
        user, member = regular_user
        client.force_login(user)
        response = client.get('/members/care/')
        assert response.status_code == 302

    def test_care_create_get(self, client, staff_user):
        """Staff can access care creation form."""
        user, member = staff_user
        client.force_login(user)
        response = client.get('/members/care/create/')
        assert response.status_code == 200

    def test_care_create_post(self, client, staff_user):
        """Staff can create a care record."""
        user, member = staff_user
        target = MemberFactory()
        client.force_login(user)
        response = client.post('/members/care/create/', data={
            'member': str(target.pk),
            'care_type': CareType.COUNSELING,
            'assigned_to': str(member.pk),
            'date': date.today().isoformat(),
            'status': CareStatus.OPEN,
            'notes': 'Test care',
        })
        assert response.status_code == 302
        assert PastoralCare.objects.filter(member=target).exists()

    def test_care_detail(self, client, staff_user):
        """Staff can view care detail."""
        user, member = staff_user
        care = PastoralCareFactory()
        client.force_login(user)
        response = client.get(f'/members/care/{care.pk}/')
        assert response.status_code == 200

    def test_care_edit(self, client, staff_user):
        """Staff can edit a care record."""
        user, member = staff_user
        care = PastoralCareFactory(notes='Original')
        client.force_login(user)
        response = client.post(f'/members/care/{care.pk}/edit/', data={
            'member': str(care.member.pk),
            'care_type': care.care_type,
            'assigned_to': str(care.assigned_to.pk),
            'date': care.date.isoformat(),
            'status': CareStatus.FOLLOW_UP,
            'notes': 'Updated',
        })
        assert response.status_code == 302
        care.refresh_from_db()
        assert care.notes == 'Updated'

    def test_care_dashboard(self, client, staff_user):
        """Staff can view care dashboard."""
        user, member = staff_user
        PastoralCareFactory(assigned_to=member)
        client.force_login(user)
        response = client.get('/members/care/dashboard/')
        assert response.status_code == 200

    def test_care_list_filter_status(self, client, staff_user):
        """Care list can be filtered by status."""
        user, member = staff_user
        PastoralCareFactory(status=CareStatus.OPEN)
        PastoralCareFactory(status=CareStatus.CLOSED)
        client.force_login(user)
        response = client.get('/members/care/?status=open')
        assert response.status_code == 200
