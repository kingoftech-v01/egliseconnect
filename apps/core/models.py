"""Base models for ÉgliseConnect - UUID primary keys, timestamps, soft delete."""
import uuid

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class ActiveManager(models.Manager):
    """Returns only active (is_active=True) objects."""

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class SoftDeleteManager(models.Manager):
    """Returns only non-deleted objects."""

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class AllObjectsManager(models.Manager):
    """Returns all objects including inactive/deleted - use for admin, reports, recovery."""
    pass


class BaseModel(models.Model):
    """Abstract base with UUID primary key, timestamps, and is_active flag."""

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

    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def deactivate(self):
        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at'])

    def activate(self):
        self.is_active = True
        self.save(update_fields=['is_active', 'updated_at'])


class SoftDeleteModel(BaseModel):
    """
    Base model with soft delete - sets deleted_at instead of removing from DB.
    Preserves data for audit trails and accidental deletion recovery.
    """

    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Date de suppression'),
        help_text=_('Date à laquelle cet enregistrement a été supprimé')
    )

    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    def delete(self, using=None, keep_parents=False, hard_delete=False):
        """
        Soft delete by default. Returns Django's expected (count, {label: count})
        tuple so callers like admin don't break.
        """
        if hard_delete:
            return super().delete(using=using, keep_parents=keep_parents)

        self.deleted_at = timezone.now()
        self.is_active = False
        self.save(update_fields=['deleted_at', 'is_active', 'updated_at'])
        return (1, {self._meta.label: 1})

    def restore(self):
        self.deleted_at = None
        self.is_active = True
        self.save(update_fields=['deleted_at', 'is_active', 'updated_at'])

    def hard_delete(self, using=None, keep_parents=False):
        return super().delete(using=using, keep_parents=keep_parents)


class TimeStampedMixin(models.Model):
    """Adds created_at/updated_at without UUID or is_active."""

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
    """Adds manual ordering capability via 'order' field."""

    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Ordre'),
        help_text=_('Ordre d\'affichage')
    )

    class Meta:
        abstract = True
        ordering = ['order']
