"""Business logic for the onboarding lifecycle."""
import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from apps.core.constants import MembershipStatus, InterviewStatus, LessonStatus, Roles
from apps.communication.models import Notification

logger = logging.getLogger(__name__)


class OnboardingService:
    """Manages all membership lifecycle transitions."""

    @staticmethod
    def initialize_onboarding(member):
        """Set up a newly registered member with QR code and form deadline."""
        from apps.attendance.models import MemberQRCode

        deadline_days = getattr(settings, 'ONBOARDING_FORM_DEADLINE_DAYS', 30)
        member.membership_status = MembershipStatus.REGISTERED
        member.registration_date = timezone.now()
        member.form_deadline = timezone.now() + timedelta(days=deadline_days)
        member.save(update_fields=[
            'membership_status', 'registration_date', 'form_deadline', 'updated_at'
        ])

        MemberQRCode.objects.get_or_create(member=member)

        Notification.objects.create(
            member=member,
            title='Bienvenue sur ÉgliseConnect!',
            message=(
                f'Votre compte a été créé. Vous avez {deadline_days} jours '
                'pour remplir votre formulaire d\'adhésion.'
            ),
            notification_type='general',
        )
        return member

    @staticmethod
    def submit_form(member):
        """Mark member form as submitted, notify admins."""
        from apps.members.models import Member

        member.membership_status = MembershipStatus.FORM_SUBMITTED
        member.form_submitted_at = timezone.now()
        member.save(update_fields=[
            'membership_status', 'form_submitted_at', 'updated_at'
        ])

        admins = Member.objects.filter(role__in=[Roles.ADMIN, Roles.PASTOR])
        for admin in admins:
            Notification.objects.create(
                member=admin,
                title='Nouveau formulaire à réviser',
                message=f'{member.full_name} a soumis son formulaire d\'adhésion.',
                notification_type='general',
                link=f'/onboarding/admin/review/{member.pk}/',
            )

    @staticmethod
    def admin_approve(member, admin_member, course):
        """Approve a member's form and assign a training course."""
        from .models import MemberTraining, ScheduledLesson

        member.membership_status = MembershipStatus.IN_TRAINING
        member.admin_reviewed_at = timezone.now()
        member.admin_reviewed_by = admin_member
        member.save(update_fields=[
            'membership_status', 'admin_reviewed_at', 'admin_reviewed_by', 'updated_at'
        ])

        training = MemberTraining.objects.create(
            member=member,
            course=course,
            assigned_by=admin_member,
        )

        # Create scheduled lessons from the course template
        for lesson in course.lessons.filter(is_active=True).order_by('order'):
            ScheduledLesson.objects.create(
                training=training,
                lesson=lesson,
                scheduled_date=timezone.now(),  # Admin will update dates later
                status=LessonStatus.UPCOMING,
            )

        Notification.objects.create(
            member=member,
            title='Votre parcours de formation est prêt!',
            message=(
                f'Vous êtes inscrit au parcours "{course.name}". '
                f'Consultez vos leçons dans votre tableau de bord.'
            ),
            notification_type='general',
            link='/onboarding/training/',
        )

        return training

    @staticmethod
    def admin_reject(member, admin_member, reason):
        """Reject a member's application."""
        member.membership_status = MembershipStatus.REJECTED
        member.admin_reviewed_at = timezone.now()
        member.admin_reviewed_by = admin_member
        member.rejection_reason = reason
        member.save(update_fields=[
            'membership_status', 'admin_reviewed_at',
            'admin_reviewed_by', 'rejection_reason', 'updated_at'
        ])

        Notification.objects.create(
            member=member,
            title='Résultat de votre demande',
            message=f'Votre demande d\'adhésion a été refusée. Raison: {reason}',
            notification_type='general',
        )

    @staticmethod
    def admin_request_changes(member, admin_member, message):
        """Ask the member to correct/complete their form."""
        member.membership_status = MembershipStatus.IN_REVIEW
        member.admin_reviewed_by = admin_member
        member.save(update_fields=[
            'membership_status', 'admin_reviewed_by', 'updated_at'
        ])

        Notification.objects.create(
            member=member,
            title='Complément requis pour votre formulaire',
            message=message,
            notification_type='general',
            link='/onboarding/form/',
        )

    @staticmethod
    def mark_lesson_attended(scheduled_lesson, marked_by):
        """Mark a lesson as completed via QR scan."""
        scheduled_lesson.status = LessonStatus.COMPLETED
        scheduled_lesson.attended_at = timezone.now()
        scheduled_lesson.marked_by = marked_by
        scheduled_lesson.save(update_fields=[
            'status', 'attended_at', 'marked_by', 'updated_at'
        ])

        training = scheduled_lesson.training
        if training.progress_percentage == 100:
            training.is_completed = True
            training.completed_at = timezone.now()
            training.save(update_fields=['is_completed', 'completed_at', 'updated_at'])

            # Notify admins that training is complete
            from apps.members.models import Member
            admins = Member.objects.filter(role__in=[Roles.ADMIN, Roles.PASTOR])
            for admin in admins:
                Notification.objects.create(
                    member=admin,
                    title='Formation complétée',
                    message=(
                        f'{training.member.full_name} a complété 100% de sa formation '
                        f'"{training.course.name}". Planifiez l\'interview.'
                    ),
                    notification_type='general',
                    link=f'/onboarding/admin/review/{training.member.pk}/',
                )

            Notification.objects.create(
                member=training.member,
                title='Formation complétée!',
                message=(
                    'Félicitations! Vous avez complété toutes vos leçons. '
                    'L\'administration va planifier votre interview finale.'
                ),
                notification_type='general',
            )

    @staticmethod
    def schedule_interview(member, training, interviewer, proposed_date, location=''):
        """Schedule the final interview."""
        from .models import Interview

        member.membership_status = MembershipStatus.INTERVIEW_SCHEDULED
        member.save(update_fields=['membership_status', 'updated_at'])

        interview = Interview.objects.create(
            member=member,
            training=training,
            interviewer=interviewer,
            proposed_date=proposed_date,
            location=location,
            status=InterviewStatus.PROPOSED,
        )

        Notification.objects.create(
            member=member,
            title='Interview planifiée',
            message=(
                f'Votre interview finale est proposée le '
                f'{proposed_date:%d/%m/%Y à %H:%M}. '
                f'Confirmez ou proposez une autre date.'
            ),
            notification_type='general',
            link='/onboarding/interview/',
        )

        return interview

    @staticmethod
    def member_accept_interview(interview):
        """Member accepts the proposed interview date."""
        interview.status = InterviewStatus.CONFIRMED
        interview.confirmed_date = interview.proposed_date
        interview.save(update_fields=['status', 'confirmed_date', 'updated_at'])

        Notification.objects.create(
            member=interview.interviewer,
            title='Interview confirmée',
            message=(
                f'{interview.member.full_name} a confirmé l\'interview du '
                f'{interview.confirmed_date:%d/%m/%Y à %H:%M}.'
            ),
            notification_type='general',
        )

    @staticmethod
    def member_counter_propose(interview, new_date):
        """Member proposes an alternative date."""
        interview.status = InterviewStatus.COUNTER
        interview.counter_proposed_date = new_date
        interview.save(update_fields=['status', 'counter_proposed_date', 'updated_at'])

        Notification.objects.create(
            member=interview.interviewer,
            title='Contre-proposition de date',
            message=(
                f'{interview.member.full_name} propose le '
                f'{new_date:%d/%m/%Y à %H:%M} pour son interview.'
            ),
            notification_type='general',
        )

    @staticmethod
    def admin_confirm_counter(interview):
        """Admin accepts the member's counter-proposed date."""
        interview.status = InterviewStatus.CONFIRMED
        interview.confirmed_date = interview.counter_proposed_date
        interview.save(update_fields=['status', 'confirmed_date', 'updated_at'])

        Notification.objects.create(
            member=interview.member,
            title='Date d\'interview confirmée',
            message=(
                f'Votre interview est confirmée pour le '
                f'{interview.confirmed_date:%d/%m/%Y à %H:%M}. '
                f'Cette date est DÉFINITIVE.'
            ),
            notification_type='general',
        )

    @staticmethod
    def complete_interview(interview, passed, notes=''):
        """Finalize the interview result."""
        interview.completed_at = timezone.now()
        interview.result_notes = notes
        member = interview.member

        if passed:
            interview.status = InterviewStatus.COMPLETED_PASS
            member.membership_status = MembershipStatus.ACTIVE
            member.became_active_at = timezone.now()
            member.joined_date = timezone.now().date()

            Notification.objects.create(
                member=member,
                title='Bienvenue dans la famille!',
                message=(
                    'Félicitations! Vous êtes maintenant membre officiel. '
                    'Votre tableau de bord complet est maintenant accessible.'
                ),
                notification_type='general',
                link='/reports/',
            )
        else:
            interview.status = InterviewStatus.COMPLETED_FAIL
            member.membership_status = MembershipStatus.REJECTED
            member.rejection_reason = notes

            Notification.objects.create(
                member=member,
                title='Résultat de votre interview',
                message=f'Votre interview n\'a pas été concluante. {notes}',
                notification_type='general',
            )

        interview.save()
        member.save()

    @staticmethod
    def mark_interview_no_show(interview):
        """Mark member as no-show for interview - definitive rejection."""
        interview.status = InterviewStatus.NO_SHOW
        interview.completed_at = timezone.now()
        interview.save(update_fields=['status', 'completed_at', 'updated_at'])

        member = interview.member
        member.membership_status = MembershipStatus.REJECTED
        member.rejection_reason = 'Absent à l\'interview finale sans justification.'
        member.save(update_fields=['membership_status', 'rejection_reason', 'updated_at'])

    @staticmethod
    def expire_overdue_members():
        """Expire accounts that didn't submit form within deadline."""
        from apps.members.models import Member

        expired = Member.objects.filter(
            membership_status__in=[
                MembershipStatus.REGISTERED,
                MembershipStatus.FORM_PENDING,
            ],
            form_deadline__lt=timezone.now()
        )
        count = expired.count()
        for member in expired:
            member.membership_status = MembershipStatus.EXPIRED
            member.is_active = False
            member.save(update_fields=['membership_status', 'is_active', 'updated_at'])
            logger.info(f'Expired member: {member.full_name} ({member.member_number})')
        return count
