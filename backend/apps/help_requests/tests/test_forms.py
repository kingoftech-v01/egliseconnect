"""Tests for help requests forms."""
import pytest

from apps.core.constants import HelpRequestUrgency, Roles
from apps.help_requests.forms import (
    HelpRequestForm,
    HelpRequestCommentForm,
    HelpRequestAssignForm,
    HelpRequestResolveForm,
)
from .factories import HelpRequestCategoryFactory
from apps.members.tests.factories import MemberFactory


@pytest.mark.django_db
class TestHelpRequestForm:
    """Tests for HelpRequestForm validation."""

    def test_valid_form(self):
        category = HelpRequestCategoryFactory()
        data = {
            'category': category.id,
            'title': 'Need prayer',
            'description': 'Please pray for my family',
            'urgency': HelpRequestUrgency.MEDIUM,
            'is_confidential': False,
        }
        form = HelpRequestForm(data=data)
        assert form.is_valid(), form.errors

    def test_title_required(self):
        category = HelpRequestCategoryFactory()
        data = {
            'category': category.id,
            'title': '',
            'description': 'Description',
            'urgency': HelpRequestUrgency.LOW,
        }
        form = HelpRequestForm(data=data)
        assert not form.is_valid()
        assert 'title' in form.errors

    def test_description_required(self):
        category = HelpRequestCategoryFactory()
        data = {
            'category': category.id,
            'title': 'Title',
            'description': '',
            'urgency': HelpRequestUrgency.LOW,
        }
        form = HelpRequestForm(data=data)
        assert not form.is_valid()
        assert 'description' in form.errors

    def test_category_required(self):
        data = {
            'title': 'Title',
            'description': 'Description',
            'urgency': HelpRequestUrgency.LOW,
        }
        form = HelpRequestForm(data=data)
        assert not form.is_valid()
        assert 'category' in form.errors

    def test_urgency_required(self):
        category = HelpRequestCategoryFactory()
        data = {
            'category': category.id,
            'title': 'Title',
            'description': 'Description',
            'urgency': '',
        }
        form = HelpRequestForm(data=data)
        assert not form.is_valid()
        assert 'urgency' in form.errors

    def test_invalid_urgency(self):
        category = HelpRequestCategoryFactory()
        data = {
            'category': category.id,
            'title': 'Title',
            'description': 'Description',
            'urgency': 'extreme',
        }
        form = HelpRequestForm(data=data)
        assert not form.is_valid()
        assert 'urgency' in form.errors

    def test_is_confidential_optional(self):
        category = HelpRequestCategoryFactory()
        data = {
            'category': category.id,
            'title': 'Title',
            'description': 'Description',
            'urgency': HelpRequestUrgency.LOW,
        }
        form = HelpRequestForm(data=data)
        assert form.is_valid()
        assert form.cleaned_data['is_confidential'] is False

    def test_is_confidential_true(self):
        category = HelpRequestCategoryFactory()
        data = {
            'category': category.id,
            'title': 'Sensitive issue',
            'description': 'Private matter',
            'urgency': HelpRequestUrgency.HIGH,
            'is_confidential': True,
        }
        form = HelpRequestForm(data=data)
        assert form.is_valid()
        assert form.cleaned_data['is_confidential'] is True

    def test_all_urgency_levels(self):
        category = HelpRequestCategoryFactory()
        for urgency in [
            HelpRequestUrgency.LOW,
            HelpRequestUrgency.MEDIUM,
            HelpRequestUrgency.HIGH,
            HelpRequestUrgency.URGENT,
        ]:
            data = {
                'category': category.id,
                'title': f'Request {urgency}',
                'description': 'Description',
                'urgency': urgency,
            }
            form = HelpRequestForm(data=data)
            assert form.is_valid(), f'Failed for urgency {urgency}: {form.errors}'

    def test_title_max_length(self):
        category = HelpRequestCategoryFactory()
        data = {
            'category': category.id,
            'title': 'A' * 201,
            'description': 'Description',
            'urgency': HelpRequestUrgency.LOW,
        }
        form = HelpRequestForm(data=data)
        assert not form.is_valid()
        assert 'title' in form.errors

    def test_form_fields(self):
        form = HelpRequestForm()
        expected = {'category', 'title', 'description', 'urgency', 'is_confidential'}
        assert set(form.fields.keys()) == expected

    def test_form_labels(self):
        form = HelpRequestForm()
        assert form.fields['category'].label == 'Catégorie'
        assert form.fields['title'].label == 'Titre'
        assert form.fields['description'].label == 'Description'
        assert form.fields['urgency'].label == 'Urgence'

    def test_description_widget(self):
        form = HelpRequestForm()
        assert form.fields['description'].widget.attrs.get('rows') == 5


@pytest.mark.django_db
class TestHelpRequestCommentForm:
    """Tests for HelpRequestCommentForm validation."""

    def test_valid_form(self):
        data = {
            'content': 'This is a helpful comment.',
            'is_internal': False,
        }
        form = HelpRequestCommentForm(data=data)
        assert form.is_valid(), form.errors

    def test_content_required(self):
        data = {
            'content': '',
            'is_internal': False,
        }
        form = HelpRequestCommentForm(data=data)
        assert not form.is_valid()
        assert 'content' in form.errors

    def test_is_internal_default(self):
        data = {'content': 'A comment'}
        form = HelpRequestCommentForm(data=data)
        assert form.is_valid()
        assert form.cleaned_data['is_internal'] is False

    def test_is_internal_true(self):
        data = {
            'content': 'Internal staff note',
            'is_internal': True,
        }
        form = HelpRequestCommentForm(data=data)
        assert form.is_valid()
        assert form.cleaned_data['is_internal'] is True

    def test_form_fields(self):
        form = HelpRequestCommentForm()
        assert set(form.fields.keys()) == {'content', 'is_internal'}

    def test_content_widget(self):
        form = HelpRequestCommentForm()
        assert form.fields['content'].widget.attrs.get('rows') == 3

    def test_form_labels(self):
        form = HelpRequestCommentForm()
        assert form.fields['content'].label == 'Commentaire'


@pytest.mark.django_db
class TestHelpRequestAssignForm:
    """Tests for HelpRequestAssignForm validation."""

    def test_valid_uuid(self):
        staff = MemberFactory(role=Roles.PASTOR)
        data = {'assigned_to': str(staff.id)}
        form = HelpRequestAssignForm(data=data)
        assert form.is_valid(), form.errors

    def test_invalid_uuid(self):
        MemberFactory(role=Roles.PASTOR)
        data = {'assigned_to': 'not-a-uuid'}
        form = HelpRequestAssignForm(data=data)
        assert not form.is_valid()
        assert 'assigned_to' in form.errors

    def test_empty_uuid(self):
        MemberFactory(role=Roles.PASTOR)
        data = {'assigned_to': ''}
        form = HelpRequestAssignForm(data=data)
        assert not form.is_valid()
        assert 'assigned_to' in form.errors

    def test_choices_populated_with_staff(self):
        """Only pastor/admin members appear in assignment choices."""
        pastor = MemberFactory(role=Roles.PASTOR, first_name='Jean', last_name='Pasteur')
        admin = MemberFactory(role=Roles.ADMIN, first_name='Marie', last_name='Admin')
        MemberFactory(role=Roles.MEMBER, first_name='Regular', last_name='Member')

        form = HelpRequestAssignForm()
        choices = form.fields['assigned_to'].widget.choices
        choice_ids = [c[0] for c in choices]

        assert str(pastor.id) in choice_ids
        assert str(admin.id) in choice_ids
        assert len(choices) == 2


class TestHelpRequestResolveForm:
    """Tests for HelpRequestResolveForm validation."""

    def test_valid_with_notes(self):
        data = {'resolution_notes': 'Resolved by providing groceries.'}
        form = HelpRequestResolveForm(data=data)
        assert form.is_valid()

    def test_valid_without_notes(self):
        data = {'resolution_notes': ''}
        form = HelpRequestResolveForm(data=data)
        assert form.is_valid()

    def test_valid_empty_form(self):
        data = {}
        form = HelpRequestResolveForm(data=data)
        assert form.is_valid()

    def test_form_fields(self):
        form = HelpRequestResolveForm()
        assert set(form.fields.keys()) == {'resolution_notes'}

    def test_widget(self):
        form = HelpRequestResolveForm()
        assert form.fields['resolution_notes'].widget.attrs.get('rows') == 3

    def test_label(self):
        form = HelpRequestResolveForm()
        assert form.fields['resolution_notes'].label == 'Notes de résolution'
