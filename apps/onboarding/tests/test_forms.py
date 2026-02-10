"""Tests for onboarding forms."""
import pytest
from django.utils import timezone
from datetime import timedelta

from apps.core.constants import Province, FamilyStatus
from apps.onboarding.forms import (
    OnboardingProfileForm,
    TrainingCourseForm,
    LessonForm,
    ScheduleLessonForm,
    ScheduleInterviewForm,
    InterviewCounterProposeForm,
    InterviewResultForm,
    AdminReviewForm,
)
from apps.members.tests.factories import MemberFactory, PastorFactory
from .factories import TrainingCourseFactory, LessonFactory, MemberTrainingFactory


@pytest.mark.django_db
class TestOnboardingProfileForm:
    """Tests for OnboardingProfileForm."""

    def _get_valid_data(self, **overrides):
        """Return valid form data with optional overrides."""
        data = {
            'first_name': 'Jean',
            'last_name': 'Dupont',
            'province': Province.QC,
            'family_status': FamilyStatus.SINGLE,
        }
        data.update(overrides)
        return data

    def test_valid_form(self):
        """Form is valid with required fields only."""
        form = OnboardingProfileForm(data=self._get_valid_data())
        assert form.is_valid(), form.errors

    def test_first_name_required(self):
        """First name is a required field."""
        form = OnboardingProfileForm(data=self._get_valid_data(first_name=''))
        assert not form.is_valid()
        assert 'first_name' in form.errors

    def test_last_name_required(self):
        """Last name is a required field."""
        form = OnboardingProfileForm(data=self._get_valid_data(last_name=''))
        assert not form.is_valid()
        assert 'last_name' in form.errors

    def test_optional_fields(self):
        """Email, phone, birth_date, address, city, postal_code, photo are optional."""
        data = self._get_valid_data(
            email='jean@example.com',
            phone='514-555-0123',
            birth_date='1990-01-15',
            address='123 Rue Test',
            city='Montreal',
            postal_code='H1A 1A1',
        )
        form = OnboardingProfileForm(data=data)
        assert form.is_valid(), form.errors

    def test_province_required(self):
        """Province field is required in form."""
        data = self._get_valid_data()
        del data['province']
        form = OnboardingProfileForm(data=data)
        assert not form.is_valid()
        assert 'province' in form.errors

    def test_family_status_required(self):
        """Family status field is required in form."""
        data = self._get_valid_data()
        del data['family_status']
        form = OnboardingProfileForm(data=data)
        assert not form.is_valid()
        assert 'family_status' in form.errors


@pytest.mark.django_db
class TestTrainingCourseForm:
    """Tests for TrainingCourseForm."""

    def _get_valid_data(self, **overrides):
        """Return valid form data with optional overrides."""
        data = {
            'name': 'Parcours de formation',
            'total_lessons': 5,
        }
        data.update(overrides)
        return data

    def test_valid_form(self):
        """Form is valid with required fields only."""
        form = TrainingCourseForm(data=self._get_valid_data())
        assert form.is_valid(), form.errors

    def test_name_required(self):
        """Name is a required field."""
        form = TrainingCourseForm(data=self._get_valid_data(name=''))
        assert not form.is_valid()
        assert 'name' in form.errors

    def test_description_optional(self):
        """Description is an optional field."""
        data = self._get_valid_data(description='Description détaillée du parcours')
        form = TrainingCourseForm(data=data)
        assert form.is_valid(), form.errors

    def test_total_lessons_required(self):
        """Total lessons field is required in form."""
        data = self._get_valid_data()
        del data['total_lessons']
        form = TrainingCourseForm(data=data)
        assert not form.is_valid()
        assert 'total_lessons' in form.errors

    def test_is_default_optional(self):
        """Is default field is optional (BooleanField with default)."""
        form = TrainingCourseForm(data=self._get_valid_data())
        assert form.is_valid(), form.errors


@pytest.mark.django_db
class TestLessonForm:
    """Tests for LessonForm."""

    def _get_valid_data(self, **overrides):
        """Return valid form data with optional overrides."""
        data = {
            'order': 1,
            'title': 'Introduction',
            'duration_minutes': 90,
        }
        data.update(overrides)
        return data

    def test_valid_with_duration_minutes(self):
        """Form is valid with all required fields including duration_minutes."""
        form = LessonForm(data=self._get_valid_data())
        assert form.is_valid(), form.errors

    def test_order_required(self):
        """Order is a required field."""
        data = self._get_valid_data()
        del data['order']
        form = LessonForm(data=data)
        assert not form.is_valid()
        assert 'order' in form.errors

    def test_title_required(self):
        """Title is a required field."""
        form = LessonForm(data=self._get_valid_data(title=''))
        assert not form.is_valid()
        assert 'title' in form.errors

    def test_duration_minutes_required(self):
        """Duration minutes is a required field (no blank=True in model)."""
        data = self._get_valid_data()
        del data['duration_minutes']
        form = LessonForm(data=data)
        assert not form.is_valid()
        assert 'duration_minutes' in form.errors

    def test_optional_fields(self):
        """Description, materials_pdf, materials_notes are optional."""
        data = self._get_valid_data(
            description='Leçon détaillée',
            materials_notes='Notes complémentaires',
        )
        form = LessonForm(data=data)
        assert form.is_valid(), form.errors


@pytest.mark.django_db
class TestScheduleLessonForm:
    """Tests for ScheduleLessonForm."""

    def _get_valid_data(self, **overrides):
        """Return valid form data with optional overrides."""
        future_date = (timezone.now() + timedelta(days=7)).strftime('%Y-%m-%dT%H:%M')
        data = {
            'scheduled_date': future_date,
        }
        data.update(overrides)
        return data

    def test_valid_form(self):
        """Form is valid with required fields only."""
        form = ScheduleLessonForm(data=self._get_valid_data())
        assert form.is_valid(), form.errors

    def test_scheduled_date_required(self):
        """Scheduled date is a required field."""
        data = self._get_valid_data()
        del data['scheduled_date']
        form = ScheduleLessonForm(data=data)
        assert not form.is_valid()
        assert 'scheduled_date' in form.errors

    def test_location_optional(self):
        """Location is an optional field."""
        data = self._get_valid_data(location='Salle de réunion A')
        form = ScheduleLessonForm(data=data)
        assert form.is_valid(), form.errors


@pytest.mark.django_db
class TestScheduleInterviewForm:
    """Tests for ScheduleInterviewForm."""

    def _get_valid_data(self, **overrides):
        """Return valid form data with optional overrides."""
        pastor = PastorFactory()
        future_date = (timezone.now() + timedelta(days=14)).strftime('%Y-%m-%dT%H:%M')
        data = {
            'proposed_date': future_date,
            'interviewer': pastor.pk,
        }
        data.update(overrides)
        return data

    def test_valid_form(self):
        """Form is valid with required fields."""
        form = ScheduleInterviewForm(data=self._get_valid_data())
        assert form.is_valid(), form.errors

    def test_proposed_date_required(self):
        """Proposed date is a required field."""
        data = self._get_valid_data()
        del data['proposed_date']
        form = ScheduleInterviewForm(data=data)
        assert not form.is_valid()
        assert 'proposed_date' in form.errors

    def test_location_optional(self):
        """Location is an optional field."""
        data = self._get_valid_data(location='Bureau du pasteur')
        form = ScheduleInterviewForm(data=data)
        assert form.is_valid(), form.errors

    def test_interviewer_required(self):
        """Interviewer is required (FK with null=True but no blank=True)."""
        data = self._get_valid_data()
        del data['interviewer']
        form = ScheduleInterviewForm(data=data)
        assert not form.is_valid()
        assert 'interviewer' in form.errors

    def test_interviewer_with_valid_member(self):
        """Form accepts a valid interviewer member pk."""
        pastor = PastorFactory()
        data = self._get_valid_data(interviewer=pastor.pk)
        form = ScheduleInterviewForm(data=data)
        assert form.is_valid(), form.errors


@pytest.mark.django_db
class TestInterviewCounterProposeForm:
    """Tests for InterviewCounterProposeForm."""

    def _get_valid_data(self, **overrides):
        """Return valid form data with optional overrides."""
        future_date = (timezone.now() + timedelta(days=10)).strftime('%Y-%m-%dT%H:%M')
        data = {
            'counter_proposed_date': future_date,
        }
        data.update(overrides)
        return data

    def test_valid_form(self):
        """Form is valid with counter proposed date."""
        form = InterviewCounterProposeForm(data=self._get_valid_data())
        assert form.is_valid(), form.errors

    def test_counter_proposed_date_required(self):
        """Counter proposed date is a required field."""
        data = self._get_valid_data()
        del data['counter_proposed_date']
        form = InterviewCounterProposeForm(data=data)
        assert not form.is_valid()
        assert 'counter_proposed_date' in form.errors

    def test_invalid_date_format(self):
        """Invalid date format should fail validation."""
        data = self._get_valid_data(counter_proposed_date='invalid-date')
        form = InterviewCounterProposeForm(data=data)
        assert not form.is_valid()
        assert 'counter_proposed_date' in form.errors


@pytest.mark.django_db
class TestInterviewResultForm:
    """Tests for InterviewResultForm."""

    def _get_valid_data(self, **overrides):
        """Return valid form data with optional overrides."""
        data = {}
        data.update(overrides)
        return data

    def test_valid_form_empty(self):
        """Form is valid with no data (all fields optional)."""
        form = InterviewResultForm(data=self._get_valid_data())
        assert form.is_valid(), form.errors

    def test_passed_optional(self):
        """Passed field is optional (BooleanField with required=False)."""
        data = self._get_valid_data(passed=True)
        form = InterviewResultForm(data=data)
        assert form.is_valid(), form.errors

    def test_result_notes_optional(self):
        """Result notes field is optional."""
        data = self._get_valid_data(result_notes='Excellent candidat')
        form = InterviewResultForm(data=data)
        assert form.is_valid(), form.errors

    def test_both_fields_provided(self):
        """Form is valid with both fields provided."""
        data = self._get_valid_data(
            passed=True,
            result_notes='Le membre a bien répondu aux questions',
        )
        form = InterviewResultForm(data=data)
        assert form.is_valid(), form.errors


@pytest.mark.django_db
class TestAdminReviewForm:
    """Tests for AdminReviewForm."""

    def _get_valid_data(self, **overrides):
        """Return valid form data with optional overrides."""
        data = {
            'action': 'approve',
        }
        data.update(overrides)
        return data

    def test_valid_form_approve(self):
        """Form is valid with approve action."""
        form = AdminReviewForm(data=self._get_valid_data())
        assert form.is_valid(), form.errors

    def test_action_required(self):
        """Action is a required field."""
        data = self._get_valid_data()
        del data['action']
        form = AdminReviewForm(data=data)
        assert not form.is_valid()
        assert 'action' in form.errors

    def test_action_reject(self):
        """Form accepts reject action."""
        data = self._get_valid_data(action='reject')
        form = AdminReviewForm(data=data)
        assert form.is_valid(), form.errors

    def test_action_request_changes(self):
        """Form accepts request_changes action."""
        data = self._get_valid_data(action='request_changes')
        form = AdminReviewForm(data=data)
        assert form.is_valid(), form.errors

    def test_invalid_action(self):
        """Form rejects invalid action choices."""
        data = self._get_valid_data(action='invalid_action')
        form = AdminReviewForm(data=data)
        assert not form.is_valid()
        assert 'action' in form.errors

    def test_course_optional(self):
        """Course field is optional (required=False)."""
        form = AdminReviewForm(data=self._get_valid_data())
        assert form.is_valid(), form.errors

    def test_course_with_valid_course(self):
        """Form accepts a valid active TrainingCourse pk."""
        course = TrainingCourseFactory(is_active=True)
        data = self._get_valid_data(course=course.pk)
        form = AdminReviewForm(data=data)
        assert form.is_valid(), form.errors

    def test_reason_optional(self):
        """Reason field is optional."""
        data = self._get_valid_data(reason='Dossier incomplet')
        form = AdminReviewForm(data=data)
        assert form.is_valid(), form.errors

    def test_all_fields_provided(self):
        """Form is valid with all fields provided."""
        course = TrainingCourseFactory(is_active=True)
        data = self._get_valid_data(
            action='approve',
            course=course.pk,
            reason='Dossier conforme',
        )
        form = AdminReviewForm(data=data)
        assert form.is_valid(), form.errors
