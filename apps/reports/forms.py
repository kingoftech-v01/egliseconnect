"""Reports forms for scheduled reports and saved reports."""
from django import forms
from django.utils.translation import gettext_lazy as _

from apps.core.mixins import W3CRMFormMixin
from .models import ReportSchedule, SavedReport


class ReportScheduleForm(W3CRMFormMixin, forms.ModelForm):
    """Form for creating/editing scheduled reports."""

    class Meta:
        model = ReportSchedule
        fields = [
            'name', 'report_type', 'frequency', 'recipients',
            'is_active', 'next_run_at', 'filters_json', 'template_name',
        ]
        widgets = {
            'next_run_at': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
            'recipients': forms.SelectMultiple(attrs={'size': '8'}),
        }


class SavedReportForm(W3CRMFormMixin, forms.ModelForm):
    """Form for creating/editing saved reports."""

    class Meta:
        model = SavedReport
        fields = [
            'name', 'report_type', 'filters_json', 'columns_json',
            'shared_with',
        ]
        widgets = {
            'shared_with': forms.SelectMultiple(attrs={'size': '8'}),
        }


class DateRangeFilterForm(forms.Form):
    """Reusable date range filter for report views."""
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label=_('Date de debut'),
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label=_('Date de fin'),
    )
