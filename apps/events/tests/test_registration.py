"""Tests for custom registration forms and entries."""
import pytest
from django.utils import timezone

from apps.events.models import RegistrationForm, RegistrationEntry
from apps.events.tests.factories import (
    EventFactory, RegistrationFormFactory, RegistrationEntryFactory,
)
from apps.members.tests.factories import MemberFactory


pytestmark = pytest.mark.django_db


class TestRegistrationFormModel:
    def test_create_registration_form(self):
        event = EventFactory()
        form = RegistrationForm.objects.create(
            event=event,
            title='Inscription conférence',
            fields_json=[
                {'name': 'dietary', 'type': 'text', 'label': 'Restrictions', 'required': False},
            ],
        )
        assert form.title == 'Inscription conférence'
        assert len(form.fields_json) == 1

    def test_str(self):
        form = RegistrationFormFactory(title='Mon formulaire')
        assert 'Mon formulaire' in str(form)
        assert form.event.title in str(form)

    def test_factory(self):
        form = RegistrationFormFactory()
        assert form.pk is not None
        assert len(form.fields_json) == 2


class TestRegistrationEntryModel:
    def test_create_entry(self):
        form = RegistrationFormFactory()
        member = MemberFactory()
        entry = RegistrationEntry.objects.create(
            form=form,
            member=member,
            data_json={'dietary': 'Végétarien', 'tshirt': 'L'},
        )
        assert entry.data_json['dietary'] == 'Végétarien'
        assert entry.submitted_at is not None

    def test_unique_form_member(self):
        entry = RegistrationEntryFactory()
        with pytest.raises(Exception):
            RegistrationEntry.objects.create(
                form=entry.form,
                member=entry.member,
                data_json={},
            )

    def test_str(self):
        entry = RegistrationEntryFactory()
        assert entry.member.full_name in str(entry)

    def test_factory(self):
        entry = RegistrationEntryFactory()
        assert entry.pk is not None
        assert 'dietary' in entry.data_json


class TestRegistrationFormRelations:
    def test_entries_related_name(self):
        form = RegistrationFormFactory()
        RegistrationEntryFactory(form=form)
        RegistrationEntryFactory(form=form)
        assert form.entries.count() == 2

    def test_event_has_registration_forms(self):
        event = EventFactory()
        RegistrationFormFactory(event=event)
        assert event.registration_forms.count() == 1
