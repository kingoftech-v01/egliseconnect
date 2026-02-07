"""Tests for onboarding API views."""
import pytest
from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.core.constants import (
    InterviewStatus,
    LessonStatus,
    MembershipStatus,
    Roles,
)
from apps.members.tests.factories import (
    AdminMemberFactory,
    MemberFactory,
    PastorFactory,
    UserFactory,
)
from apps.onboarding.models import (
    Interview,
    Lesson,
    MemberTraining,
    ScheduledLesson,
    TrainingCourse,
)
from apps.onboarding.tests.factories import (
    InterviewFactory,
    LessonFactory,
    MemberTrainingFactory,
    ScheduledLessonFactory,
    TrainingCourseFactory,
)


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def api_client():
    """DRF API client."""
    return APIClient()


@pytest.fixture
def regular_member(api_client):
    """Authenticated regular member (no onboarding signal)."""
    user = UserFactory()
    member = MemberFactory(
        user=None,
        role=Roles.MEMBER,
        membership_status=MembershipStatus.REGISTERED,
        registration_date=timezone.now() - timedelta(days=5),
        form_deadline=timezone.now() + timedelta(days=25),
    )
    member.user = user
    member.save(update_fields=['user'])
    api_client.force_authenticate(user=user)
    return member


@pytest.fixture
def admin_member(api_client):
    """Authenticated admin member."""
    user = UserFactory()
    member = AdminMemberFactory(
        user=None,
        registration_date=timezone.now() - timedelta(days=60),
        form_deadline=timezone.now() - timedelta(days=30),
        membership_status=MembershipStatus.ACTIVE,
    )
    member.user = user
    member.save(update_fields=['user'])
    api_client.force_authenticate(user=user)
    return member


@pytest.fixture
def pastor_member(api_client):
    """Authenticated pastor member."""
    user = UserFactory()
    member = PastorFactory(
        user=None,
        registration_date=timezone.now() - timedelta(days=60),
        form_deadline=timezone.now() - timedelta(days=30),
        membership_status=MembershipStatus.ACTIVE,
    )
    member.user = user
    member.save(update_fields=['user'])
    api_client.force_authenticate(user=user)
    return member


# ---------------------------------------------------------------------------
# TrainingCourseViewSet
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestTrainingCourseViewSet:
    """Tests for TrainingCourseViewSet (CRUD, IsPastorOrAdmin)."""

    base_url = '/api/v1/onboarding/courses/'

    def test_list_requires_auth(self, api_client):
        """Unauthenticated users are rejected."""
        response = api_client.get(self.base_url)
        assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)

    def test_list_regular_member_denied(self, api_client, regular_member):
        """Regular members are denied access."""
        response = api_client.get(self.base_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_admin_ok(self, api_client, admin_member):
        """Admin can list courses."""
        TrainingCourseFactory.create_batch(3)
        response = api_client.get(self.base_url)
        assert response.status_code == status.HTTP_200_OK

    def test_list_pastor_ok(self, api_client, pastor_member):
        """Pastor can list courses."""
        response = api_client.get(self.base_url)
        assert response.status_code == status.HTTP_200_OK

    def test_create_course(self, api_client, admin_member):
        """Admin can create a course."""
        data = {
            'name': 'API Course',
            'description': 'Created via API',
            'total_lessons': 4,
            'is_default': False,
        }
        response = api_client.post(self.base_url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert TrainingCourse.objects.filter(name='API Course').exists()

    def test_create_regular_member_denied(self, api_client, regular_member):
        """Regular members cannot create courses."""
        data = {'name': 'Blocked', 'total_lessons': 3}
        response = api_client.post(self.base_url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_retrieve_course(self, api_client, admin_member):
        """Admin can retrieve a single course."""
        course = TrainingCourseFactory()
        url = f'{self.base_url}{course.pk}/'
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == course.name

    def test_update_course(self, api_client, admin_member):
        """Admin can update a course."""
        course = TrainingCourseFactory()
        url = f'{self.base_url}{course.pk}/'
        response = api_client.patch(url, {'name': 'Updated Course'})
        assert response.status_code == status.HTTP_200_OK
        course.refresh_from_db()
        assert course.name == 'Updated Course'

    def test_delete_course(self, api_client, admin_member):
        """Admin can delete a course."""
        course = TrainingCourseFactory()
        url = f'{self.base_url}{course.pk}/'
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_response_includes_lessons(self, api_client, admin_member):
        """Course retrieval includes nested lessons."""
        course = TrainingCourseFactory()
        LessonFactory(course=course, order=1)
        LessonFactory(course=course, order=2)
        url = f'{self.base_url}{course.pk}/'
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'lessons' in response.data
        assert len(response.data['lessons']) == 2

    def test_response_includes_lesson_count(self, api_client, admin_member):
        """Course response includes lesson_count field."""
        course = TrainingCourseFactory()
        LessonFactory(course=course, order=1)
        url = f'{self.base_url}{course.pk}/'
        response = api_client.get(url)
        assert response.data['lesson_count'] == 1


# ---------------------------------------------------------------------------
# LessonViewSet
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestLessonViewSet:
    """Tests for LessonViewSet (CRUD, IsPastorOrAdmin, filter by course)."""

    base_url = '/api/v1/onboarding/lessons/'

    def test_list_requires_auth(self, api_client):
        """Unauthenticated users are rejected."""
        response = api_client.get(self.base_url)
        assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)

    def test_list_regular_member_denied(self, api_client, regular_member):
        """Regular members are denied."""
        response = api_client.get(self.base_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_admin_ok(self, api_client, admin_member):
        """Admin can list lessons."""
        course = TrainingCourseFactory()
        LessonFactory(course=course, order=1)
        response = api_client.get(self.base_url)
        assert response.status_code == status.HTTP_200_OK

    def test_filter_by_course(self, api_client, admin_member):
        """Lessons can be filtered by course."""
        course1 = TrainingCourseFactory()
        course2 = TrainingCourseFactory()
        LessonFactory(course=course1, order=1)
        LessonFactory(course=course1, order=2)
        LessonFactory(course=course2, order=1)

        response = api_client.get(self.base_url, {'course': str(course1.pk)})
        assert response.status_code == status.HTTP_200_OK
        # Should only contain lessons from course1
        for lesson_data in response.data['results']:
            assert str(lesson_data['course']) == str(course1.pk)

    def test_create_lesson(self, api_client, admin_member):
        """Admin can create a lesson."""
        course = TrainingCourseFactory()
        data = {
            'course': str(course.pk),
            'order': 1,
            'title': 'New Lesson',
            'duration_minutes': 60,
        }
        response = api_client.post(self.base_url, data)
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_regular_member_denied(self, api_client, regular_member):
        """Regular members cannot create lessons."""
        course = TrainingCourseFactory()
        data = {
            'course': str(course.pk),
            'order': 1,
            'title': 'Blocked',
            'duration_minutes': 60,
        }
        response = api_client.post(self.base_url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_retrieve_lesson(self, api_client, admin_member):
        """Admin can retrieve a lesson."""
        course = TrainingCourseFactory()
        lesson = LessonFactory(course=course, order=1)
        url = f'{self.base_url}{lesson.pk}/'
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == lesson.title

    def test_update_lesson(self, api_client, admin_member):
        """Admin can update a lesson."""
        course = TrainingCourseFactory()
        lesson = LessonFactory(course=course, order=1)
        url = f'{self.base_url}{lesson.pk}/'
        response = api_client.patch(url, {'title': 'Updated Title'})
        assert response.status_code == status.HTTP_200_OK
        lesson.refresh_from_db()
        assert lesson.title == 'Updated Title'

    def test_delete_lesson(self, api_client, admin_member):
        """Admin can delete a lesson."""
        course = TrainingCourseFactory()
        lesson = LessonFactory(course=course, order=1)
        url = f'{self.base_url}{lesson.pk}/'
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT


# ---------------------------------------------------------------------------
# MemberTrainingViewSet
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestMemberTrainingViewSet:
    """Tests for MemberTrainingViewSet (ReadOnly)."""

    base_url = '/api/v1/onboarding/trainings/'

    def test_list_requires_auth(self, api_client):
        """Unauthenticated users are rejected."""
        response = api_client.get(self.base_url)
        assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)

    def test_regular_member_sees_own_only(self, api_client, regular_member):
        """Regular members only see their own trainings."""
        course = TrainingCourseFactory()
        own_training = MemberTrainingFactory(member=regular_member, course=course)
        other_member = MemberFactory(user=None, registration_date=timezone.now())
        MemberTrainingFactory(member=other_member, course=course)

        response = api_client.get(self.base_url)
        assert response.status_code == status.HTTP_200_OK
        ids = [item['id'] for item in response.data['results']]
        assert str(own_training.pk) in ids
        assert len(ids) == 1

    def test_admin_sees_all(self, api_client, admin_member):
        """Admins see all trainings."""
        course = TrainingCourseFactory()
        member1 = MemberFactory(user=None, registration_date=timezone.now())
        member2 = MemberFactory(user=None, registration_date=timezone.now())
        MemberTrainingFactory(member=member1, course=course)
        MemberTrainingFactory(member=member2, course=course)

        response = api_client.get(self.base_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 2

    def test_pastor_sees_all(self, api_client, pastor_member):
        """Pastors see all trainings."""
        course = TrainingCourseFactory()
        member1 = MemberFactory(user=None, registration_date=timezone.now())
        MemberTrainingFactory(member=member1, course=course)

        response = api_client.get(self.base_url)
        assert response.status_code == status.HTTP_200_OK

    def test_readonly_no_create(self, api_client, admin_member):
        """ViewSet is read-only; POST returns 405."""
        course = TrainingCourseFactory()
        member = MemberFactory(user=None, registration_date=timezone.now())
        data = {
            'member': str(member.pk),
            'course': str(course.pk),
        }
        response = api_client.post(self.base_url, data)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_retrieve_training(self, api_client, regular_member):
        """Member can retrieve their own training detail."""
        course = TrainingCourseFactory()
        training = MemberTrainingFactory(member=regular_member, course=course)
        url = f'{self.base_url}{training.pk}/'
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['course_name'] == course.name

    def test_user_without_profile_gets_empty(self, api_client):
        """User without member_profile gets empty queryset."""
        user = UserFactory()
        api_client.force_authenticate(user=user)
        response = api_client.get(self.base_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 0

    def test_response_includes_progress(self, api_client, regular_member):
        """Training response includes progress fields."""
        course = TrainingCourseFactory()
        training = MemberTrainingFactory(member=regular_member, course=course)
        lesson = LessonFactory(course=course, order=1)
        ScheduledLessonFactory(training=training, lesson=lesson, status=LessonStatus.COMPLETED)

        url = f'{self.base_url}{training.pk}/'
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'progress_percentage' in response.data
        assert 'completed_count' in response.data
        assert 'total_count' in response.data
        assert response.data['completed_count'] == 1


# ---------------------------------------------------------------------------
# InterviewViewSet
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestInterviewViewSet:
    """Tests for InterviewViewSet (ReadOnly + accept/counter_propose actions)."""

    base_url = '/api/v1/onboarding/interviews/'

    def test_list_requires_auth(self, api_client):
        """Unauthenticated users are rejected."""
        response = api_client.get(self.base_url)
        assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)

    def test_regular_member_sees_own_only(self, api_client, regular_member):
        """Regular members only see their own interviews."""
        course = TrainingCourseFactory()
        training = MemberTrainingFactory(member=regular_member, course=course)
        own_interview = InterviewFactory(member=regular_member, training=training)

        other_member = MemberFactory(user=None, registration_date=timezone.now())
        other_training = MemberTrainingFactory(member=other_member, course=course)
        InterviewFactory(member=other_member, training=other_training)

        response = api_client.get(self.base_url)
        assert response.status_code == status.HTTP_200_OK
        ids = [item['id'] for item in response.data['results']]
        assert str(own_interview.pk) in ids
        assert len(ids) == 1

    def test_admin_sees_all(self, api_client, admin_member):
        """Admin sees all interviews."""
        course = TrainingCourseFactory()
        member1 = MemberFactory(user=None, registration_date=timezone.now())
        training1 = MemberTrainingFactory(member=member1, course=course)
        InterviewFactory(member=member1, training=training1)
        member2 = MemberFactory(user=None, registration_date=timezone.now())
        training2 = MemberTrainingFactory(member=member2, course=course)
        InterviewFactory(member=member2, training=training2)

        response = api_client.get(self.base_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 2

    def test_readonly_no_create(self, api_client, admin_member):
        """ViewSet is read-only; POST returns 405."""
        data = {'member': 'x', 'training': 'y'}
        response = api_client.post(self.base_url, data)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_retrieve_interview(self, api_client, regular_member):
        """Member can retrieve their own interview."""
        course = TrainingCourseFactory()
        training = MemberTrainingFactory(member=regular_member, course=course)
        interview = InterviewFactory(member=regular_member, training=training)
        url = f'{self.base_url}{interview.pk}/'
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_user_without_profile_gets_empty(self, api_client):
        """User without member_profile gets empty queryset."""
        user = UserFactory()
        api_client.force_authenticate(user=user)
        response = api_client.get(self.base_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 0

    # --- accept action ---

    def test_accept_action(self, api_client, regular_member):
        """POST accept action confirms the interview."""
        course = TrainingCourseFactory()
        training = MemberTrainingFactory(member=regular_member, course=course)
        interviewer = PastorFactory(user=None, registration_date=timezone.now())
        interview = InterviewFactory(
            member=regular_member,
            training=training,
            interviewer=interviewer,
            status=InterviewStatus.PROPOSED,
        )
        url = f'{self.base_url}{interview.pk}/accept/'
        response = api_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'accepted'

        interview.refresh_from_db()
        assert interview.status == InterviewStatus.CONFIRMED

    # --- counter_propose action ---

    def test_counter_propose_action(self, api_client, regular_member):
        """POST counter_propose with valid date changes status."""
        course = TrainingCourseFactory()
        training = MemberTrainingFactory(member=regular_member, course=course)
        interviewer = PastorFactory(user=None, registration_date=timezone.now())
        interview = InterviewFactory(
            member=regular_member,
            training=training,
            interviewer=interviewer,
            status=InterviewStatus.PROPOSED,
        )
        new_date = (timezone.now() + timedelta(days=10)).strftime('%Y-%m-%dT%H:%M:%S')
        url = f'{self.base_url}{interview.pk}/counter_propose/'
        response = api_client.post(url, {'counter_proposed_date': new_date})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'counter_proposed'

        interview.refresh_from_db()
        assert interview.status == InterviewStatus.COUNTER
        assert interview.counter_proposed_date is not None

    def test_counter_propose_without_date(self, api_client, regular_member):
        """POST counter_propose without date returns 400."""
        course = TrainingCourseFactory()
        training = MemberTrainingFactory(member=regular_member, course=course)
        interviewer = PastorFactory(user=None, registration_date=timezone.now())
        interview = InterviewFactory(
            member=regular_member,
            training=training,
            interviewer=interviewer,
        )
        url = f'{self.base_url}{interview.pk}/counter_propose/'
        response = api_client.post(url, {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data

    def test_counter_propose_invalid_date(self, api_client, regular_member):
        """POST counter_propose with invalid date format returns 400."""
        course = TrainingCourseFactory()
        training = MemberTrainingFactory(member=regular_member, course=course)
        interviewer = PastorFactory(user=None, registration_date=timezone.now())
        interview = InterviewFactory(
            member=regular_member,
            training=training,
            interviewer=interviewer,
        )
        url = f'{self.base_url}{interview.pk}/counter_propose/'
        response = api_client.post(url, {'counter_proposed_date': 'not-a-date'})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data

    def test_response_includes_final_date(self, api_client, regular_member):
        """Interview response includes final_date field."""
        course = TrainingCourseFactory()
        training = MemberTrainingFactory(member=regular_member, course=course)
        interview = InterviewFactory(member=regular_member, training=training)
        url = f'{self.base_url}{interview.pk}/'
        response = api_client.get(url)
        assert 'final_date' in response.data


# ---------------------------------------------------------------------------
# OnboardingStatusView
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestOnboardingStatusView:
    """Tests for OnboardingStatusView."""

    url = '/api/v1/onboarding/status/'

    def test_requires_auth(self, api_client):
        """Unauthenticated users are rejected."""
        response = api_client.get(self.url)
        assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)

    def test_no_profile_returns_no_profile(self, api_client):
        """User without member_profile returns status: no_profile."""
        user = UserFactory()
        api_client.force_authenticate(user=user)
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'no_profile'

    def test_returns_member_status_data(self, api_client, regular_member):
        """Returns membership status fields for authenticated member."""
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert 'membership_status' in response.data
        assert 'has_full_access' in response.data
        assert 'can_use_qr' in response.data
        assert 'days_remaining_for_form' in response.data
        assert 'is_form_expired' in response.data

    def test_in_training_includes_training_progress(self, api_client, regular_member):
        """When IN_TRAINING, response includes training progress."""
        regular_member.membership_status = MembershipStatus.IN_TRAINING
        regular_member.save(update_fields=['membership_status'])

        course = TrainingCourseFactory()
        training = MemberTrainingFactory(member=regular_member, course=course)
        lesson = LessonFactory(course=course, order=1)
        ScheduledLessonFactory(training=training, lesson=lesson, status=LessonStatus.COMPLETED)

        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert 'training' in response.data
        training_data = response.data['training']
        assert training_data['course_name'] == course.name
        assert training_data['progress'] == 100
        assert training_data['completed'] == 1
        assert training_data['total'] == 1

    def test_in_training_no_training_object(self, api_client, regular_member):
        """When IN_TRAINING but no MemberTraining exists, no training key."""
        regular_member.membership_status = MembershipStatus.IN_TRAINING
        regular_member.save(update_fields=['membership_status'])

        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert 'training' not in response.data

    def test_registered_status_no_training_key(self, api_client, regular_member):
        """REGISTERED status does not include training key."""
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['membership_status'] == MembershipStatus.REGISTERED
        assert 'training' not in response.data

    def test_active_member_full_access(self, api_client, admin_member):
        """ACTIVE members have has_full_access=True."""
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['has_full_access'] is True


# ---------------------------------------------------------------------------
# OnboardingStatsView
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestOnboardingStatsView:
    """Tests for OnboardingStatsView (admin-only stats endpoint)."""

    url = '/api/v1/onboarding/stats/'

    def test_admin_can_view_stats(self, api_client, admin_member):
        """Admin can view onboarding statistics."""
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert 'pipeline' in response.data
        assert 'success_rate' in response.data
        assert 'avg_completion_days' in response.data
        assert 'training' in response.data
        assert 'interviews' in response.data

    def test_pastor_can_view_stats(self, api_client, pastor_member):
        """Pastor can view onboarding statistics."""
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert 'pipeline' in response.data

    def test_regular_member_denied(self, api_client, regular_member):
        """Regular members are denied access to stats."""
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_denied(self, api_client):
        """Unauthenticated users are denied."""
        response = api_client.get(self.url)
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )
