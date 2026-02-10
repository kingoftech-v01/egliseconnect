"""Forms for donation management."""
from django import forms
from django.utils.translation import gettext_lazy as _

from apps.core.constants import DonationType, PaymentMethod
from apps.core.mixins import W3CRMFormMixin

from .models import Donation, DonationCampaign


class DonationForm(W3CRMFormMixin, forms.ModelForm):
    """Online donation form for members."""

    class Meta:
        model = Donation
        fields = [
            'amount',
            'donation_type',
            'campaign',
            'notes',
        ]
        widgets = {
            'amount': forms.NumberInput(attrs={
                'min': '1',
                'step': '0.01',
                'placeholder': _('Montant en $')
            }),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['campaign'].queryset = DonationCampaign.objects.filter(
            is_active=True
        )
        self.fields['campaign'].required = False

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise forms.ValidationError(_('Le montant doit être positif.'))
        return amount


class PhysicalDonationForm(W3CRMFormMixin, forms.ModelForm):
    """Form for treasurer to record cash, check, and other physical donations."""

    class Meta:
        model = Donation
        fields = [
            'member',
            'amount',
            'donation_type',
            'payment_method',
            'date',
            'campaign',
            'check_number',
            'notes',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'amount': forms.NumberInput(attrs={
                'min': '1',
                'step': '0.01',
            }),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only allow physical payment methods
        self.fields['payment_method'].choices = [
            (PaymentMethod.CASH, _('Espèces')),
            (PaymentMethod.CHECK, _('Chèque')),
            (PaymentMethod.BANK_TRANSFER, _('Virement bancaire')),
            (PaymentMethod.OTHER, _('Autre')),
        ]
        self.fields['campaign'].queryset = DonationCampaign.objects.filter(
            is_active=True
        )
        self.fields['campaign'].required = False

    def clean(self):
        """Check payments require a check number."""
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        check_number = cleaned_data.get('check_number')

        if payment_method == PaymentMethod.CHECK and not check_number:
            self.add_error('check_number', _('Le numéro de chèque est requis.'))

        return cleaned_data


class DonationCampaignForm(W3CRMFormMixin, forms.ModelForm):
    """Form for creating and editing donation campaigns."""

    class Meta:
        model = DonationCampaign
        fields = [
            'name',
            'description',
            'goal_amount',
            'start_date',
            'end_date',
            'image',
            'is_active',
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'goal_amount': forms.NumberInput(attrs={
                'min': '0',
                'step': '0.01',
            }),
        }

    def clean(self):
        """End date must be after start date."""
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and end_date < start_date:
            self.add_error('end_date', _('La date de fin doit être après la date de début.'))

        return cleaned_data


class DonationEditForm(W3CRMFormMixin, forms.ModelForm):
    """Form for finance staff to edit a donation."""

    class Meta:
        model = Donation
        fields = [
            'amount',
            'donation_type',
            'payment_method',
            'date',
            'campaign',
            'check_number',
            'notes',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'amount': forms.NumberInput(attrs={
                'min': '1',
                'step': '0.01',
            }),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['campaign'].queryset = DonationCampaign.objects.filter(
            is_active=True
        )
        self.fields['campaign'].required = False

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise forms.ValidationError(_('Le montant doit être positif.'))
        return amount


class DonationFilterForm(W3CRMFormMixin, forms.Form):
    """Filter form for donation list."""

    date_from = forms.DateField(
        required=False,
        label=_('Du'),
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    date_to = forms.DateField(
        required=False,
        label=_('Au'),
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    donation_type = forms.ChoiceField(
        required=False,
        label=_('Type'),
        choices=[('', _('Tous'))] + list(DonationType.CHOICES)
    )

    payment_method = forms.ChoiceField(
        required=False,
        label=_('Mode de paiement'),
        choices=[('', _('Tous'))] + list(PaymentMethod.CHOICES)
    )

    campaign = forms.ModelChoiceField(
        required=False,
        label=_('Campagne'),
        queryset=DonationCampaign.objects.all(),
        empty_label=_('Toutes')
    )

    member = forms.CharField(
        required=False,
        label=_('Membre'),
        widget=forms.TextInput(attrs={'placeholder': _('Nom ou numéro')})
    )


class DonationReportForm(W3CRMFormMixin, forms.Form):
    """Form for generating donation reports."""

    PERIOD_CHOICES = [
        ('month', _('Mois')),
        ('quarter', _('Trimestre')),
        ('year', _('Année')),
        ('custom', _('Personnalisé')),
    ]

    period = forms.ChoiceField(
        choices=PERIOD_CHOICES,
        label=_('Période')
    )

    year = forms.IntegerField(
        required=False,
        label=_('Année'),
        min_value=2000,
        max_value=2100
    )

    month = forms.IntegerField(
        required=False,
        label=_('Mois'),
        min_value=1,
        max_value=12
    )

    date_from = forms.DateField(
        required=False,
        label=_('Du'),
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    date_to = forms.DateField(
        required=False,
        label=_('Au'),
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    group_by = forms.ChoiceField(
        choices=[
            ('type', _('Par type')),
            ('method', _('Par mode de paiement')),
            ('campaign', _('Par campagne')),
            ('member', _('Par membre')),
        ],
        label=_('Regrouper par')
    )
