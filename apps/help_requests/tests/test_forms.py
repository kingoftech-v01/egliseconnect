"""Help requests form tests."""
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


# =============================================================================
# HELP REQUEST FORM
# =============================================================================


@pytest.mark.django_db
class TestHelpRequestForm:
    """Tests for HelpRequestForm."""

    def test_valid_form(self):
        """Form with all required fields is valid."""
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
        """Title is required."""
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
        """Description is required."""
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
        """Category is required."""
        data = {
            'title': 'Title',
            'description': 'Description',
            'urgency': HelpRequestUrgency.LOW,
        }
        form = HelpRequestForm(data=data)
        assert not form.is_valid()
        assert 'category' in form.errors

    def test_urgency_required(self):
        """Urgency is required."""
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
        """Invalid urgency value is rejected."""
        category = HelpRequestCategoryFactory()
        data = {
            'category': category.id,
            'title': 'Title',
            'description': 'Description',
            'urgency': 'extreme',  # not a valid choice
        }
        form = HelpRequestForm(data=data)
        assert not form.is_valid()
        assert 'urgency' in form.errors

    def test_is_confidential_optional(self):
        """is_confidential defaults to False."""
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
        """is_confidential can be set to True."""
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
        """All valid urgency levels are accepted."""
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
        """Title has max length of 200."""
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
        """Form has correct fields."""
        form = HelpRequestForm()
        expected = {'category', 'title', 'description', 'urgency', 'is_confidential'}
        assert set(form.fields.keys()) == expected

    def test_form_labels(self):
        """Form has French labels."""
        form = HelpRequestForm()
        assert form.fields['category'].label == 'Catégorie'
        assert form.fields['title'].label == 'Titre'
        assert form.fields['description'].label == 'Description'
        assert form.fields['urgency'].label == 'Urgence'

    def test_description_widget(self):
        """Description uses Textarea widget with 5 rows."""
        form = HelpRequestForm()
        assert form.fields['description'].widget.attrs.get('rows') == 5


# =============================================================================
# HELP REQUEST COMMENT FORM
# =============================================================================


@pytest.mark.django_db
class TestHelpRequestCommentForm:
    """Tests for HelpRequestCommentForm."""

    def test_valid_form(self):
        """Valid comment form."""
        data = {
            'content': 'This is a helpful comment.',
            'is_internal': False,
        }
        form = HelpRequestCommentForm(data=data)
        assert form.is_valid(), form.errors

    def test_content_required(self):
        """Content is required."""
        data = {
            'content': '',
            'is_internal': False,
        }
        form = HelpRequestCommentForm(data=data)
        assert not form.is_valid()
        assert 'content' in form.errors

    def test_is_internal_default(self):
        """is_internal defaults to False."""
        data = {'content': 'A comment'}
        form = HelpRequestCommentForm(data=data)
        assert form.is_valid()
        assert form.cleaned_data['is_internal'] is False

    def test_is_internal_true(self):
        """is_internal can be set to True."""
        data = {
            'content': 'Internal staff note',
            'is_internal': True,
        }
        form = HelpRequestCommentForm(data=data)
        assert form.is_valid()
        assert form.cleaned_data['is_internal'] is True

    def test_form_fields(self):
        """Form has correct fields."""
        form = HelpRequestCommentForm()
        assert set(form.fields.keys()) == {'content', 'is_internal'}

    def test_content_widget(self):
        """Content uses Textarea widget with 3 rows."""
        form = HelpRequestCommentForm()
        assert form.fields['content'].widget.attrs.get('rows') == 3

    def test_form_labels(self):
        """Form has French labels."""
        form = HelpRequestCommentForm()
        assert form.fields['content'].label == 'Commentaire'


# =============================================================================
# HELP REQUEST ASSIGN FORM
# =============================================================================


@pytest.mark.django_db
class TestHelpRequestAssignForm:
    """Tests for HelpRequestAssignForm."""

    def test_valid_uuid(self):
        """Form accepts a valid UUID."""
        staff = MemberFactory(role=Roles.PASTOR)

        data = {'assigned_to': str(staff.id)}
        form = HelpRequestAssignForm(data=data)
        assert form.is_valid(), form.errors

    def test_invalid_uuid(self):
        """Form rejects invalid UUID."""
        MemberFactory(role=Roles.PASTOR)

        data = {'assigned_to': 'not-a-uuid'}
        form = HelpRequestAssignForm(data=data)
        assert not form.is_valid()
        assert 'assigned_to' in form.errors

    def test_empty_uuid(self):
        """Form rejects empty assigned_to."""
        MemberFactory(role=Roles.PASTOR)

        data = {'assigned_to': ''}
        form = HelpRequestAssignForm(data=data)
        assert not form.is_valid()
        assert 'assigned_to' in form.errors

    def test_choices_populated_with_staff(self):
        """Widget choices are populated with pastor/admin members."""
        pastor = MemberFactory(role=Roles.PASTOR, first_name='Jean', last_name='Pasteur')
        admin = MemberFactory(role=Roles.ADMIN, first_name='Marie', last_name='Admin')
        MemberFactory(role=Roles.MEMBER, first_name='Regular', last_name='Member')

        form = HelpRequestAssignForm()
        choices = form.fields['assigned_to'].widget.choices
        choice_ids = [c[0] for c in choices]

        assert str(pastor.id) in choice_ids
        assert str(admin.id) in choice_ids
        # Regular member should not be in staff choices
        assert len(choices) == 2


# =============================================================================
# HELP REQUEST RESOLVE FORM
# =============================================================================


class TestHelpRequestResolveForm:
    """Tests for HelpRequestResolveForm."""

    def test_valid_with_notes(self):
        """Form with resolution notes is valid."""
        data = {'resolution_notes': 'Resolved by providing groceries.'}
        form = HelpRequestResolveForm(data=data)
        assert form.is_valid()

    def test_valid_without_notes(self):
        """Form without resolution notes is valid (field is optional)."""
        data = {'resolution_notes': ''}
        form = HelpRequestResolveForm(data=data)
        assert form.is_valid()

    def test_valid_empty_form(self):
        """Completely empty form is valid (field not required)."""
        data = {}
        form = HelpRequestResolveForm(data=data)
        assert form.is_valid()

    def test_form_fields(self):
        """Form has correct fields."""
        form = HelpRequestResolveForm()
        assert set(form.fields.keys()) == {'resolution_notes'}

    def test_widget(self):
        """Resolution notes uses Textarea with 3 rows."""
        form = HelpRequestResolveForm()
        assert form.fields['resolution_notes'].widget.attrs.get('rows') == 3

    def test_label(self):
        """Form has French label."""
        form = HelpRequestResolveForm()
        assert form.fields['resolution_notes'].label == 'Notes de résolution'
