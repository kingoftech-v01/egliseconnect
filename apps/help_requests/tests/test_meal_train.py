"""Tests for meal train models and views."""
import pytest
from datetime import timedelta
from django.utils import timezone

from apps.core.constants import MealTrainStatus
from apps.help_requests.models import MealTrain, MealSignup
from apps.members.tests.factories import MemberFactory, MemberWithUserFactory
from .factories import MealTrainFactory, MealSignupFactory


@pytest.mark.django_db
class TestMealTrainModel:
    """Tests for MealTrain model."""

    def test_create_meal_train(self):
        train = MealTrainFactory(reason='Post-surgery recovery')
        assert train.reason == 'Post-surgery recovery'
        assert train.status == MealTrainStatus.ACTIVE
        assert train.recipient is not None

    def test_meal_train_str(self):
        train = MealTrainFactory()
        assert str(train.recipient) in str(train)

    def test_meal_train_dates(self):
        today = timezone.now().date()
        end = today + timedelta(days=14)
        train = MealTrainFactory(start_date=today, end_date=end)
        assert train.start_date == today
        assert train.end_date == end

    def test_meal_train_dietary_restrictions(self):
        train = MealTrainFactory(dietary_restrictions='Gluten-free, no dairy')
        assert 'Gluten-free' in train.dietary_restrictions


@pytest.mark.django_db
class TestMealSignupModel:
    """Tests for MealSignup model."""

    def test_create_signup(self):
        signup = MealSignupFactory()
        assert signup.volunteer is not None
        assert signup.confirmed is False

    def test_signup_str(self):
        signup = MealSignupFactory()
        assert str(signup.volunteer) in str(signup)

    def test_confirm_signup(self):
        signup = MealSignupFactory(confirmed=False)
        signup.confirmed = True
        signup.save()
        signup.refresh_from_db()
        assert signup.confirmed is True

    def test_unique_together(self):
        train = MealTrainFactory()
        volunteer = MemberFactory()
        date = (timezone.now() + timedelta(days=1)).date()
        MealSignupFactory(meal_train=train, volunteer=volunteer, date=date)
        with pytest.raises(Exception):
            MealSignupFactory(meal_train=train, volunteer=volunteer, date=date)


@pytest.mark.django_db
class TestMealTrainListView:
    """Tests for meal train list view."""

    def test_list_requires_login(self, client):
        response = client.get('/help-requests/meals/')
        assert response.status_code == 302

    def test_list_accessible(self, client):
        member = MemberWithUserFactory()
        client.force_login(member.user)
        response = client.get('/help-requests/meals/')
        assert response.status_code == 200

    def test_list_shows_trains(self, client):
        member = MemberWithUserFactory()
        client.force_login(member.user)
        MealTrainFactory()
        response = client.get('/help-requests/meals/')
        assert response.status_code == 200


@pytest.mark.django_db
class TestMealTrainCreateView:
    """Tests for creating meal trains."""

    def test_create_requires_pastor(self, client):
        member = MemberWithUserFactory(role='member')
        client.force_login(member.user)
        response = client.get('/help-requests/meals/create/')
        assert response.status_code == 302

    def test_create_get(self, client):
        pastor = MemberWithUserFactory(role='pastor')
        client.force_login(pastor.user)
        response = client.get('/help-requests/meals/create/')
        assert response.status_code == 200

    def test_create_post(self, client):
        pastor = MemberWithUserFactory(role='pastor')
        recipient = MemberFactory()
        client.force_login(pastor.user)
        today = timezone.now().date()
        response = client.post('/help-requests/meals/create/', {
            'recipient': str(recipient.pk),
            'reason': 'New baby',
            'start_date': today.isoformat(),
            'end_date': (today + timedelta(days=14)).isoformat(),
            'dietary_restrictions': '',
        })
        assert response.status_code == 302
        assert MealTrain.objects.filter(recipient=recipient).exists()


@pytest.mark.django_db
class TestMealTrainDetailView:
    """Tests for meal train detail view."""

    def test_detail_view(self, client):
        member = MemberWithUserFactory()
        client.force_login(member.user)
        train = MealTrainFactory()
        response = client.get(f'/help-requests/meals/{train.pk}/')
        assert response.status_code == 200


@pytest.mark.django_db
class TestMealTrainSignupView:
    """Tests for signing up for a meal train."""

    def test_signup_post(self, client):
        member = MemberWithUserFactory()
        client.force_login(member.user)
        train = MealTrainFactory()
        tomorrow = (timezone.now() + timedelta(days=1)).date()

        response = client.post(f'/help-requests/meals/{train.pk}/signup/', {
            'date': tomorrow.isoformat(),
            'notes': 'Will bring pasta',
        })
        assert response.status_code == 302
        assert MealSignup.objects.filter(meal_train=train, volunteer=member).exists()
