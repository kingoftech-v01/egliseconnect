"""Business logic for member management including disciplinary actions."""
from django.utils import timezone

from apps.core.constants import (
    Roles, MembershipStatus, DisciplinaryType, ApprovalStatus,
)
from apps.communication.models import Notification


class DisciplinaryService:
    """Manages disciplinary actions with hierarchy enforcement."""

    # Role hierarchy: higher index = more authority
    HIERARCHY = Roles.HIERARCHY  # [MEMBER, VOLUNTEER, GROUP_LEADER, DEACON, TREASURER, PASTOR, ADMIN]

    @classmethod
    def _role_level(cls, role):
        """Get the hierarchy level of a role."""
        try:
            return cls.HIERARCHY.index(role)
        except ValueError:
            return 0

    @classmethod
    def can_discipline(cls, actor, target):
        """
        Check if actor can create a disciplinary action against target.
        Rules:
        - Only DEACON, PASTOR, ADMIN can create actions
        - Actor must have strictly higher hierarchy than target
        - ADMIN can discipline anyone except other ADMINs
        """
        actor_level = cls._role_level(actor.role)
        target_level = cls._role_level(target.role)

        if actor.role not in Roles.STAFF_ROLES:
            return False

        if actor_level <= target_level:
            return False

        return True

    @classmethod
    def can_approve(cls, approver, action):
        """
        Check if approver can approve a disciplinary action.
        Rules:
        - Approver must be different from creator
        - Approver must be at least at PASTOR level
        - Approver must have >= hierarchy than creator
        """
        if approver.pk == action.created_by.pk:
            return False

        approver_level = cls._role_level(approver.role)
        if approver_level < cls._role_level(Roles.PASTOR):
            return False

        return True

    @classmethod
    def create_action(cls, actor, target, action_type, reason,
                      start_date, end_date=None, notes='',
                      auto_suspend=True):
        """Create a disciplinary action if hierarchy allows it."""
        from .models import DisciplinaryAction

        if not cls.can_discipline(actor, target):
            raise ValueError(
                'Vous n\'avez pas l\'autorité pour cette action disciplinaire.'
            )

        action = DisciplinaryAction.objects.create(
            member=target,
            action_type=action_type,
            reason=reason,
            start_date=start_date,
            end_date=end_date,
            created_by=actor,
            auto_suspend_membership=auto_suspend,
            notes=notes,
            approval_status=ApprovalStatus.PENDING,
        )

        # Notify pastors/admins for approval
        from .models import Member
        approvers = Member.objects.filter(
            role__in=[Roles.PASTOR, Roles.ADMIN],
            is_active=True,
        ).exclude(pk=actor.pk)

        for approver in approvers:
            Notification.objects.create(
                member=approver,
                title='Action disciplinaire à approuver',
                message=(
                    f'{actor.full_name} a créé une {action.get_action_type_display()} '
                    f'contre {target.full_name}. Motif: {reason[:100]}'
                ),
                notification_type='general',
                link=f'/members/disciplinary/{action.pk}/',
            )

        return action

    @classmethod
    def approve_action(cls, approver, action):
        """Approve a pending disciplinary action."""
        if not cls.can_approve(approver, action):
            raise ValueError(
                'Vous n\'avez pas l\'autorité pour approuver cette action.'
            )

        action.approval_status = ApprovalStatus.APPROVED
        action.approved_by = approver
        action.save(update_fields=['approval_status', 'approved_by', 'updated_at'])

        # Auto-suspend if flagged
        if action.auto_suspend_membership and action.action_type == DisciplinaryType.SUSPENSION:
            member = action.member
            member.membership_status = MembershipStatus.SUSPENDED
            member.save(update_fields=['membership_status', 'updated_at'])

            Notification.objects.create(
                member=member,
                title='Compte suspendu',
                message=(
                    f'Votre compte a été suspendu. Motif: {action.reason[:200]}'
                ),
                notification_type='general',
            )

        # Notify creator
        Notification.objects.create(
            member=action.created_by,
            title='Action disciplinaire approuvée',
            message=(
                f'L\'action disciplinaire contre {action.member.full_name} '
                f'a été approuvée par {approver.full_name}.'
            ),
            notification_type='general',
        )

        return action

    @classmethod
    def reject_action(cls, approver, action):
        """Reject a pending disciplinary action."""
        if not cls.can_approve(approver, action):
            raise ValueError(
                'Vous n\'avez pas l\'autorité pour rejeter cette action.'
            )

        action.approval_status = ApprovalStatus.REJECTED
        action.approved_by = approver
        action.save(update_fields=['approval_status', 'approved_by', 'updated_at'])

        Notification.objects.create(
            member=action.created_by,
            title='Action disciplinaire rejetée',
            message=(
                f'L\'action disciplinaire contre {action.member.full_name} '
                f'a été rejetée par {approver.full_name}.'
            ),
            notification_type='general',
        )

        return action

    @classmethod
    def lift_suspension(cls, actor, action):
        """Lift a suspension and reactivate the member."""
        member = action.member

        if action.action_type != DisciplinaryType.SUSPENSION:
            raise ValueError('Seule une suspension peut être levée.')

        if action.approval_status != ApprovalStatus.APPROVED:
            raise ValueError('L\'action n\'est pas approuvée.')

        action.end_date = timezone.now().date()
        action.save(update_fields=['end_date', 'updated_at'])

        if member.membership_status == MembershipStatus.SUSPENDED:
            member.membership_status = MembershipStatus.ACTIVE
            member.save(update_fields=['membership_status', 'updated_at'])

        Notification.objects.create(
            member=member,
            title='Suspension levée',
            message='Votre suspension a été levée. Votre compte est de nouveau actif.',
            notification_type='general',
        )

        return action
