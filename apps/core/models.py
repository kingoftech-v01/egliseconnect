"""
Core models - Base models for ÉgliseConnect.

This module provides base model classes that all other models inherit from:
- BaseModel: UUID primary key, timestamps, is_active flag
- SoftDeleteModel: Adds soft delete functionality
"""
import uuid

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


# =============================================================================
# MANAGERS
# =============================================================================

class ActiveManager(models.Manager):
    """Manager that returns only active objects."""

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class SoftDeleteManager(models.Manager):
    """Manager that returns only non-deleted objects."""

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class AllObjectsManager(models.Manager):
    """Manager that returns all objects including deleted ones."""

    def get_queryset(self):
        return super().get_queryset()


# =============================================================================
# BASE MODELS
# =============================================================================

class BaseModel(models.Model):
    """
    Abstract base model with UUID primary key and timestamps.

    All models in the application should inherit from this class.

    Attributes:
        id: UUID primary key
        created_at: Timestamp when the object was created
        updated_at: Timestamp when the object was last updated
        is_active: Boolean flag to indicate if the object is active
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID')
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Date de création')
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Date de modification')
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Actif'),
        help_text=_('Indique si cet enregistrement est actif')
    )

    # Managers
    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def deactivate(self):
        """Deactivate this object."""
        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at'])

    def activate(self):
        """Activate this object."""
        self.is_active = True
        self.save(update_fields=['is_active', 'updated_at'])


class SoftDeleteModel(BaseModel):
    """
    Abstract base model with soft delete functionality.

    Instead of deleting records from the database, this model marks them
    as deleted by setting the deleted_at timestamp.

    Attributes:
        deleted_at: Timestamp when the object was soft deleted
    """

    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Date de suppression'),
        help_text=_('Date à laquelle cet enregistrement a été supprimé')
    )

    # Managers
    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True

    @property
    def is_deleted(self):
        """Check if this object has been soft deleted."""
        return self.deleted_at is not None

    def delete(self, using=None, keep_parents=False, hard_delete=False):
        """
        Soft delete this object by setting deleted_at timestamp.

        Args:
            hard_delete: If True, permanently delete the object from the database.
        """
        if hard_delete:
            return super().delete(using=using, keep_parents=keep_parents)

        self.deleted_at = timezone.now()
        self.is_active = False
        self.save(update_fields=['deleted_at', 'is_active', 'updated_at'])

    def restore(self):
        """Restore a soft deleted object."""
        self.deleted_at = None
        self.is_active = True
        self.save(update_fields=['deleted_at', 'is_active', 'updated_at'])

    def hard_delete(self, using=None, keep_parents=False):
        """Permanently delete this object from the database."""
        return super().delete(using=using, keep_parents=keep_parents)


# =============================================================================
# MIXINS
# =============================================================================

class TimeStampedMixin(models.Model):
    """
    Mixin that adds created_at and updated_at fields.

    Use this when you need timestamps but don't want to inherit from BaseModel.
    """

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Date de création')
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Date de modification')
    )

    class Meta:
        abstract = True


class OrderedMixin(models.Model):
    """
    Mixin that adds ordering functionality.

    Use this for models that need to be manually ordered.
    """

    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Ordre'),
        help_text=_('Ordre d\'affichage')
    )

    class Meta:
        abstract = True
        ordering = ['order']
