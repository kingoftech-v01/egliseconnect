"""Tests for crisis response models and views."""
import pytest

from apps.help_requests.models import CrisisProtocol, CrisisResource
from apps.members.tests.factories import MemberWithUserFactory, MemberFactory
from .factories import CrisisProtocolFactory, CrisisResourceFactory, CareTeamFactory, CareTeamMemberFactory


@pytest.mark.django_db
class TestCrisisProtocolModel:
    """Tests for CrisisProtocol model."""

    def test_create_protocol(self):
        protocol = CrisisProtocolFactory(title='Death Protocol')
        assert protocol.title == 'Death Protocol'
        assert protocol.is_active is True
        assert len(protocol.steps_json) == 3

    def test_protocol_str(self):
        protocol = CrisisProtocolFactory(title='Emergency Response')
        assert str(protocol) == 'Emergency Response'

    def test_protocol_types(self):
        protocol = CrisisProtocolFactory(protocol_type='hospitalization')
        assert protocol.protocol_type == 'hospitalization'


@pytest.mark.django_db
class TestCrisisResourceModel:
    """Tests for CrisisResource model."""

    def test_create_resource(self):
        resource = CrisisResourceFactory(title='Grief Support Line')
        assert resource.title == 'Grief Support Line'

    def test_resource_str(self):
        resource = CrisisResourceFactory(title='Crisis Hotline')
        assert str(resource) == 'Crisis Hotline'

    def test_resource_with_url(self):
        resource = CrisisResourceFactory(url='https://example.com')
        assert resource.url == 'https://example.com'


@pytest.mark.django_db
class TestCrisisProtocolListView:
    """Tests for crisis protocol list view."""

    def test_list_requires_pastor(self, client):
        member = MemberWithUserFactory(role='member')
        client.force_login(member.user)
        response = client.get('/help-requests/crisis/protocols/')
        assert response.status_code == 302

    def test_list_accessible_by_pastor(self, client):
        pastor = MemberWithUserFactory(role='pastor')
        client.force_login(pastor.user)
        response = client.get('/help-requests/crisis/protocols/')
        assert response.status_code == 200

    def test_list_shows_protocols(self, client):
        pastor = MemberWithUserFactory(role='pastor')
        client.force_login(pastor.user)
        CrisisProtocolFactory(title='Test Protocol')
        response = client.get('/help-requests/crisis/protocols/')
        assert response.status_code == 200


@pytest.mark.django_db
class TestCrisisProtocolCreateView:
    """Tests for creating crisis protocols."""

    def test_create_get(self, client):
        pastor = MemberWithUserFactory(role='pastor')
        client.force_login(pastor.user)
        response = client.get('/help-requests/crisis/protocols/create/')
        assert response.status_code == 200

    def test_create_post(self, client):
        pastor = MemberWithUserFactory(role='pastor')
        client.force_login(pastor.user)
        response = client.post('/help-requests/crisis/protocols/create/', {
            'title': 'New Protocol',
            'protocol_type': 'death',
            'steps_json': '["Step 1", "Step 2"]',
            'is_active': True,
        })
        assert response.status_code == 302
        assert CrisisProtocol.objects.filter(title='New Protocol').exists()


@pytest.mark.django_db
class TestCrisisProtocolDetailView:
    """Tests for crisis protocol detail view."""

    def test_detail_view(self, client):
        pastor = MemberWithUserFactory(role='pastor')
        client.force_login(pastor.user)
        protocol = CrisisProtocolFactory()
        response = client.get(f'/help-requests/crisis/protocols/{protocol.pk}/')
        assert response.status_code == 200


@pytest.mark.django_db
class TestCrisisResourceListView:
    """Tests for crisis resource list view."""

    def test_list_accessible_by_pastor(self, client):
        pastor = MemberWithUserFactory(role='pastor')
        client.force_login(pastor.user)
        response = client.get('/help-requests/crisis/resources/')
        assert response.status_code == 200


@pytest.mark.django_db
class TestCrisisResourceCreateView:
    """Tests for creating crisis resources."""

    def test_create_post(self, client):
        pastor = MemberWithUserFactory(role='pastor')
        client.force_login(pastor.user)
        response = client.post('/help-requests/crisis/resources/create/', {
            'title': 'New Resource',
            'description': 'A helpful resource',
            'contact_info': '514-555-1234',
            'url': 'https://example.com',
            'category': 'grief_support',
        })
        assert response.status_code == 302
        assert CrisisResource.objects.filter(title='New Resource').exists()


@pytest.mark.django_db
class TestCrisisNotifyView:
    """Tests for crisis notification broadcasting."""

    def test_notify_requires_pastor(self, client):
        member = MemberWithUserFactory(role='member')
        client.force_login(member.user)
        response = client.get('/help-requests/crisis/notify/')
        assert response.status_code == 302

    def test_notify_form_get(self, client):
        pastor = MemberWithUserFactory(role='pastor')
        client.force_login(pastor.user)
        response = client.get('/help-requests/crisis/notify/')
        assert response.status_code == 200

    def test_notify_post(self, client):
        pastor = MemberWithUserFactory(role='pastor')
        client.force_login(pastor.user)
        # Create a care team with a member
        team = CareTeamFactory()
        team_member = MemberFactory()
        CareTeamMemberFactory(team=team, member=team_member)

        response = client.post('/help-requests/crisis/notify/', {
            'title': 'Emergency Alert',
            'message': 'Please respond immediately.',
        })
        assert response.status_code == 302
