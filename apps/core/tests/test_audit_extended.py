"""Tests for AuditLog model, service, and viewer views."""
import json

import pytest
from django.contrib.auth import get_user_model

from apps.core.constants import Roles
from apps.core.models_extended import AuditLog
from apps.core.services_audit import AuditService
from apps.members.tests.factories import MemberWithUserFactory, UserFactory, MemberFactory

User = get_user_model()


@pytest.mark.django_db
class TestAuditLogModel:
    def test_create_audit_log(self):
        user = UserFactory()
        log = AuditLog.objects.create(
            user=user,
            action='create',
            model_name='Member',
            object_id='test-123',
            object_repr='Jean Tremblay',
        )
        assert log.action == 'create'
        assert log.model_name == 'Member'
        assert log.object_repr == 'Jean Tremblay'

    def test_str_representation(self):
        user = UserFactory()
        log = AuditLog.objects.create(
            user=user,
            action='update',
            model_name='Event',
        )
        result = str(log)
        assert user.username in result
        assert 'Modification' in result
        assert 'Event' in result

    def test_str_without_user(self):
        log = AuditLog.objects.create(
            action='create',
            model_name='Member',
        )
        assert 'System' in str(log)

    def test_ordering(self):
        from datetime import timedelta
        from django.utils import timezone
        user = UserFactory()
        l1 = AuditLog.objects.create(user=user, action='create', model_name='A')
        l2 = AuditLog.objects.create(user=user, action='update', model_name='B')
        # Ensure distinct created_at values so ordering is deterministic
        now = timezone.now()
        AuditLog.objects.filter(pk=l1.pk).update(created_at=now - timedelta(seconds=10))
        AuditLog.objects.filter(pk=l2.pk).update(created_at=now)
        logs = list(AuditLog.objects.all())
        assert logs[0] == l2  # Newest first

    def test_action_choices(self):
        user = UserFactory()
        for action_value, _ in AuditLog.ACTION_CHOICES:
            log = AuditLog.objects.create(
                user=user,
                action=action_value,
                model_name='Test',
            )
            assert log.action == action_value

    def test_changes_json(self):
        user = UserFactory()
        changes = {
            'email': {'old': 'old@test.com', 'new': 'new@test.com'},
        }
        log = AuditLog.objects.create(
            user=user,
            action='update',
            model_name='Member',
            changes=changes,
        )
        assert log.changes['email']['old'] == 'old@test.com'

    def test_ip_address_nullable(self):
        log = AuditLog.objects.create(
            action='create',
            model_name='Member',
        )
        assert log.ip_address is None

    def test_indexes_exist(self):
        """Verify indexes are defined in Meta."""
        indexes = AuditLog._meta.indexes
        assert len(indexes) >= 3


@pytest.mark.django_db
class TestAuditService:
    def test_log_create(self):
        from django.test import RequestFactory
        user = UserFactory()
        member = MemberFactory()
        factory = RequestFactory()
        request = factory.get('/', REMOTE_ADDR='1.2.3.4')
        request.user = user

        AuditService.log_create(request, member)
        log = AuditLog.objects.last()
        assert log.action == 'create'
        assert log.model_name == 'Member'
        assert log.user == user
        assert log.ip_address == '1.2.3.4'

    def test_log_update_with_changes(self):
        from django.test import RequestFactory
        user = UserFactory()
        member = MemberFactory(first_name='OldName')
        factory = RequestFactory()
        request = factory.get('/', REMOTE_ADDR='5.6.7.8')
        request.user = user

        old_data = {'first_name': 'OldName'}
        member.first_name = 'NewName'
        member.save()

        AuditService.log_update(request, member, old_data)
        log = AuditLog.objects.last()
        assert log.action == 'update'
        assert 'first_name' in log.changes

    def test_log_delete(self):
        from django.test import RequestFactory
        user = UserFactory()
        member = MemberFactory()
        factory = RequestFactory()
        request = factory.get('/', REMOTE_ADDR='10.0.0.1')
        request.user = user

        AuditService.log_delete(request, member)
        log = AuditLog.objects.last()
        assert log.action == 'delete'

    def test_log_export(self):
        from django.test import RequestFactory
        user = UserFactory()
        factory = RequestFactory()
        request = factory.get('/')
        request.user = user

        AuditService.log_export(request, 'Member', 50)
        log = AuditLog.objects.last()
        assert log.action == 'export'
        assert '50' in log.object_repr

    def test_log_without_request(self):
        member = MemberFactory()
        AuditService.log(None, 'create', member)
        log = AuditLog.objects.last()
        assert log.user is None
        assert log.ip_address is None


@pytest.mark.django_db
class TestAuditLogListView:
    def test_requires_login(self, client):
        response = client.get('/settings/audit/')
        assert response.status_code == 302

    def test_requires_admin(self, client):
        member = MemberWithUserFactory(role=Roles.MEMBER)
        client.force_login(member.user)
        response = client.get('/settings/audit/')
        assert response.status_code == 302

    def test_admin_access(self, client):
        admin = MemberWithUserFactory(role=Roles.ADMIN)
        client.force_login(admin.user)
        response = client.get('/settings/audit/')
        assert response.status_code == 200

    def test_filter_by_action(self, client):
        admin = MemberWithUserFactory(role=Roles.ADMIN)
        AuditLog.objects.create(
            user=admin.user,
            action='create',
            model_name='Test',
        )
        client.force_login(admin.user)
        response = client.get('/settings/audit/?action=create')
        assert response.status_code == 200

    def test_filter_by_model(self, client):
        admin = MemberWithUserFactory(role=Roles.ADMIN)
        client.force_login(admin.user)
        response = client.get('/settings/audit/?model=Member')
        assert response.status_code == 200


@pytest.mark.django_db
class TestAuditLogExportView:
    def test_csv_export(self, client):
        admin = MemberWithUserFactory(role=Roles.ADMIN)
        AuditLog.objects.create(
            user=admin.user,
            action='create',
            model_name='Test',
            object_repr='Test Object',
        )
        client.force_login(admin.user)
        response = client.get('/settings/audit/export/?format=csv')
        assert response.status_code == 200
        assert response['Content-Type'] == 'text/csv; charset=utf-8'

    def test_json_export(self, client):
        admin = MemberWithUserFactory(role=Roles.ADMIN)
        AuditLog.objects.create(
            user=admin.user,
            action='update',
            model_name='Event',
            object_repr='Test Event',
        )
        client.force_login(admin.user)
        response = client.get('/settings/audit/export/?format=json')
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/json'
        data = json.loads(response.content)
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_requires_admin(self, client):
        member = MemberWithUserFactory(role=Roles.MEMBER)
        client.force_login(member.user)
        response = client.get('/settings/audit/export/')
        assert response.status_code == 302
