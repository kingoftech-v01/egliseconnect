"""Volunteer forms."""
from django import forms
from django.utils.translation import gettext_lazy as _

from apps.core.mixins import W3CRMFormMixin
from apps.members.models import Member
from .models import (
    VolunteerPosition, VolunteerSchedule, SwapRequest,
    VolunteerHours, VolunteerBackgroundCheck, TeamAnnouncement,
    PositionChecklist, Skill, VolunteerSkill, AvailabilitySlot,
    CrossTraining,
)


class VolunteerPositionForm(W3CRMFormMixin, forms.ModelForm):
    class Meta:
        model = VolunteerPosition
        fields = ['name', 'role_type', 'description', 'min_volunteers', 'max_volunteers', 'skills_required']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'skills_required': forms.Textarea(attrs={'rows': 3}),
        }


class VolunteerScheduleForm(W3CRMFormMixin, forms.ModelForm):
    class Meta:
        model = VolunteerSchedule
        fields = ['member', 'position', 'event', 'date', 'status', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'member': forms.Select(attrs={'data-search': 'true'}),
        }


class SwapRequestForm(W3CRMFormMixin, forms.ModelForm):
    """Form for creating a swap request between two volunteers."""

    requesting_schedule = forms.ModelChoiceField(
        queryset=VolunteerSchedule.objects.none(),
        label=_('Mon horaire'),
    )
    target_member = forms.ModelChoiceField(
        queryset=Member.objects.filter(is_active=True),
        label=_('Echanger avec'),
    )
    target_schedule = forms.ModelChoiceField(
        queryset=VolunteerSchedule.objects.none(),
        label=_('Horaire cible'),
        required=False,
    )
    reason = forms.CharField(
        label=_('Raison'),
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': "Raison de la demande d'echange (optionnel)..."}),
    )

    class Meta:
        model = SwapRequest
        fields = ['requesting_schedule', 'target_member', 'target_schedule', 'reason']

    def __init__(self, *args, member=None, **kwargs):
        super().__init__(*args, **kwargs)
        if member:
            from django.utils import timezone
            self.fields['requesting_schedule'].queryset = VolunteerSchedule.objects.filter(
                member=member,
                date__gte=timezone.now().date(),
                is_active=True,
            ).select_related('position').order_by('date')

        if self.data.get('target_member'):
            try:
                from django.utils import timezone
                target_member_id = self.data.get('target_member')
                self.fields['target_schedule'].queryset = VolunteerSchedule.objects.filter(
                    member_id=target_member_id,
                    date__gte=timezone.now().date(),
                    is_active=True,
                ).select_related('position').order_by('date')
            except (ValueError, TypeError):
                pass

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.original_schedule = self.cleaned_data['requesting_schedule']
        instance.requested_by = self.cleaned_data['requesting_schedule'].member
        instance.swap_with = self.cleaned_data['target_member']
        if commit:
            instance.save()
        return instance


# ──────────────────────────────────────────────────────────────────────────────
# P1: Volunteer Hours
# ──────────────────────────────────────────────────────────────────────────────

class VolunteerHoursForm(W3CRMFormMixin, forms.ModelForm):
    """Form for logging volunteer hours."""

    class Meta:
        model = VolunteerHours
        fields = ['member', 'position', 'date', 'hours_worked', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'member': forms.Select(attrs={'data-search': 'true'}),
        }


class VolunteerHoursSelfForm(W3CRMFormMixin, forms.ModelForm):
    """Form for a volunteer to self-report hours (no member field)."""

    class Meta:
        model = VolunteerHours
        fields = ['position', 'date', 'hours_worked', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }


# ──────────────────────────────────────────────────────────────────────────────
# P1: Background Check
# ──────────────────────────────────────────────────────────────────────────────

class VolunteerBackgroundCheckForm(W3CRMFormMixin, forms.ModelForm):
    """Form for managing background check records."""

    class Meta:
        model = VolunteerBackgroundCheck
        fields = ['member', 'position', 'status', 'check_date', 'expiry_date', 'notes']
        widgets = {
            'check_date': forms.DateInput(attrs={'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'member': forms.Select(attrs={'data-search': 'true'}),
        }


# ──────────────────────────────────────────────────────────────────────────────
# P1: Team Communication
# ──────────────────────────────────────────────────────────────────────────────

class TeamAnnouncementForm(W3CRMFormMixin, forms.ModelForm):
    """Form for creating team announcements."""

    class Meta:
        model = TeamAnnouncement
        fields = ['position', 'title', 'body']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 5}),
        }


# ──────────────────────────────────────────────────────────────────────────────
# P2: Onboarding Checklist
# ──────────────────────────────────────────────────────────────────────────────

class PositionChecklistForm(W3CRMFormMixin, forms.ModelForm):
    """Form for creating/editing checklist items."""

    class Meta:
        model = PositionChecklist
        fields = ['position', 'title', 'description', 'order', 'is_required']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


# ──────────────────────────────────────────────────────────────────────────────
# P2: Skills
# ──────────────────────────────────────────────────────────────────────────────

class SkillForm(W3CRMFormMixin, forms.ModelForm):
    """Form for managing skills."""

    class Meta:
        model = Skill
        fields = ['name', 'category', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class VolunteerSkillForm(W3CRMFormMixin, forms.ModelForm):
    """Form for assigning skills to volunteers."""

    class Meta:
        model = VolunteerSkill
        fields = ['member', 'skill', 'proficiency_level', 'certified_at']
        widgets = {
            'certified_at': forms.DateInput(attrs={'type': 'date'}),
            'member': forms.Select(attrs={'data-search': 'true'}),
        }


class VolunteerSkillSelfForm(W3CRMFormMixin, forms.ModelForm):
    """Form for volunteers to self-report skills (no member field)."""

    class Meta:
        model = VolunteerSkill
        fields = ['skill', 'proficiency_level', 'certified_at']
        widgets = {
            'certified_at': forms.DateInput(attrs={'type': 'date'}),
        }


# ──────────────────────────────────────────────────────────────────────────────
# P3: Availability Slots
# ──────────────────────────────────────────────────────────────────────────────

class AvailabilitySlotForm(W3CRMFormMixin, forms.ModelForm):
    """Form for submitting availability time slots."""

    class Meta:
        model = AvailabilitySlot
        fields = ['day_of_week', 'time_start', 'time_end', 'is_available']
        widgets = {
            'time_start': forms.TimeInput(attrs={'type': 'time'}),
            'time_end': forms.TimeInput(attrs={'type': 'time'}),
        }


# ──────────────────────────────────────────────────────────────────────────────
# P3: Cross-Training
# ──────────────────────────────────────────────────────────────────────────────

class CrossTrainingForm(W3CRMFormMixin, forms.ModelForm):
    """Form for recording cross-training between positions."""

    class Meta:
        model = CrossTraining
        fields = ['member', 'original_position', 'trained_position', 'certified_at', 'notes']
        widgets = {
            'certified_at': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'member': forms.Select(attrs={'data-search': 'true'}),
        }
