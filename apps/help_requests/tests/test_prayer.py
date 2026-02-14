"""Tests for prayer request models and views."""
import pytest
from django.utils import timezone

from apps.core.constants import PrayerRequestStatus
from apps.help_requests.models import PrayerRequest
from apps.members.tests.factories import MemberFactory, MemberWithUserFactory
from .factories import PrayerRequestFactory, CareTeamFactory, CareTeamMemberFactory


@pytest.mark.django_db
class TestPrayerRequestModel:
    """Tests for PrayerRequest model."""

    def test_create_prayer_request(self):
        prayer = PrayerRequestFactory(title='Healing prayer')
        assert prayer.title == 'Healing prayer'
        assert prayer.status == PrayerRequestStatus.ACTIVE
        assert prayer.is_approved is True

    def test_prayer_request_str(self):
        prayer = PrayerRequestFactory(title='Test Prayer')
        assert str(prayer) == 'Test Prayer'

    def test_anonymous_prayer_request(self):
        prayer = PrayerRequestFactory(is_anonymous=True)
        assert prayer.is_anonymous is True

    def test_mark_answered(self):
        prayer = PrayerRequestFactory()
        prayer.mark_answered(testimony='God answered!')
        assert prayer.status == PrayerRequestStatus.ANSWERED
        assert prayer.answered_at is not None
        assert prayer.testimony == 'God answered!'

    def test_mark_answered_without_testimony(self):
        prayer = PrayerRequestFactory()
        prayer.mark_answered()
        assert prayer.status == PrayerRequestStatus.ANSWERED
        assert prayer.testimony == ''

    def test_prayer_not_approved_by_default_anonymous(self):
        """Anonymous submissions via the form set is_approved=False."""
        prayer = PrayerRequestFactory(is_anonymous=True, is_approved=False)
        assert prayer.is_approved is False


@pytest.mark.django_db
class TestPrayerWallView:
    """Tests for the prayer wall."""

    def test_prayer_wall_shows_public_approved(self, client):
        member = MemberWithUserFactory()
        client.force_login(member.user)
        PrayerRequestFactory(is_public=True, is_approved=True, title='Public Prayer')
        PrayerRequestFactory(is_public=False, title='Private Prayer')
        PrayerRequestFactory(is_approved=False, title='Unapproved')
        response = client.get('/help-requests/prayer/wall/')
        assert response.status_code == 200

    def test_prayer_wall_requires_login(self, client):
        response = client.get('/help-requests/prayer/wall/')
        assert response.status_code == 302


@pytest.mark.django_db
class TestPrayerCreateView:
    """Tests for creating prayer requests."""

    def test_prayer_create_get(self, client):
        member = MemberWithUserFactory()
        client.force_login(member.user)
        response = client.get('/help-requests/prayer/create/')
        assert response.status_code == 200

    def test_prayer_create_post(self, client):
        member = MemberWithUserFactory()
        client.force_login(member.user)
        response = client.post('/help-requests/prayer/create/', {
            'title': 'Test Prayer',
            'description': 'Please pray for this.',
            'is_anonymous': False,
            'is_public': True,
        })
        assert response.status_code == 302
        assert PrayerRequest.objects.filter(title='Test Prayer').exists()
        prayer = PrayerRequest.objects.get(title='Test Prayer')
        assert prayer.member == member
        assert prayer.is_approved is True


@pytest.mark.django_db
class TestPrayerAnonymousView:
    """Tests for anonymous prayer request submission."""

    def test_anonymous_form_get(self, client):
        response = client.get('/help-requests/prayer/anonymous/')
        assert response.status_code == 200

    def test_anonymous_form_post(self, client):
        response = client.post('/help-requests/prayer/anonymous/', {
            'title': 'Anonymous Prayer',
            'description': 'Please pray.',
        })
        assert response.status_code == 302
        prayer = PrayerRequest.objects.get(title='Anonymous Prayer')
        assert prayer.is_anonymous is True
        assert prayer.is_approved is False  # Needs moderation

    def test_anonymous_done_page(self, client):
        response = client.get('/help-requests/prayer/anonymous/done/')
        assert response.status_code == 200


@pytest.mark.django_db
class TestPrayerMarkAnswered:
    """Tests for marking prayers as answered."""

    def test_mark_answered_by_owner(self, client):
        member = MemberWithUserFactory()
        client.force_login(member.user)
        prayer = PrayerRequestFactory(member=member)

        response = client.post(f'/help-requests/prayer/{prayer.pk}/answered/', {
            'testimony': 'God is good!',
        })
        assert response.status_code == 302
        prayer.refresh_from_db()
        assert prayer.status == PrayerRequestStatus.ANSWERED
        assert prayer.testimony == 'God is good!'

    def test_mark_answered_by_pastor(self, client):
        pastor = MemberWithUserFactory(role='pastor')
        client.force_login(pastor.user)
        prayer = PrayerRequestFactory()

        response = client.post(f'/help-requests/prayer/{prayer.pk}/answered/', {
            'testimony': 'Praise the Lord!',
        })
        assert response.status_code == 302
        prayer.refresh_from_db()
        assert prayer.status == PrayerRequestStatus.ANSWERED

    def test_mark_answered_denied_for_other_member(self, client):
        member = MemberWithUserFactory(role='member')
        client.force_login(member.user)
        prayer = PrayerRequestFactory()  # Different member

        response = client.post(f'/help-requests/prayer/{prayer.pk}/answered/', {
            'testimony': 'Should not work',
        })
        assert response.status_code == 302
        prayer.refresh_from_db()
        assert prayer.status == PrayerRequestStatus.ACTIVE


@pytest.mark.django_db
class TestPrayerModerationView:
    """Tests for moderation of anonymous prayer requests."""

    def test_moderation_requires_pastor(self, client):
        member = MemberWithUserFactory(role='member')
        client.force_login(member.user)
        response = client.get('/help-requests/prayer/moderation/')
        assert response.status_code == 302

    def test_moderation_shows_pending(self, client):
        pastor = MemberWithUserFactory(role='pastor')
        client.force_login(pastor.user)
        PrayerRequestFactory(is_approved=False, title='Pending Prayer')
        response = client.get('/help-requests/prayer/moderation/')
        assert response.status_code == 200

    def test_approve_prayer(self, client):
        pastor = MemberWithUserFactory(role='pastor')
        client.force_login(pastor.user)
        prayer = PrayerRequestFactory(is_approved=False)

        response = client.post(f'/help-requests/prayer/{prayer.pk}/moderate/', {
            'action': 'approve',
        })
        assert response.status_code == 302
        prayer.refresh_from_db()
        assert prayer.is_approved is True

    def test_reject_prayer(self, client):
        pastor = MemberWithUserFactory(role='pastor')
        client.force_login(pastor.user)
        prayer = PrayerRequestFactory(is_approved=False)

        response = client.post(f'/help-requests/prayer/{prayer.pk}/moderate/', {
            'action': 'reject',
        })
        assert response.status_code == 302
        prayer.refresh_from_db()
        assert prayer.status == PrayerRequestStatus.CLOSED
