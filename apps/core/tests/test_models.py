"""Tests for core models (BaseModel and SoftDeleteModel)."""
import uuid

import pytest
from django.utils import timezone

from apps.core.audit import LoginAudit
from apps.members.models import Member
from apps.members.tests.factories import MemberFactory, UserFactory


@pytest.mark.django_db
class TestBaseModel:
    """Tests for BaseModel using LoginAudit (a concrete BaseModel subclass)."""

    def test_uuid_primary_key(self):
        """BaseModel uses UUID as primary key."""
        user = UserFactory()
        obj = LoginAudit.objects.create(
            user=user,
            email_attempted='test@test.com',
            ip_address='127.0.0.1',
            success=True,
        )
        assert isinstance(obj.id, uuid.UUID)

    def test_created_at_auto_set(self):
        """created_at is automatically set."""
        obj = LoginAudit.objects.create(
            email_attempted='test@test.com',
            ip_address='127.0.0.1',
        )
        assert obj.created_at is not None
        assert obj.created_at <= timezone.now()

    def test_updated_at_auto_updated(self):
        """updated_at is updated on save."""
        obj = LoginAudit.objects.create(
            email_attempted='test@test.com',
            ip_address='127.0.0.1',
        )
        original_updated = obj.updated_at

        obj.failure_reason = 'Updated'
        obj.save()

        assert obj.updated_at >= original_updated

    def test_is_active_default_true(self):
        """is_active defaults to True."""
        obj = LoginAudit.objects.create(
            email_attempted='test@test.com',
            ip_address='127.0.0.1',
        )
        assert obj.is_active is True

    def test_deactivate(self):
        """deactivate method sets is_active to False."""
        obj = LoginAudit.objects.create(
            email_attempted='test@test.com',
            ip_address='127.0.0.1',
        )
        obj.deactivate()
        assert obj.is_active is False

    def test_activate(self):
        """activate method sets is_active to True."""
        obj = LoginAudit.objects.create(
            email_attempted='test@test.com',
            ip_address='127.0.0.1',
            is_active=False,
        )
        obj.activate()
        assert obj.is_active is True

    def test_active_manager_excludes_inactive(self):
        """Default manager excludes inactive objects."""
        active = LoginAudit.objects.create(
            email_attempted='a@test.com', ip_address='1.1.1.1', is_active=True,
        )
        inactive = LoginAudit.objects.create(
            email_attempted='b@test.com', ip_address='2.2.2.2', is_active=False,
        )
        assert active in LoginAudit.objects.all()
        assert inactive not in LoginAudit.objects.all()

    def test_all_objects_includes_inactive(self):
        """all_objects manager includes inactive objects."""
        active = LoginAudit.objects.create(
            email_attempted='a@test.com', ip_address='1.1.1.1',
        )
        inactive = LoginAudit.all_objects.create(
            email_attempted='b@test.com', ip_address='2.2.2.2', is_active=False,
        )
        all_objs = LoginAudit.all_objects.all()
        assert active in all_objs
        assert inactive in all_objs


@pytest.mark.django_db
class TestSoftDeleteModel:
    """Tests for SoftDeleteModel using Member (a concrete SoftDeleteModel subclass)."""

    def test_deleted_at_null_by_default(self):
        """deleted_at is null by default."""
        obj = MemberFactory()
        assert obj.deleted_at is None

    def test_is_deleted_property(self):
        """is_deleted property reflects deleted_at value."""
        obj = MemberFactory()
        assert obj.is_deleted is False

        obj.deleted_at = timezone.now()
        assert obj.is_deleted is True

    def test_soft_delete(self):
        """Soft delete sets deleted_at."""
        obj = MemberFactory()
        obj.delete()
        obj = Member.all_objects.get(pk=obj.pk)
        assert obj.deleted_at is not None
        assert obj.is_active is False

    def test_soft_delete_excludes_from_default_queryset(self):
        """Soft deleted objects are excluded from default queryset."""
        obj = MemberFactory()
        obj.delete()
        assert obj not in Member.objects.all()

    def test_restore(self):
        """restore method clears deleted_at and reactivates."""
        obj = MemberFactory()
        obj.delete()
        obj = Member.all_objects.get(pk=obj.pk)
        obj.restore()
        assert obj.deleted_at is None
        assert obj.is_active is True
        assert obj in Member.objects.all()

    def test_hard_delete(self):
        """hard_delete permanently removes object."""
        obj = MemberFactory()
        pk = obj.pk
        obj.hard_delete()
        with pytest.raises(Member.DoesNotExist):
            Member.all_objects.get(pk=pk)

    def test_delete_with_hard_delete_flag(self):
        """delete with hard_delete=True permanently removes."""
        obj = MemberFactory()
        pk = obj.pk
        obj.delete(hard_delete=True)
        with pytest.raises(Member.DoesNotExist):
            Member.all_objects.get(pk=pk)

    def test_all_objects_includes_deleted(self):
        """all_objects manager includes deleted objects."""
        obj1 = MemberFactory()
        obj2 = MemberFactory()
        obj2.delete()
        all_objs = Member.all_objects.all()
        assert obj1 in all_objs
        obj2_refreshed = Member.all_objects.get(pk=obj2.pk)
        assert obj2_refreshed in all_objs
