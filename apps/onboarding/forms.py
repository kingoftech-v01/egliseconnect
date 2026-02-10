"""Forms for the onboarding process."""
from django import forms
from django.utils.translation import gettext_lazy as _

from apps.core.mixins import W3CRMFormMixin
from apps.core.constants import FamilyStatus, Province, Roles
from apps.members.models import Member
from .models import TrainingCourse, Lesson, ScheduledLesson, Interview, InvitationCode


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


class InvitationCreateForm(W3CRMFormMixin, forms.Form):
    """Admin form for creating an invitation code."""

    ROLE_CHOICES = [(r[0], r[1]) for r in Roles.CHOICES]

    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        initial=Roles.MEMBER,
        label=_('Rôle assigné'),
    )

    expires_in_days = forms.IntegerField(
        initial=30,
        min_value=1,
        max_value=365,
        label=_('Expire dans (jours)'),
    )

    max_uses = forms.IntegerField(
        initial=1,
        min_value=1,
        max_value=100,
        label=_('Utilisations max'),
    )

    skip_onboarding = forms.BooleanField(
        required=False,
        initial=False,
        label=_('Passer le parcours'),
        help_text=_('Le membre devient actif immédiatement (pour membres pré-existants)'),
    )

    note = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label=_('Note'),
    )


class InvitationEditForm(W3CRMFormMixin, forms.ModelForm):
    """Admin form for editing an existing invitation code."""

    class Meta:
        model = InvitationCode
        fields = ['role', 'expires_at', 'max_uses', 'skip_onboarding', 'note', 'is_active']
        widgets = {
            'expires_at': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
            'note': forms.Textarea(attrs={'rows': 2}),
        }


class InvitationAcceptForm(W3CRMFormMixin, forms.Form):
    """Form for a member to accept an invitation code."""

    code = forms.CharField(
        max_length=32,
        label=_('Code d\'invitation'),
        widget=forms.TextInput(attrs={
            'placeholder': 'Ex: AB12CD34',
            'class': 'form-control text-uppercase',
        }),
    )

    def clean_code(self):
        code = self.cleaned_data['code'].upper().strip()
        try:
            invitation = InvitationCode.objects.get(code=code)
        except InvitationCode.DoesNotExist:
            raise forms.ValidationError(_('Code d\'invitation invalide.'))

        if not invitation.is_usable:
            raise forms.ValidationError(_('Ce code d\'invitation a expiré ou a été utilisé.'))

        self.invitation = invitation
        return code
