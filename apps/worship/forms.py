"""Forms for worship service planning."""
from django import forms
from django.utils.translation import gettext_lazy as _

from apps.core.mixins import W3CRMFormMixin
from apps.core.constants import ServiceSectionType
from apps.members.models import Member, Department, DepartmentTaskType
from .models import WorshipService, ServiceSection, ServiceAssignment, EligibleMemberList


class WorshipServiceForm(W3CRMFormMixin, forms.ModelForm):
    """Form for creating/editing worship services."""

    class Meta:
        model = WorshipService
        fields = ['date', 'start_time', 'end_time', 'duration_minutes',
                  'theme', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class ServiceSectionForm(W3CRMFormMixin, forms.ModelForm):
    """Form for adding/editing sections."""

    class Meta:
        model = ServiceSection
        fields = ['name', 'order', 'section_type', 'duration_minutes',
                  'department', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].queryset = Department.objects.filter(is_active=True)
        self.fields['department'].required = False


class ServiceAssignmentForm(W3CRMFormMixin, forms.Form):
    """Form for assigning a member to a section."""

    member = forms.ModelChoiceField(
        queryset=Member.objects.filter(is_active=True),
        label=_('Membre'),
    )

    task_type = forms.ModelChoiceField(
        queryset=DepartmentTaskType.objects.none(),
        required=False,
        label=_('Type de tâche'),
    )

    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label=_('Notes'),
    )

    def __init__(self, *args, section=None, **kwargs):
        super().__init__(*args, **kwargs)
        if section and section.department:
            self.fields['task_type'].queryset = (
                DepartmentTaskType.objects.filter(
                    department=section.department, is_active=True
                )
            )


class EligibleMemberListForm(W3CRMFormMixin, forms.ModelForm):
    """Form for managing which members are eligible for a section type."""

    class Meta:
        model = EligibleMemberList
        fields = ['section_type', 'members', 'department']
        widgets = {
            'members': forms.SelectMultiple(attrs={'size': 10}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['members'].queryset = Member.objects.filter(is_active=True)
        self.fields['department'].queryset = Department.objects.filter(is_active=True)
        self.fields['department'].required = False


class ServiceDateRangeFilterForm(W3CRMFormMixin, forms.Form):
    """Filter form for service list date range."""

    date_from = forms.DateField(
        required=False,
        label=_('Du'),
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    date_to = forms.DateField(
        required=False,
        label=_('Au'),
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
