"""Tests for core admin classes (BaseModelAdmin, SoftDeleteModelAdmin, LoginAuditAdmin)."""
import pytest
from django.test import RequestFactory
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage

from apps.core.admin import BaseModelAdmin, SoftDeleteModelAdmin, LoginAuditAdmin
from apps.core.audit import LoginAudit
from apps.members.models import Member
from apps.members.admin import MemberAdmin
from apps.members.tests.factories import MemberFactory

User = get_user_model()


def _attach_messages(request):
    """Attach Django messages framework to a request for admin actions."""
    setattr(request, 'session', 'session')
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)
    return request


@pytest.mark.django_db
class TestBaseModelAdmin:
    """Tests for BaseModelAdmin.get_queryset which uses all_objects."""

    def test_get_queryset_includes_inactive(self):
        """get_queryset should return both active and inactive objects."""
        active = MemberFactory()
        inactive = MemberFactory(is_active=False)

        site = AdminSite()
        admin_instance = MemberAdmin(Member, site)
        factory = RequestFactory()
        request = factory.get('/admin/')
        request.user = User.objects.create_superuser('admin_base', 'admin_base@test.com', 'pw')

        qs = admin_instance.get_queryset(request)
        assert qs.filter(pk=active.pk).exists()
        assert qs.filter(pk=inactive.pk).exists()

    def test_get_queryset_includes_soft_deleted(self):
        """get_queryset should return soft-deleted objects as well."""
        member = MemberFactory()
        member.delete()  # soft delete

        site = AdminSite()
        admin_instance = MemberAdmin(Member, site)
        factory = RequestFactory()
        request = factory.get('/admin/')
        request.user = User.objects.create_superuser('admin_base2', 'admin_base2@test.com', 'pw')

        qs = admin_instance.get_queryset(request)
        assert qs.filter(pk=member.pk).exists()


@pytest.mark.django_db
class TestSoftDeleteModelAdmin:
    """Tests for SoftDeleteModelAdmin restore_selected and hard_delete_selected actions."""

    def test_restore_selected_restores_deleted_objects(self):
        """restore_selected should restore soft-deleted objects."""
        member = MemberFactory()
        member.delete()  # soft delete
        member = Member.all_objects.get(pk=member.pk)
        assert member.is_deleted

        site = AdminSite()
        admin_instance = MemberAdmin(Member, site)
        factory = RequestFactory()
        request = factory.get('/admin/')
        request.user = User.objects.create_superuser('admin_restore', 'restore@test.com', 'pw')
        _attach_messages(request)

        qs = Member.all_objects.filter(pk=member.pk)
        admin_instance.restore_selected(request, qs)

        member.refresh_from_db()
        assert member.is_deleted is False
        assert member.is_active is True

    def test_restore_selected_skips_non_deleted(self):
        """restore_selected should not error on non-deleted objects, count stays 0 for them."""
        member = MemberFactory()
        assert member.is_active

        site = AdminSite()
        admin_instance = MemberAdmin(Member, site)
        factory = RequestFactory()
        request = factory.get('/admin/')
        request.user = User.objects.create_superuser('admin_skip', 'skip@test.com', 'pw')
        _attach_messages(request)

        qs = Member.all_objects.filter(pk=member.pk)
        admin_instance.restore_selected(request, qs)

        member.refresh_from_db()
        assert member.is_active is True

    def test_hard_delete_selected_permanently_removes(self):
        """hard_delete_selected should permanently remove objects from database."""
        member = MemberFactory()
        pk = member.pk

        site = AdminSite()
        admin_instance = MemberAdmin(Member, site)
        factory = RequestFactory()
        request = factory.get('/admin/')
        request.user = User.objects.create_superuser('admin_hard', 'hard@test.com', 'pw')
        _attach_messages(request)

        qs = Member.all_objects.filter(pk=pk)
        admin_instance.hard_delete_selected(request, qs)

        assert not Member.all_objects.filter(pk=pk).exists()

    def test_hard_delete_selected_multiple_objects(self):
        """hard_delete_selected should handle multiple objects."""
        m1 = MemberFactory()
        m2 = MemberFactory()
        pk1, pk2 = m1.pk, m2.pk

        site = AdminSite()
        admin_instance = MemberAdmin(Member, site)
        factory = RequestFactory()
        request = factory.get('/admin/')
        request.user = User.objects.create_superuser('admin_multi', 'multi@test.com', 'pw')
        _attach_messages(request)

        qs = Member.all_objects.filter(pk__in=[pk1, pk2])
        admin_instance.hard_delete_selected(request, qs)

        assert not Member.all_objects.filter(pk__in=[pk1, pk2]).exists()


@pytest.mark.django_db
class TestLoginAuditAdmin:
    """Tests for LoginAuditAdmin read-only permission overrides."""

    def setup_method(self):
        self.site = AdminSite()
        self.admin = LoginAuditAdmin(LoginAudit, self.site)
        self.factory = RequestFactory()

    def test_has_add_permission_returns_false(self):
        """has_add_permission should always return False (audit logs are read-only)."""
        request = self.factory.get('/admin/')
        request.user = User.objects.create_superuser('su_add', 'su_add@test.com', 'pw')
        assert self.admin.has_add_permission(request) is False

    def test_has_change_permission_returns_false(self):
        """has_change_permission should always return False."""
        request = self.factory.get('/admin/')
        request.user = User.objects.create_superuser('su_change', 'su_change@test.com', 'pw')
        assert self.admin.has_change_permission(request) is False

    def test_has_change_permission_with_obj_returns_false(self):
        """has_change_permission should return False even with an obj argument."""
        request = self.factory.get('/admin/')
        request.user = User.objects.create_superuser('su_change2', 'su_change2@test.com', 'pw')
        audit = LoginAudit.objects.create(
            email_attempted='test@test.com',
            ip_address='127.0.0.1',
            success=True,
        )
        assert self.admin.has_change_permission(request, obj=audit) is False

    def test_has_delete_permission_superuser_returns_true(self):
        """Superusers should be able to delete audit logs."""
        request = self.factory.get('/admin/')
        request.user = User.objects.create_superuser('su_del', 'su_del@test.com', 'pw')
        assert self.admin.has_delete_permission(request) is True

    def test_has_delete_permission_non_superuser_returns_false(self):
        """Non-superuser staff should not be able to delete audit logs."""
        request = self.factory.get('/admin/')
        request.user = User.objects.create_user('staff_del', 'staff_del@test.com', 'pw', is_staff=True)
        assert self.admin.has_delete_permission(request) is False

    def test_has_delete_permission_regular_user_returns_false(self):
        """Regular users should not be able to delete audit logs."""
        request = self.factory.get('/admin/')
        request.user = User.objects.create_user('user_del', 'user_del@test.com', 'pw')
        assert self.admin.has_delete_permission(request) is False
