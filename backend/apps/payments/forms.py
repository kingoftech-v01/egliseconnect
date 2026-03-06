"""Forms for the payments app."""
from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from apps.core.mixins import W3CRMFormMixin
from .models import (
    GivingGoal,
    GivingStatement,
    RecurringDonation,
    RecurringFrequency,
    StatementType,
    PaymentPlan,
    EmployerMatch,
    GivingCampaign,
    CurrencyChoices,
)
from apps.core.constants import DonationType, PledgeFrequency


class DonateForm(W3CRMFormMixin, forms.Form):
    """Donation form for Stripe payment."""
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=1,
        label=_('Montant'),
    )
    donation_type = forms.ChoiceField(
        choices=DonationType.CHOICES,
        label=_('Type de don'),
    )
    campaign_id = forms.UUIDField(
        required=False,
        label=_('Campagne'),
    )
    currency = forms.ChoiceField(
        choices=CurrencyChoices.CHOICES,
        initial=CurrencyChoices.CAD,
        label=_('Devise'),
    )


class GivingGoalForm(W3CRMFormMixin, forms.ModelForm):
    """Form for setting an annual giving goal."""

    class Meta:
        model = GivingGoal
        fields = ['year', 'target_amount']
        widgets = {
            'year': forms.NumberInput(attrs={'min': 2020, 'max': 2099}),
        }

    def __init__(self, *args, **kwargs):
        self.member = kwargs.pop('member', None)
        super().__init__(*args, **kwargs)
        if not self.instance.pk and not self.initial.get('year'):
            self.initial['year'] = timezone.now().year

    def clean(self):
        cleaned_data = super().clean()
        year = cleaned_data.get('year')
        if self.member and year:
            existing = GivingGoal.objects.filter(
                member=self.member, year=year
            ).exclude(pk=self.instance.pk if self.instance.pk else None)
            if existing.exists():
                raise forms.ValidationError(
                    _('Un objectif existe déjà pour cette année.')
                )
        return cleaned_data


class BulkStatementForm(W3CRMFormMixin, forms.Form):
    """Form for bulk statement generation (admin)."""
    period_start = forms.DateField(
        label=_('Début de la période'),
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    period_end = forms.DateField(
        label=_('Fin de la période'),
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    statement_type = forms.ChoiceField(
        choices=StatementType.CHOICES,
        label=_('Type de relevé'),
    )

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('period_start')
        end = cleaned_data.get('period_end')
        if start and end and start > end:
            raise forms.ValidationError(
                _('La date de début doit être avant la date de fin.')
            )
        return cleaned_data


class EditRecurringForm(W3CRMFormMixin, forms.Form):
    """Form for editing recurring donation amount and frequency."""
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=1,
        label=_('Nouveau montant'),
    )
    frequency = forms.ChoiceField(
        choices=RecurringFrequency.CHOICES,
        label=_('Fréquence'),
    )


class PaymentPlanForm(W3CRMFormMixin, forms.ModelForm):
    """Form for creating a payment plan."""

    class Meta:
        model = PaymentPlan
        fields = ['total_amount', 'installment_amount', 'frequency', 'start_date', 'donation_type']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        total = cleaned_data.get('total_amount')
        installment = cleaned_data.get('installment_amount')
        if total and installment:
            if installment > total:
                raise forms.ValidationError(
                    _('Le montant par versement ne peut pas dépasser le montant total.')
                )
            if installment <= 0:
                raise forms.ValidationError(
                    _('Le montant par versement doit être supérieur à zéro.')
                )
        return cleaned_data


class EmployerMatchForm(W3CRMFormMixin, forms.ModelForm):
    """Form for submitting employer matching info."""

    class Meta:
        model = EmployerMatch
        fields = ['employer_name', 'match_ratio', 'annual_cap']


class GivingCampaignForm(W3CRMFormMixin, forms.ModelForm):
    """Form for creating/editing a giving campaign."""

    class Meta:
        model = GivingCampaign
        fields = ['name', 'description', 'goal_amount', 'start_date', 'end_date', 'is_year_end', 'image']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_date')
        end = cleaned_data.get('end_date')
        if start and end and start > end:
            raise forms.ValidationError(
                _('La date de début doit être avant la date de fin.')
            )
        return cleaned_data
