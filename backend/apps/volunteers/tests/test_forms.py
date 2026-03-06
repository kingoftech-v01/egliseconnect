"""Tests for volunteers forms."""
import pytest

from apps.core.constants import VolunteerRole, ScheduleStatus
from apps.members.tests.factories import MemberFactory
from apps.volunteers.forms import VolunteerPositionForm, VolunteerScheduleForm
from apps.volunteers.tests.factories import VolunteerPositionFactory
from apps.volunteers.models import VolunteerPosition, VolunteerSchedule

pytestmark = pytest.mark.django_db


class TestVolunteerPositionForm:

    def _get_valid_data(self, **overrides):
        data = {
            'name': 'Technicien son',
            'role_type': VolunteerRole.TECHNICAL,
            'description': 'Gérer le son pendant le culte',
            'min_volunteers': 2,
            'max_volunteers': 5,
            'skills_required': 'Connaissance audio',
        }
        data.update(overrides)
        return data

    def test_valid_form(self):
        form = VolunteerPositionForm(data=self._get_valid_data())
        assert form.is_valid()

    def test_valid_minimal(self):
        form = VolunteerPositionForm(data={
            'name': 'Accueil',
            'role_type': VolunteerRole.WORSHIP,
            'min_volunteers': 1,
        })
        assert form.is_valid()

    def test_name_required(self):
        form = VolunteerPositionForm(data=self._get_valid_data(name=''))
        assert not form.is_valid()
        assert 'name' in form.errors

    def test_role_type_required(self):
        form = VolunteerPositionForm(data=self._get_valid_data(role_type=''))
        assert not form.is_valid()
        assert 'role_type' in form.errors

    def test_save_creates_position(self):
        form = VolunteerPositionForm(data=self._get_valid_data())
        assert form.is_valid()
        position = form.save()
        assert position.pk is not None
        assert position.name == 'Technicien son'
        assert VolunteerPosition.objects.filter(pk=position.pk).exists()

    def test_update_existing_position(self):
        position = VolunteerPositionFactory(name='Old Name')
        form = VolunteerPositionForm(
            data=self._get_valid_data(name='New Name'),
            instance=position,
        )
        assert form.is_valid()
        updated = form.save()
        assert updated.pk == position.pk
        assert updated.name == 'New Name'


class TestVolunteerScheduleForm:

    def _get_valid_data(self, **overrides):
        member = overrides.pop('member', None) or MemberFactory()
        position = overrides.pop('position', None) or VolunteerPositionFactory()
        data = {
            'member': member.pk,
            'position': position.pk,
            'date': '2026-03-15',
            'status': ScheduleStatus.SCHEDULED,
            'notes': '',
        }
        data.update(overrides)
        return data

    def test_valid_form(self):
        form = VolunteerScheduleForm(data=self._get_valid_data())
        assert form.is_valid()

    def test_member_required(self):
        data = self._get_valid_data()
        data['member'] = ''
        form = VolunteerScheduleForm(data=data)
        assert not form.is_valid()
        assert 'member' in form.errors

    def test_position_required(self):
        data = self._get_valid_data()
        data['position'] = ''
        form = VolunteerScheduleForm(data=data)
        assert not form.is_valid()
        assert 'position' in form.errors

    def test_date_required(self):
        data = self._get_valid_data()
        data['date'] = ''
        form = VolunteerScheduleForm(data=data)
        assert not form.is_valid()
        assert 'date' in form.errors

    def test_event_optional(self):
        data = self._get_valid_data()
        data['event'] = ''
        form = VolunteerScheduleForm(data=data)
        assert form.is_valid()

    def test_save_creates_schedule(self):
        form = VolunteerScheduleForm(data=self._get_valid_data())
        assert form.is_valid()
        schedule = form.save()
        assert schedule.pk is not None
        assert VolunteerSchedule.objects.filter(pk=schedule.pk).exists()

    def test_update_existing_schedule(self):
        from apps.volunteers.tests.factories import VolunteerScheduleFactory
        schedule = VolunteerScheduleFactory()
        form = VolunteerScheduleForm(
            data=self._get_valid_data(
                member=schedule.member,
                position=schedule.position,
                notes='Updated note',
            ),
            instance=schedule,
        )
        assert form.is_valid()
        updated = form.save()
        assert updated.pk == schedule.pk
        assert updated.notes == 'Updated note'
