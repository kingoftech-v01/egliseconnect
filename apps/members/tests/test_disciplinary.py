"""Tests for disciplinary action system: service, views."""
import pytest
from datetime import date

from apps.core.constants import (
    Roles, DisciplinaryType, ApprovalStatus, MembershipStatus,
)
from apps.communication.models import Notification
from apps.members.models import DisciplinaryAction
from apps.members.services import DisciplinaryService
from apps.members.tests.factories import (
    MemberFactory, PastorFactory, AdminMemberFactory,
    DeaconFactory, MemberWithUserFactory, UserFactory,
    DisciplinaryActionFactory,
)


# ==============================================================================
# Service tests
# ==============================================================================


@pytest.mark.django_db
class TestDisciplinaryServiceHierarchy:
    """Tests for hierarchy enforcement."""

    def test_pastor_can_discipline_deacon(self):
        pastor = PastorFactory()
        deacon = DeaconFactory()
        assert DisciplinaryService.can_discipline(pastor, deacon) is True

    def test_pastor_can_discipline_member(self):
        pastor = PastorFactory()
        member = MemberFactory(role=Roles.MEMBER)
        assert DisciplinaryService.can_discipline(pastor, member) is True

    def test_deacon_can_discipline_volunteer(self):
        deacon = DeaconFactory()
        volunteer = MemberFactory(role=Roles.VOLUNTEER)
        assert DisciplinaryService.can_discipline(deacon, volunteer) is True

    def test_member_cannot_discipline(self):
        member = MemberFactory(role=Roles.MEMBER)
        target = MemberFactory(role=Roles.VOLUNTEER)
        assert DisciplinaryService.can_discipline(member, target) is False

    def test_same_role_cannot_discipline(self):
        p1 = PastorFactory()
        p2 = PastorFactory()
        assert DisciplinaryService.can_discipline(p1, p2) is False

    def test_lower_cannot_discipline_higher(self):
        deacon = DeaconFactory()
        pastor = PastorFactory()
        assert DisciplinaryService.can_discipline(deacon, pastor) is False

    def test_admin_can_discipline_pastor(self):
        admin = AdminMemberFactory()
        pastor = PastorFactory()
        assert DisciplinaryService.can_discipline(admin, pastor) is True


@pytest.mark.django_db
class TestDisciplinaryServiceApproval:
    """Tests for approval logic."""

    def test_can_approve_different_person(self):
        pastor = PastorFactory()
        deacon = DeaconFactory()
        action = DisciplinaryActionFactory(created_by=deacon, member=MemberFactory())
        assert DisciplinaryService.can_approve(pastor, action) is True

    def test_cannot_approve_own_action(self):
        pastor = PastorFactory()
        action = DisciplinaryActionFactory(created_by=pastor, member=MemberFactory())
        assert DisciplinaryService.can_approve(pastor, action) is False

    def test_deacon_cannot_approve(self):
        deacon = DeaconFactory()
        pastor = PastorFactory()
        action = DisciplinaryActionFactory(created_by=pastor, member=MemberFactory())
        assert DisciplinaryService.can_approve(deacon, action) is False


@pytest.mark.django_db
class TestDisciplinaryServiceCreateAction:
    """Tests for create_action."""

    def test_create_action(self):
        pastor = PastorFactory()
        member = MemberFactory()
        action = DisciplinaryService.create_action(
            actor=pastor,
            target=member,
            action_type=DisciplinaryType.PUNISHMENT,
            reason='Comportement inapproprié',
            start_date=date.today(),
        )
        assert action.id is not None
        assert action.approval_status == ApprovalStatus.PENDING
        assert action.created_by == pastor

    def test_create_action_notifies_admins(self):
        admin = AdminMemberFactory()
        pastor = PastorFactory()
        member = MemberFactory()
        DisciplinaryService.create_action(
            actor=pastor,
            target=member,
            action_type=DisciplinaryType.SUSPENSION,
            reason='Absence prolongée',
            start_date=date.today(),
        )
        assert Notification.objects.filter(
            member=admin,
            title='Action disciplinaire à approuver',
        ).exists()

    def test_create_action_unauthorized_raises(self):
        member1 = MemberFactory(role=Roles.MEMBER)
        member2 = MemberFactory(role=Roles.MEMBER)
        with pytest.raises(ValueError, match='autorité'):
            DisciplinaryService.create_action(
                actor=member1,
                target=member2,
                action_type=DisciplinaryType.PUNISHMENT,
                reason='Test',
                start_date=date.today(),
            )


@pytest.mark.django_db
class TestDisciplinaryServiceApproveAction:
    """Tests for approve_action."""

    def test_approve(self):
        deacon = DeaconFactory()
        member = MemberFactory()
        action = DisciplinaryService.create_action(
            actor=deacon, target=member,
            action_type=DisciplinaryType.PUNISHMENT,
            reason='Test', start_date=date.today(),
        )
        pastor = PastorFactory()
        DisciplinaryService.approve_action(pastor, action)
        action.refresh_from_db()
        assert action.approval_status == ApprovalStatus.APPROVED
        assert action.approved_by == pastor

    def test_approve_suspension_auto_suspends_member(self):
        deacon = DeaconFactory()
        member = MemberFactory(membership_status=MembershipStatus.ACTIVE)
        action = DisciplinaryService.create_action(
            actor=deacon, target=member,
            action_type=DisciplinaryType.SUSPENSION,
            reason='Test', start_date=date.today(),
            auto_suspend=True,
        )
        pastor = PastorFactory()
        DisciplinaryService.approve_action(pastor, action)
        member.refresh_from_db()
        assert member.membership_status == MembershipStatus.SUSPENDED

    def test_approve_unauthorized_raises(self):
        deacon = DeaconFactory()
        member = MemberFactory()
        action = DisciplinaryActionFactory(
            created_by=deacon, member=member,
            approval_status=ApprovalStatus.PENDING,
        )
        with pytest.raises(ValueError, match='autorité'):
            DisciplinaryService.approve_action(deacon, action)

    def test_reject(self):
        deacon = DeaconFactory()
        member = MemberFactory()
        action = DisciplinaryService.create_action(
            actor=deacon, target=member,
            action_type=DisciplinaryType.PUNISHMENT,
            reason='Test', start_date=date.today(),
        )
        pastor = PastorFactory()
        DisciplinaryService.reject_action(pastor, action)
        action.refresh_from_db()
        assert action.approval_status == ApprovalStatus.REJECTED


@pytest.mark.django_db
class TestDisciplinaryServiceLift:
    """Tests for lift_suspension."""

    def test_lift_suspension(self):
        deacon = DeaconFactory()
        member = MemberFactory(membership_status=MembershipStatus.SUSPENDED)
        action = DisciplinaryActionFactory(
            created_by=deacon, member=member,
            action_type=DisciplinaryType.SUSPENSION,
            approval_status=ApprovalStatus.APPROVED,
        )
        pastor = PastorFactory()
        DisciplinaryService.lift_suspension(pastor, action)
        member.refresh_from_db()
        assert member.membership_status == MembershipStatus.ACTIVE
        action.refresh_from_db()
        assert action.end_date is not None

    def test_lift_non_suspension_raises(self):
        action = DisciplinaryActionFactory(
            action_type=DisciplinaryType.PUNISHMENT,
            approval_status=ApprovalStatus.APPROVED,
        )
        pastor = PastorFactory()
        with pytest.raises(ValueError, match='suspension'):
            DisciplinaryService.lift_suspension(pastor, action)

    def test_lift_unapproved_raises(self):
        action = DisciplinaryActionFactory(
            action_type=DisciplinaryType.SUSPENSION,
            approval_status=ApprovalStatus.PENDING,
        )
        pastor = PastorFactory()
        with pytest.raises(ValueError, match='approuvée'):
            DisciplinaryService.lift_suspension(pastor, action)


# ==============================================================================
# View tests
# ==============================================================================


def _staff_login(client, role=Roles.PASTOR):
    """Create a staff member and log them in."""
    if role == Roles.PASTOR:
        member = PastorFactory()
    elif role == Roles.ADMIN:
        member = AdminMemberFactory()
    else:
        member = DeaconFactory()
    user = UserFactory()
    member.user = user
    member.save()
    client.force_login(user)
    return member


@pytest.mark.django_db
class TestDisciplinaryListView:
    """Tests for disciplinary_list view."""

    def test_staff_can_view(self, client):
        _staff_login(client)
        response = client.get('/members/disciplinary/')
        assert response.status_code == 200

    def test_non_staff_denied(self, client):
        member = MemberWithUserFactory(role=Roles.MEMBER)
        client.force_login(member.user)
        response = client.get('/members/disciplinary/')
        assert response.status_code == 302

    def test_filter_by_status(self, client):
        _staff_login(client)
        response = client.get('/members/disciplinary/?status=pending')
        assert response.status_code == 200


@pytest.mark.django_db
class TestDisciplinaryCreateView:
    """Tests for disciplinary_create view."""

    def test_get_form(self, client):
        _staff_login(client)
        response = client.get('/members/disciplinary/create/')
        assert response.status_code == 200

    def test_post_valid(self, client):
        pastor = _staff_login(client)
        member = MemberFactory(role=Roles.MEMBER)
        response = client.post('/members/disciplinary/create/', {
            'member': str(member.pk),
            'action_type': DisciplinaryType.PUNISHMENT,
            'reason': 'Test motif',
            'start_date': '2026-02-07',
            'auto_suspend_membership': True,
        })
        assert response.status_code == 302
        assert DisciplinaryAction.objects.count() == 1

    def test_non_staff_denied(self, client):
        member = MemberWithUserFactory(role=Roles.MEMBER)
        client.force_login(member.user)
        response = client.get('/members/disciplinary/create/')
        assert response.status_code == 302


@pytest.mark.django_db
class TestDisciplinaryDetailView:
    """Tests for disciplinary_detail view."""

    def test_get(self, client):
        _staff_login(client)
        action = DisciplinaryActionFactory()
        response = client.get(f'/members/disciplinary/{action.pk}/')
        assert response.status_code == 200


@pytest.mark.django_db
class TestDisciplinaryApproveView:
    """Tests for disciplinary_approve view."""

    def test_approve(self, client):
        pastor = _staff_login(client)
        deacon = DeaconFactory()
        member = MemberFactory()
        action = DisciplinaryService.create_action(
            actor=deacon, target=member,
            action_type=DisciplinaryType.PUNISHMENT,
            reason='Test', start_date=date.today(),
        )
        response = client.post(f'/members/disciplinary/{action.pk}/approve/', {
            'decision': 'approve',
        })
        assert response.status_code == 302
        action.refresh_from_db()
        assert action.approval_status == ApprovalStatus.APPROVED

    def test_reject(self, client):
        pastor = _staff_login(client)
        deacon = DeaconFactory()
        member = MemberFactory()
        action = DisciplinaryService.create_action(
            actor=deacon, target=member,
            action_type=DisciplinaryType.PUNISHMENT,
            reason='Test', start_date=date.today(),
        )
        response = client.post(f'/members/disciplinary/{action.pk}/approve/', {
            'decision': 'reject',
        })
        assert response.status_code == 302
        action.refresh_from_db()
        assert action.approval_status == ApprovalStatus.REJECTED

    def test_non_pastor_denied(self, client):
        member = MemberWithUserFactory(role=Roles.MEMBER)
        client.force_login(member.user)
        action = DisciplinaryActionFactory()
        response = client.post(f'/members/disciplinary/{action.pk}/approve/', {
            'decision': 'approve',
        })
        assert response.status_code == 302  # Redirect with error
