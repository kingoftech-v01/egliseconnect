"""Signals for automatic onboarding initialization."""
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.members.models import Member
from apps.core.constants import MembershipStatus


@receiver(post_save, sender=Member)
def initialize_onboarding_on_create(sender, instance, created, **kwargs):
    """When a new member is created with a user account, initialize onboarding."""
    if created and instance.user and not instance.registration_date:
        # Superusers skip onboarding — they're already active admins
        if instance.user.is_superuser:
            return
        from .services import OnboardingService
        OnboardingService.initialize_onboarding(instance)
