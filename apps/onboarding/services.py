"""Business logic for the onboarding lifecycle."""
import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from apps.core.constants import (
    MembershipStatus, InterviewStatus, LessonStatus, Roles,
    MentorAssignmentStatus, AchievementTrigger, VisitorFollowUpStatus,
)
from apps.communication.models import Notification

logger = logging.getLogger(__name__)


class OnboardingService:
    """Manages all membership lifecycle transitions."""

    # ─── Existing methods ─────────────────────────────────────────────────

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
            title='Bienvenue sur EgliseConnect!',
            message=(
                f'Votre compte a ete cree. Vous avez {deadline_days} jours '
                'pour remplir votre formulaire d\'adhesion.'
            ),
            notification_type='general',
        )

        # Start welcome sequence if active
        OnboardingService._start_welcome_sequence(member)

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
                title='Nouveau formulaire a reviser',
                message=f'{member.full_name} a soumis son formulaire d\'adhesion.',
                notification_type='general',
                link=f'/onboarding/admin/review/{member.pk}/',
            )

        # Check achievements
        OnboardingService.check_achievements(member, AchievementTrigger.FORM_SUBMITTED)

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
            title='Votre parcours de formation est pret!',
            message=(
                f'Vous etes inscrit au parcours "{course.name}". '
                f'Consultez vos lecons dans votre tableau de bord.'
            ),
            notification_type='general',
            link='/onboarding/training/',
        )

        # Check achievements
        OnboardingService.check_achievements(member, AchievementTrigger.TRAINING_STARTED)

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
            title='Resultat de votre demande',
            message=f'Votre demande d\'adhesion a ete refusee. Raison: {reason}',
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
            title='Complement requis pour votre formulaire',
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
        member = training.member

        # Check lesson completion achievement
        OnboardingService.check_achievements(member, AchievementTrigger.LESSON_COMPLETED)

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
                    title='Formation completee',
                    message=(
                        f'{member.full_name} a complete 100% de sa formation '
                        f'"{training.course.name}". Planifiez l\'interview.'
                    ),
                    notification_type='general',
                    link=f'/onboarding/admin/review/{member.pk}/',
                )

            Notification.objects.create(
                member=member,
                title='Formation completee!',
                message=(
                    'Felicitations! Vous avez complete toutes vos lecons. '
                    'L\'administration va planifier votre interview finale.'
                ),
                notification_type='general',
            )

            # Check training completion achievement
            OnboardingService.check_achievements(member, AchievementTrigger.TRAINING_COMPLETED)

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
            title='Interview planifiee',
            message=(
                f'Votre interview finale est proposee le '
                f'{proposed_date:%d/%m/%Y a %H:%M}. '
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
            title='Interview confirmee',
            message=(
                f'{interview.member.full_name} a confirme l\'interview du '
                f'{interview.confirmed_date:%d/%m/%Y a %H:%M}.'
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
                f'{new_date:%d/%m/%Y a %H:%M} pour son interview.'
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
            title='Date d\'interview confirmee',
            message=(
                f'Votre interview est confirmee pour le '
                f'{interview.confirmed_date:%d/%m/%Y a %H:%M}. '
                f'Cette date est DEFINITIVE.'
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
                    'Felicitations! Vous etes maintenant membre officiel. '
                    'Votre tableau de bord complet est maintenant accessible.'
                ),
                notification_type='general',
                link='/reports/',
            )

            # Check achievements
            OnboardingService.check_achievements(member, AchievementTrigger.INTERVIEW_PASSED)
            OnboardingService.check_achievements(member, AchievementTrigger.BECAME_ACTIVE)
        else:
            interview.status = InterviewStatus.COMPLETED_FAIL
            member.membership_status = MembershipStatus.REJECTED
            member.rejection_reason = notes

            # P3 item 48: Notify member about interview outcome
            Notification.objects.create(
                member=member,
                title='Resultat de votre interview',
                message=f'Votre interview n\'a pas ete concluante. {notes}',
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
        member.rejection_reason = 'Absent a l\'interview finale sans justification.'
        member.save(update_fields=['membership_status', 'rejection_reason', 'updated_at'])

    @staticmethod
    def create_invitation(created_by, role=None, expires_in_days=30,
                          max_uses=1, skip_onboarding=False, note=''):
        """Create a new invitation code."""
        from .models import InvitationCode

        if role is None:
            role = Roles.MEMBER

        invitation = InvitationCode.objects.create(
            created_by=created_by,
            role=role,
            expires_at=timezone.now() + timedelta(days=expires_in_days),
            max_uses=max_uses,
            skip_onboarding=skip_onboarding,
            note=note,
        )
        return invitation

    @staticmethod
    def accept_invitation(invitation, member):
        """Use an invitation code to assign role and optionally skip onboarding."""
        if not invitation.is_usable:
            raise ValueError('Ce code d\'invitation n\'est plus valide.')

        invitation.use_count += 1
        invitation.used_by = member
        invitation.used_at = timezone.now()

        if invitation.use_count >= invitation.max_uses:
            invitation.is_active = False

        invitation.save()

        # Assign the role via additional_roles if different from primary
        if invitation.role != member.role and invitation.role != Roles.MEMBER:
            from apps.members.models import MemberRole
            MemberRole.objects.get_or_create(
                member=member, role=invitation.role
            )

        # Skip onboarding if flagged (pre-existing members)
        if invitation.skip_onboarding:
            member.membership_status = MembershipStatus.ACTIVE
            member.became_active_at = timezone.now()
            member.joined_date = timezone.now().date()
            member.save(update_fields=[
                'membership_status', 'became_active_at', 'joined_date', 'updated_at'
            ])

            Notification.objects.create(
                member=member,
                title='Bienvenue!',
                message=(
                    f'Votre invitation a ete acceptee. '
                    f'Vous etes maintenant {invitation.get_role_display()}.'
                ),
                notification_type='general',
            )
        else:
            Notification.objects.create(
                member=member,
                title='Invitation acceptee',
                message=(
                    f'Votre invitation a ete acceptee avec le role '
                    f'{invitation.get_role_display()}. Poursuivez votre parcours.'
                ),
                notification_type='general',
            )

        return invitation

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

    # ─── P1: Mentor/Buddy Assignment (items 1-5) ─────────────────────────

    @staticmethod
    def assign_mentor(new_member, mentor, notes='', assigned_by=None):
        """Create a mentor assignment for a new member."""
        from .models import MentorAssignment

        assignment = MentorAssignment.objects.create(
            new_member=new_member,
            mentor=mentor,
            notes=notes,
        )

        Notification.objects.create(
            member=mentor,
            title='Nouveau mentorat assigne',
            message=(
                f'Vous etes assigne comme mentor pour {new_member.full_name}. '
                f'Contactez-le pour planifier votre premiere rencontre.'
            ),
            notification_type='general',
            link='/onboarding/mentor/dashboard/',
        )

        Notification.objects.create(
            member=new_member,
            title='Mentor assigne!',
            message=(
                f'{mentor.full_name} est votre mentor. '
                f'Il/elle vous accompagnera dans votre parcours.'
            ),
            notification_type='general',
            link='/onboarding/mentee/',
        )

        # Check achievements
        OnboardingService.check_achievements(new_member, AchievementTrigger.MENTOR_ASSIGNED)

        return assignment

    @staticmethod
    def log_mentor_checkin(assignment, notes, logged_by):
        """Log a check-in between mentor and mentee."""
        from .models import MentorCheckIn

        checkin = MentorCheckIn.objects.create(
            assignment=assignment,
            notes=notes,
            logged_by=logged_by,
        )

        assignment.check_in_count += 1
        assignment.save(update_fields=['check_in_count', 'updated_at'])

        return checkin

    @staticmethod
    def complete_mentor_assignment(assignment):
        """Mark a mentor assignment as completed."""
        assignment.status = MentorAssignmentStatus.COMPLETED
        assignment.save(update_fields=['status', 'updated_at'])

    # ─── P1: Welcome Sequence ────────────────────────────────────────────

    @staticmethod
    def _start_welcome_sequence(member):
        """Start the active welcome sequence for a new member."""
        from .models import WelcomeSequence, WelcomeProgress

        sequence = WelcomeSequence.objects.filter(is_active=True).first()
        if not sequence:
            return None

        progress, created = WelcomeProgress.objects.get_or_create(
            member=member,
            sequence=sequence,
            defaults={'current_step': 0},
        )
        return progress

    @staticmethod
    def advance_welcome_sequence(progress):
        """Advance a member to the next step in their welcome sequence."""
        steps = progress.sequence.steps.filter(is_active=True).order_by('order')
        step_list = list(steps)

        if progress.current_step >= len(step_list):
            # All steps completed
            progress.completed_at = timezone.now()
            progress.save(update_fields=['completed_at', 'updated_at'])
            return None

        step = step_list[progress.current_step]

        # Check if the member is ready for this step based on day_offset
        days_since_start = (timezone.now() - progress.started_at).days
        if days_since_start < step.day_offset:
            return None  # Not yet time for this step

        # Send the message
        body = step.body.replace('{{ member_name }}', progress.member.full_name)

        Notification.objects.create(
            member=progress.member,
            title=step.subject,
            message=body,
            notification_type='general',
        )

        progress.current_step += 1
        if progress.current_step >= len(step_list):
            progress.completed_at = timezone.now()
        progress.save(update_fields=['current_step', 'completed_at', 'updated_at'])

        return step

    # ─── P2: Estimated Completion Date (item 21) ─────────────────────────

    @staticmethod
    def estimate_completion_date(member):
        """Estimate when a member will complete onboarding based on avg pace."""
        from .models import MemberTraining
        from apps.members.models import Member

        # Get average completion days
        completed_members = Member.objects.filter(
            membership_status=MembershipStatus.ACTIVE,
            registration_date__isnull=False,
            became_active_at__isnull=False,
        )

        if not completed_members.exists():
            # Default estimate: 60 days
            if member.registration_date:
                return member.registration_date + timedelta(days=60)
            return timezone.now() + timedelta(days=60)

        total_days = 0
        count = 0
        for m in completed_members[:50]:  # Sample up to 50
            delta = m.became_active_at - m.registration_date
            total_days += delta.days
            count += 1

        avg_days = total_days / count if count > 0 else 60

        if member.registration_date:
            return member.registration_date + timedelta(days=int(avg_days))
        return timezone.now() + timedelta(days=int(avg_days))

    # ─── P2: What's Next Guidance (item 22) ──────────────────────────────

    @staticmethod
    def get_whats_next(member):
        """Return guidance text for the member's current onboarding stage."""
        status = member.membership_status

        guidance = {
            MembershipStatus.REGISTERED: {
                'title': 'Remplir votre formulaire',
                'description': 'Completez votre formulaire d\'adhesion pour continuer.',
                'action_url': '/onboarding/form/',
                'action_label': 'Remplir le formulaire',
                'icon': 'fas fa-file-alt',
            },
            MembershipStatus.FORM_PENDING: {
                'title': 'Remplir votre formulaire',
                'description': 'Completez votre formulaire d\'adhesion pour continuer.',
                'action_url': '/onboarding/form/',
                'action_label': 'Remplir le formulaire',
                'icon': 'fas fa-file-alt',
            },
            MembershipStatus.FORM_SUBMITTED: {
                'title': 'En attente de revision',
                'description': 'Votre formulaire est en cours d\'examen par l\'administration.',
                'action_url': None,
                'action_label': None,
                'icon': 'fas fa-hourglass-half',
            },
            MembershipStatus.IN_REVIEW: {
                'title': 'Complements requis',
                'description': 'L\'administration a demande des modifications a votre formulaire.',
                'action_url': '/onboarding/form/',
                'action_label': 'Modifier le formulaire',
                'icon': 'fas fa-edit',
            },
            MembershipStatus.IN_TRAINING: {
                'title': 'Suivre vos lecons',
                'description': 'Participez a vos lecons de formation pour progresser.',
                'action_url': '/onboarding/training/',
                'action_label': 'Voir ma formation',
                'icon': 'fas fa-graduation-cap',
            },
            MembershipStatus.INTERVIEW_SCHEDULED: {
                'title': 'Preparer votre interview',
                'description': 'Votre interview finale est planifiee. Confirmez la date.',
                'action_url': '/onboarding/interview/',
                'action_label': 'Voir mon interview',
                'icon': 'fas fa-comments',
            },
            MembershipStatus.ACTIVE: {
                'title': 'Bienvenue!',
                'description': 'Vous etes membre actif. Explorez votre tableau de bord.',
                'action_url': '/reports/',
                'action_label': 'Tableau de bord',
                'icon': 'fas fa-check-circle',
            },
        }

        return guidance.get(status, {
            'title': 'Votre parcours',
            'description': 'Consultez votre tableau de bord pour plus d\'informations.',
            'action_url': '/onboarding/dashboard/',
            'action_label': 'Tableau de bord',
            'icon': 'fas fa-info-circle',
        })

    # ─── P2: First-Time Visitor Detection (item 24) ─────────────────────

    @staticmethod
    def detect_first_time_visitors():
        """Detect attendance records without member profiles (visitors)."""
        from apps.attendance.models import AttendanceRecord

        # Find check-ins in the last 7 days where the member has no profile
        # This checks for members who attended but are still in early registration
        seven_days_ago = timezone.now() - timedelta(days=7)

        recent_first_visits = AttendanceRecord.objects.filter(
            checked_in_at__gte=seven_days_ago,
            member__registration_date__gte=seven_days_ago,
            member__membership_status=MembershipStatus.REGISTERED,
        ).select_related('member').values_list('member', flat=True).distinct()

        return list(recent_first_visits)

    # ─── P2: Visitor Follow-Up Trigger (item 25) ────────────────────────

    @staticmethod
    def create_visitor_followup(visitor_name, first_visit_date, email='', phone='', assigned_to=None):
        """Create a follow-up record for a first-time visitor."""
        from .models import VisitorFollowUp

        followup = VisitorFollowUp.objects.create(
            visitor_name=visitor_name,
            visitor_email=email,
            visitor_phone=phone,
            first_visit_date=first_visit_date,
            assigned_to=assigned_to,
        )

        if assigned_to:
            Notification.objects.create(
                member=assigned_to,
                title='Nouveau suivi de visiteur',
                message=f'Vous etes assigne au suivi de {visitor_name}.',
                notification_type='general',
                link='/onboarding/admin/visitors/',
            )

        return followup

    # ─── P2: Visitor-to-Member Conversion Stats (item 26) ───────────────

    @staticmethod
    def visitor_conversion_stats():
        """Calculate visitor-to-member conversion statistics."""
        from .models import VisitorFollowUp

        total = VisitorFollowUp.objects.count()
        converted = VisitorFollowUp.objects.filter(
            converted_at__isnull=False
        ).count()
        pending = VisitorFollowUp.objects.filter(
            status=VisitorFollowUpStatus.PENDING
        ).count()
        in_progress = VisitorFollowUp.objects.filter(
            status=VisitorFollowUpStatus.IN_PROGRESS
        ).count()

        return {
            'total_visitors': total,
            'converted': converted,
            'pending': pending,
            'in_progress': in_progress,
            'conversion_rate': round((converted / total) * 100, 1) if total > 0 else 0,
        }

    # ─── P3: Gamification — Achievement Checking (item 41) ──────────────

    @staticmethod
    def check_achievements(member, trigger_type):
        """Check if member has earned any achievements for a given trigger."""
        from .models import Achievement, MemberAchievement

        achievements = Achievement.objects.filter(
            trigger_type=trigger_type,
            is_active=True,
        )

        earned = []
        for achievement in achievements:
            # Skip if already earned
            if MemberAchievement.objects.filter(
                member=member, achievement=achievement
            ).exists():
                continue

            MemberAchievement.objects.create(
                member=member,
                achievement=achievement,
            )

            Notification.objects.create(
                member=member,
                title=f'Badge obtenu: {achievement.name}',
                message=f'Felicitations! Vous avez obtenu le badge "{achievement.name}". {achievement.description}',
                notification_type='general',
            )

            earned.append(achievement)

        return earned

    # ─── P1: Bulk Pipeline Actions (item 17) ─────────────────────────────

    @staticmethod
    def bulk_approve(member_ids, admin_member, course):
        """Approve multiple members at once and assign training."""
        from apps.members.models import Member

        approved = 0
        for member_id in member_ids:
            try:
                member = Member.objects.get(pk=member_id)
                if member.membership_status == MembershipStatus.FORM_SUBMITTED:
                    OnboardingService.admin_approve(member, admin_member, course)
                    approved += 1
            except Member.DoesNotExist:
                continue
        return approved

    @staticmethod
    def bulk_send_reminder(member_ids):
        """Send reminder notifications to multiple members."""
        from apps.members.models import Member

        sent = 0
        for member_id in member_ids:
            try:
                member = Member.objects.get(pk=member_id)
                Notification.objects.create(
                    member=member,
                    title='Rappel: Completez votre parcours',
                    message='N\'oubliez pas de completer les etapes de votre parcours d\'integration.',
                    notification_type='general',
                    link='/onboarding/dashboard/',
                )
                sent += 1
            except Member.DoesNotExist:
                continue
        return sent

    # ─── P2: Document Signing (items 28-32) ──────────────────────────────

    @staticmethod
    def sign_document(document, member, signature_text, ip_address=None):
        """Record a member's signature on a document."""
        from .models import DocumentSignature

        signature, created = DocumentSignature.objects.get_or_create(
            document=document,
            member=member,
            defaults={
                'signature_text': signature_text,
                'ip_address': ip_address,
            },
        )

        if created:
            OnboardingService.check_achievements(member, AchievementTrigger.DOCUMENT_SIGNED)

        return signature, created

    @staticmethod
    def get_member_document_status(member):
        """Get signing status for all required documents for a member."""
        from .models import OnboardingDocument, DocumentSignature

        documents = OnboardingDocument.objects.filter(
            is_active=True, requires_signature=True
        )

        result = []
        for doc in documents:
            signed = DocumentSignature.objects.filter(
                document=doc, member=member
            ).exists()
            result.append({
                'document': doc,
                'signed': signed,
            })

        return result

    # ─── P1: Lesson Reordering (item 16) ─────────────────────────────────

    @staticmethod
    def reorder_lessons(course, lesson_order):
        """Reorder lessons in a course. lesson_order is a list of lesson PKs in new order."""
        from .models import Lesson

        for idx, lesson_pk in enumerate(lesson_order, start=1):
            Lesson.all_objects.filter(pk=lesson_pk, course=course).update(order=idx)
