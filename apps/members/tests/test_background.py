"""Tests for BackgroundCheck model and views."""
import pytest
from datetime import date, timedelta

from apps.core.constants import Roles, BackgroundCheckStatus
from apps.members.models import BackgroundCheck

from .factories import (
    UserFactory,
    MemberFactory,
    PastorFactory,
    BackgroundCheckFactory,
)


@pytest.mark.django_db
class TestBackgroundCheckModel:
    """Tests for BackgroundCheck model."""

    def test_create_background_check(self):
        """BackgroundCheck creation with required fields."""
        check = BackgroundCheckFactory()
        assert check.id is not None
        assert check.status == BackgroundCheckStatus.PENDING

    def test_str(self):
        """String representation includes member name and status."""
        check = BackgroundCheckFactory()
        assert check.member.full_name in str(check)

    def test_is_expired_true(self):
        """is_expired returns True when expiry_date is past."""
        check = BackgroundCheckFactory(
            expiry_date=date.today() - timedelta(days=1),
            status=BackgroundCheckStatus.APPROVED,
        )
        assert check.is_expired is True

    def test_is_expired_false_future(self):
        """is_expired returns False when expiry_date is in the future."""
        check = BackgroundCheckFactory(
            expiry_date=date.today() + timedelta(days=30),
        )
        assert check.is_expired is False

    def test_is_expired_false_no_date(self):
        """is_expired returns False when no expiry_date."""
        check = BackgroundCheckFactory(expiry_date=None)
        assert check.is_expired is False

    def test_days_until_expiry(self):
        """days_until_expiry returns correct number."""
        check = BackgroundCheckFactory(
            expiry_date=date.today() + timedelta(days=15),
        )
        assert check.days_until_expiry == 15

    def test_days_until_expiry_negative(self):
        """days_until_expiry returns negative when expired."""
        check = BackgroundCheckFactory(
            expiry_date=date.today() - timedelta(days=5),
        )
        assert check.days_until_expiry == -5

    def test_days_until_expiry_none(self):
        """days_until_expiry returns None when no expiry_date."""
        check = BackgroundCheckFactory(expiry_date=None)
        assert check.days_until_expiry is None


@pytest.fixture(autouse=True)
def _setup_templates(settings, tmp_path):
    """Create minimal template stubs."""
    members_dir = tmp_path / 'members'
    members_dir.mkdir()
    template_names = [
        'background_check_list.html',
        'background_check_form.html',
        'background_check_detail.html',
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
class TestBackgroundCheckViews:
    """Tests for background check views."""

    def test_list_staff(self, client, staff_user):
        """Staff can view background check list."""
        user, member = staff_user
        BackgroundCheckFactory()
        client.force_login(user)
        response = client.get('/members/background-checks/')
        assert response.status_code == 200

    def test_list_denied_regular(self, client, regular_user):
        """Non-staff redirected from background check list."""
        user, member = regular_user
        client.force_login(user)
        response = client.get('/members/background-checks/')
        assert response.status_code == 302

    def test_create_get(self, client, staff_user):
        """Staff can access creation form."""
        user, member = staff_user
        client.force_login(user)
        response = client.get('/members/background-checks/create/')
        assert response.status_code == 200

    def test_create_post(self, client, staff_user):
        """Staff can create a background check."""
        user, member = staff_user
        target = MemberFactory()
        client.force_login(user)
        response = client.post('/members/background-checks/create/', data={
            'member': str(target.pk),
            'status': BackgroundCheckStatus.PENDING,
            'check_date': date.today().isoformat(),
            'provider': 'Test Provider',
        })
        assert response.status_code == 302
        assert BackgroundCheck.objects.filter(member=target).exists()

    def test_detail(self, client, staff_user):
        """Staff can view background check detail."""
        user, member = staff_user
        check = BackgroundCheckFactory()
        client.force_login(user)
        response = client.get(f'/members/background-checks/{check.pk}/')
        assert response.status_code == 200

    def test_edit(self, client, staff_user):
        """Staff can edit a background check."""
        user, member = staff_user
        check = BackgroundCheckFactory(provider='Original')
        client.force_login(user)
        response = client.post(f'/members/background-checks/{check.pk}/edit/', data={
            'member': str(check.member.pk),
            'status': BackgroundCheckStatus.APPROVED,
            'check_date': check.check_date.isoformat(),
            'provider': 'Updated Provider',
        })
        assert response.status_code == 302
        check.refresh_from_db()
        assert check.provider == 'Updated Provider'

    def test_list_filter_status(self, client, staff_user):
        """Background check list can be filtered by status."""
        user, member = staff_user
        BackgroundCheckFactory(status=BackgroundCheckStatus.PENDING)
        BackgroundCheckFactory(status=BackgroundCheckStatus.APPROVED)
        client.force_login(user)
        response = client.get('/members/background-checks/?status=pending')
        assert response.status_code == 200
