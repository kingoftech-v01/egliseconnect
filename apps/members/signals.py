"""Signals for automatic member profile creation."""
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()


@receiver(post_save, sender=User)
def create_member_for_superuser(sender, instance, created, **kwargs):
    """Auto-create an active admin Member profile for new superusers."""
    if not created or not instance.is_superuser:
        return

    from apps.members.models import Member
    from apps.core.constants import MembershipStatus, Roles

    if hasattr(instance, 'member_profile'):
        return

    Member.objects.create(
        user=instance,
        first_name=instance.first_name or 'Admin',
        last_name=instance.last_name or instance.username.capitalize(),
        email=instance.email or '',
        role=Roles.ADMIN,
        membership_status=MembershipStatus.ACTIVE,
    )
