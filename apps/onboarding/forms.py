"""Forms for the onboarding process."""
from django import forms
from django.utils.translation import gettext_lazy as _

from apps.core.mixins import W3CRMFormMixin
from apps.core.constants import FamilyStatus, Province
from apps.members.models import Member
from .models import TrainingCourse, Lesson, ScheduledLesson, Interview


class OnboardingProfileForm(W3CRMFormMixin, forms.ModelForm):
    """The mandatory form a new member must fill within 30 days."""

    class Meta:
        model = Member
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'phone_secondary',
            'birth_date', 'address', 'city', 'province', 'postal_code',
            'photo', 'family_status',
        ]
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 2}),
        }


class TrainingCourseForm(W3CRMFormMixin, forms.ModelForm):
    """Admin form for creating/editing training courses."""

    class Meta:
        model = TrainingCourse
        fields = ['name', 'description', 'total_lessons', 'is_default']


class LessonForm(W3CRMFormMixin, forms.ModelForm):
    """Admin form for creating/editing lessons."""

    class Meta:
        model = Lesson
        fields = ['order', 'title', 'description', 'duration_minutes',
                  'materials_pdf', 'materials_notes']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'materials_notes': forms.Textarea(attrs={'rows': 5}),
        }


class ScheduleLessonForm(W3CRMFormMixin, forms.ModelForm):
    """Admin form for scheduling lessons for a member."""

    class Meta:
        model = ScheduledLesson
        fields = ['scheduled_date', 'location']
        widgets = {
            'scheduled_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
        }


class ScheduleInterviewForm(W3CRMFormMixin, forms.ModelForm):
    """Admin form for scheduling an interview."""

    class Meta:
        model = Interview
        fields = ['proposed_date', 'location', 'interviewer']
        widgets = {
            'proposed_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
        }


class InterviewCounterProposeForm(W3CRMFormMixin, forms.Form):
    """Member form for proposing an alternative interview date."""

    counter_proposed_date = forms.DateTimeField(
        label=_('Date proposée'),
        widget=forms.DateTimeInput(
            attrs={'type': 'datetime-local'},
            format='%Y-%m-%dT%H:%M',
        ),
    )


class InterviewResultForm(W3CRMFormMixin, forms.Form):
    """Admin form for recording interview results."""

    passed = forms.BooleanField(
        required=False,
        label=_('Interview réussie'),
    )

    result_notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        required=False,
        label=_('Notes'),
    )


class AdminReviewForm(W3CRMFormMixin, forms.Form):
    """Admin form for reviewing a member's application."""

    ACTION_CHOICES = [
        ('approve', _('Approuver')),
        ('reject', _('Refuser')),
        ('request_changes', _('Demander des compléments')),
    ]

    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.RadioSelect,
        label=_('Action'),
    )

    course = forms.ModelChoiceField(
        queryset=TrainingCourse.objects.filter(is_active=True),
        required=False,
        label=_('Parcours de formation'),
        help_text=_('Requis si vous approuvez'),
    )

    reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        label=_('Raison / Message'),
        help_text=_('Requis si vous refusez ou demandez des compléments'),
    )
