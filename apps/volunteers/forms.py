"""Volunteer forms."""
from django import forms
from django.utils.translation import gettext_lazy as _

from apps.core.mixins import W3CRMFormMixin
from apps.members.models import Member
from .models import VolunteerPosition, VolunteerSchedule, SwapRequest


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
        label=_('Échanger avec'),
    )
    target_schedule = forms.ModelChoiceField(
        queryset=VolunteerSchedule.objects.none(),
        label=_('Horaire cible'),
        required=False,
    )
    reason = forms.CharField(
        label=_('Raison'),
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': "Raison de la demande d'échange (optionnel)..."}),
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
