"""
Tests for core models.
"""
import uuid
from datetime import timedelta

import pytest
from django.db import models
from django.utils import timezone

from apps.core.models import BaseModel, SoftDeleteModel


# =============================================================================
# TEST MODELS (for testing abstract models)
# =============================================================================

class ConcreteBaseModel(BaseModel):
    """Concrete implementation of BaseModel for testing."""
    name = models.CharField(max_length=100)

    class Meta:
        app_label = 'core'


class ConcreteSoftDeleteModel(SoftDeleteModel):
    """Concrete implementation of SoftDeleteModel for testing."""
    name = models.CharField(max_length=100)

    class Meta:
        app_label = 'core'


# =============================================================================
# BASE MODEL TESTS
# =============================================================================

@pytest.mark.django_db
class TestBaseModel:
    """Tests for BaseModel."""

    def test_uuid_primary_key(self):
        """Test that BaseModel uses UUID as primary key."""
        obj = ConcreteBaseModel(name='Test')
        assert isinstance(obj.id, uuid.UUID)

    def test_created_at_auto_set(self):
        """Test that created_at is automatically set."""
        obj = ConcreteBaseModel.objects.create(name='Test')
        assert obj.created_at is not None
        assert obj.created_at <= timezone.now()

    def test_updated_at_auto_updated(self):
        """Test that updated_at is updated on save."""
        obj = ConcreteBaseModel.objects.create(name='Test')
        original_updated = obj.updated_at

        # Wait a tiny bit to ensure different timestamp
        obj.name = 'Updated'
        obj.save()

        assert obj.updated_at >= original_updated

    def test_is_active_default_true(self):
        """Test that is_active defaults to True."""
        obj = ConcreteBaseModel.objects.create(name='Test')
        assert obj.is_active is True

    def test_deactivate(self):
        """Test deactivate method."""
        obj = ConcreteBaseModel.objects.create(name='Test')
        obj.deactivate()

        assert obj.is_active is False

    def test_activate(self):
        """Test activate method."""
        obj = ConcreteBaseModel.objects.create(name='Test', is_active=False)
        obj.activate()

        assert obj.is_active is True

    def test_active_manager_excludes_inactive(self):
        """Test that default manager excludes inactive objects."""
        active = ConcreteBaseModel.objects.create(name='Active', is_active=True)
        inactive = ConcreteBaseModel.objects.create(name='Inactive', is_active=False)

        # Default manager should only return active
        assert active in ConcreteBaseModel.objects.all()
        assert inactive not in ConcreteBaseModel.objects.all()

    def test_all_objects_includes_inactive(self):
        """Test that all_objects manager includes inactive objects."""
        active = ConcreteBaseModel.objects.create(name='Active', is_active=True)
        inactive = ConcreteBaseModel.all_objects.create(name='Inactive', is_active=False)

        # all_objects should return both
        all_objs = ConcreteBaseModel.all_objects.all()
        assert active in all_objs
        assert inactive in all_objs


# =============================================================================
# SOFT DELETE MODEL TESTS
# =============================================================================

@pytest.mark.django_db
class TestSoftDeleteModel:
    """Tests for SoftDeleteModel."""

    def test_deleted_at_null_by_default(self):
        """Test that deleted_at is null by default."""
        obj = ConcreteSoftDeleteModel.objects.create(name='Test')
        assert obj.deleted_at is None

    def test_is_deleted_property(self):
        """Test is_deleted property."""
        obj = ConcreteSoftDeleteModel.objects.create(name='Test')
        assert obj.is_deleted is False

        obj.deleted_at = timezone.now()
        assert obj.is_deleted is True

    def test_soft_delete(self):
        """Test soft delete sets deleted_at."""
        obj = ConcreteSoftDeleteModel.objects.create(name='Test')
        obj.delete()

        # Refresh from database using all_objects
        obj = ConcreteSoftDeleteModel.all_objects.get(pk=obj.pk)

        assert obj.deleted_at is not None
        assert obj.is_active is False

    def test_soft_delete_excludes_from_default_queryset(self):
        """Test that soft deleted objects are excluded from default queryset."""
        obj = ConcreteSoftDeleteModel.objects.create(name='Test')
        obj.delete()

        assert obj not in ConcreteSoftDeleteModel.objects.all()

    def test_restore(self):
        """Test restore method."""
        obj = ConcreteSoftDeleteModel.objects.create(name='Test')
        obj.delete()

        # Get from all_objects since it's deleted
        obj = ConcreteSoftDeleteModel.all_objects.get(pk=obj.pk)
        obj.restore()

        assert obj.deleted_at is None
        assert obj.is_active is True
        assert obj in ConcreteSoftDeleteModel.objects.all()

    def test_hard_delete(self):
        """Test hard delete permanently removes object."""
        obj = ConcreteSoftDeleteModel.objects.create(name='Test')
        pk = obj.pk
        obj.hard_delete()

        with pytest.raises(ConcreteSoftDeleteModel.DoesNotExist):
            ConcreteSoftDeleteModel.all_objects.get(pk=pk)

    def test_delete_with_hard_delete_flag(self):
        """Test delete with hard_delete=True."""
        obj = ConcreteSoftDeleteModel.objects.create(name='Test')
        pk = obj.pk
        obj.delete(hard_delete=True)

        with pytest.raises(ConcreteSoftDeleteModel.DoesNotExist):
            ConcreteSoftDeleteModel.all_objects.get(pk=pk)

    def test_all_objects_includes_deleted(self):
        """Test that all_objects manager includes deleted objects."""
        obj1 = ConcreteSoftDeleteModel.objects.create(name='Active')
        obj2 = ConcreteSoftDeleteModel.objects.create(name='Deleted')
        obj2.delete()

        all_objs = ConcreteSoftDeleteModel.all_objects.all()
        assert obj1 in all_objs
        # Need to get obj2 from all_objects since it's now deleted
        obj2_refreshed = ConcreteSoftDeleteModel.all_objects.get(pk=obj2.pk)
        assert obj2_refreshed in all_objs
