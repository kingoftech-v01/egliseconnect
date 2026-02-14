"""Tests for benevolence fund models and views."""
import pytest
from django.utils import timezone

from apps.core.constants import BenevolenceStatus
from apps.help_requests.models import BenevolenceRequest, BenevolenceFund
from apps.members.tests.factories import MemberFactory, MemberWithUserFactory
from .factories import BenevolenceRequestFactory, BenevolenceFundFactory


@pytest.mark.django_db
class TestBenevolenceFundModel:
    """Tests for BenevolenceFund model."""

    def test_create_fund(self):
        fund = BenevolenceFundFactory(name='General Fund', total_balance=10000)
        assert fund.name == 'General Fund'
        assert fund.total_balance == 10000

    def test_fund_str(self):
        fund = BenevolenceFundFactory(name='Emergency Fund')
        assert str(fund) == 'Emergency Fund'


@pytest.mark.django_db
class TestBenevolenceRequestModel:
    """Tests for BenevolenceRequest model."""

    def test_create_request(self):
        req = BenevolenceRequestFactory(amount_requested=500)
        assert req.amount_requested == 500
        assert req.status == BenevolenceStatus.SUBMITTED

    def test_request_str(self):
        req = BenevolenceRequestFactory()
        assert str(req.member) in str(req)

    def test_approval_workflow(self):
        approver = MemberFactory(role='pastor')
        req = BenevolenceRequestFactory()

        # Review
        req.status = BenevolenceStatus.REVIEWING
        req.save()
        assert req.status == BenevolenceStatus.REVIEWING

        # Approve
        req.status = BenevolenceStatus.APPROVED
        req.approved_by = approver
        req.amount_granted = 400
        req.save()
        assert req.status == BenevolenceStatus.APPROVED
        assert req.approved_by == approver

        # Disburse
        req.status = BenevolenceStatus.DISBURSED
        req.disbursed_at = timezone.now()
        req.save()
        assert req.status == BenevolenceStatus.DISBURSED
        assert req.disbursed_at is not None


@pytest.mark.django_db
class TestBenevolenceListView:
    """Tests for benevolence list view."""

    def test_list_requires_pastor(self, client):
        member = MemberWithUserFactory(role='member')
        client.force_login(member.user)
        response = client.get('/help-requests/benevolence/')
        assert response.status_code == 302

    def test_list_accessible_by_pastor(self, client):
        pastor = MemberWithUserFactory(role='pastor')
        client.force_login(pastor.user)
        response = client.get('/help-requests/benevolence/')
        assert response.status_code == 200


@pytest.mark.django_db
class TestBenevolenceCreateView:
    """Tests for creating benevolence requests."""

    def test_create_get(self, client):
        member = MemberWithUserFactory()
        client.force_login(member.user)
        response = client.get('/help-requests/benevolence/create/')
        assert response.status_code == 200

    def test_create_post(self, client):
        member = MemberWithUserFactory()
        fund = BenevolenceFundFactory()
        client.force_login(member.user)
        response = client.post('/help-requests/benevolence/create/', {
            'fund': str(fund.pk),
            'amount_requested': '750.00',
            'reason': 'Need help with rent',
        })
        assert response.status_code == 302
        assert BenevolenceRequest.objects.filter(member=member).exists()


@pytest.mark.django_db
class TestBenevolenceApprovalView:
    """Tests for approving/denying benevolence requests."""

    def test_approve_request(self, client):
        pastor = MemberWithUserFactory(role='pastor')
        client.force_login(pastor.user)
        req = BenevolenceRequestFactory()

        response = client.post(f'/help-requests/benevolence/{req.pk}/approve/', {
            'action': 'approve',
            'amount_granted': '500.00',
        })
        assert response.status_code == 302
        req.refresh_from_db()
        assert req.status == BenevolenceStatus.APPROVED
        assert req.approved_by == pastor

    def test_deny_request(self, client):
        pastor = MemberWithUserFactory(role='pastor')
        client.force_login(pastor.user)
        req = BenevolenceRequestFactory()

        response = client.post(f'/help-requests/benevolence/{req.pk}/approve/', {
            'action': 'deny',
        })
        assert response.status_code == 302
        req.refresh_from_db()
        assert req.status == BenevolenceStatus.DENIED


@pytest.mark.django_db
class TestBenevolenceDisburseView:
    """Tests for disbursing benevolence funds."""

    def test_disburse(self, client):
        pastor = MemberWithUserFactory(role='pastor')
        client.force_login(pastor.user)
        fund = BenevolenceFundFactory(total_balance=5000)
        req = BenevolenceRequestFactory(
            fund=fund,
            status=BenevolenceStatus.APPROVED,
            amount_granted=500,
        )

        response = client.post(f'/help-requests/benevolence/{req.pk}/disburse/')
        assert response.status_code == 302
        req.refresh_from_db()
        assert req.status == BenevolenceStatus.DISBURSED
        assert req.disbursed_at is not None
        fund.refresh_from_db()
        assert fund.total_balance == 4500

    def test_cannot_disburse_unapproved(self, client):
        pastor = MemberWithUserFactory(role='pastor')
        client.force_login(pastor.user)
        req = BenevolenceRequestFactory(status=BenevolenceStatus.SUBMITTED)

        response = client.post(f'/help-requests/benevolence/{req.pk}/disburse/')
        assert response.status_code == 302
        req.refresh_from_db()
        assert req.status == BenevolenceStatus.SUBMITTED  # Unchanged
