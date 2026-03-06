"""Help Requests forms."""
from django import forms
from django.utils.translation import gettext_lazy as _

from apps.core.mixins import W3CRMFormMixin
from .models import (
    HelpRequest, HelpRequestCategory, HelpRequestComment,
    PastoralCare, PrayerRequest, CareTeam, CareTeamMember,
    BenevolenceRequest, BenevolenceFund,
    MealTrain, MealSignup,
    CrisisProtocol, CrisisResource,
)


class HelpRequestForm(W3CRMFormMixin, forms.ModelForm):
    class Meta:
        model = HelpRequest
        fields = ['category', 'title', 'description', 'urgency', 'is_confidential']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }
        labels = {
            'category': _('Catégorie'),
            'title': _('Titre'),
            'description': _('Description'),
            'urgency': _('Urgence'),
            'is_confidential': _('Confidentiel (visible uniquement par les pasteurs)'),
        }


class HelpRequestCommentForm(W3CRMFormMixin, forms.ModelForm):
    class Meta:
        model = HelpRequestComment
        fields = ['content', 'is_internal']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'content': _('Commentaire'),
            'is_internal': _('Note interne (visible uniquement par le staff)'),
        }


class HelpRequestAssignForm(W3CRMFormMixin, forms.Form):
    assigned_to = forms.UUIDField(
        label=_('Assigner à'),
        widget=forms.Select()
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.members.models import Member
        staff = Member.objects.filter(
            role__in=['pastor', 'admin'],
            is_active=True
        ).order_by('last_name', 'first_name')
        self.fields['assigned_to'].widget.choices = [
            (str(m.id), m.full_name) for m in staff
        ]


class HelpRequestResolveForm(W3CRMFormMixin, forms.Form):
    resolution_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3}),
        label=_('Notes de résolution')
    )


class HelpRequestCategoryForm(W3CRMFormMixin, forms.ModelForm):
    class Meta:
        model = HelpRequestCategory
        fields = ['name', 'name_fr', 'description', 'icon', 'order', 'is_active']
        labels = {
            'name': _('Nom (anglais)'),
            'name_fr': _('Nom (français)'),
            'description': _('Description'),
            'icon': _('Icône'),
            'order': _("Ordre d'affichage"),
            'is_active': _('Actif'),
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


# ─── Pastoral Care Forms ─────────────────────────────────────────────────────


class PastoralCareForm(W3CRMFormMixin, forms.ModelForm):
    class Meta:
        model = PastoralCare
        fields = ['care_type', 'member', 'assigned_to', 'date', 'notes', 'follow_up_date', 'status']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 4}),
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'follow_up_date': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'care_type': _('Type de soin'),
            'member': _('Membre'),
            'assigned_to': _('Assigné à'),
            'date': _('Date'),
            'notes': _('Notes'),
            'follow_up_date': _('Date de suivi'),
            'status': _('Statut'),
        }


class PastoralCareUpdateForm(W3CRMFormMixin, forms.ModelForm):
    """Form for updating notes and follow-up on an existing care visit."""
    class Meta:
        model = PastoralCare
        fields = ['notes', 'follow_up_date', 'status']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 4}),
            'follow_up_date': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'notes': _('Notes'),
            'follow_up_date': _('Date de suivi'),
            'status': _('Statut'),
        }


# ─── Prayer Request Forms ────────────────────────────────────────────────────


class PrayerRequestForm(W3CRMFormMixin, forms.ModelForm):
    """Form for logged-in members to submit prayer requests."""
    class Meta:
        model = PrayerRequest
        fields = ['title', 'description', 'is_anonymous', 'is_public']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }
        labels = {
            'title': _('Titre'),
            'description': _('Description de la demande de prière'),
            'is_anonymous': _('Soumettre anonymement'),
            'is_public': _('Afficher sur le mur de prière'),
        }


class AnonymousPrayerRequestForm(W3CRMFormMixin, forms.ModelForm):
    """Public-facing form for anonymous prayer requests (no login required)."""
    class Meta:
        model = PrayerRequest
        fields = ['title', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }
        labels = {
            'title': _('Titre de la demande'),
            'description': _('Votre demande de prière'),
        }


class PrayerRequestTestimonyForm(W3CRMFormMixin, forms.Form):
    """Form for marking a prayer as answered with testimony."""
    testimony = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 4}),
        label=_('Témoignage (optionnel)'),
    )


# ─── Care Team Forms ─────────────────────────────────────────────────────────


class CareTeamForm(W3CRMFormMixin, forms.ModelForm):
    class Meta:
        model = CareTeam
        fields = ['name', 'description', 'leader']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'name': _('Nom de l\'équipe'),
            'description': _('Description'),
            'leader': _('Leader'),
        }


class CareTeamMemberForm(W3CRMFormMixin, forms.ModelForm):
    class Meta:
        model = CareTeamMember
        fields = ['team', 'member']
        labels = {
            'team': _('Équipe'),
            'member': _('Membre'),
        }


# ─── Benevolence Forms ───────────────────────────────────────────────────────


class BenevolenceRequestForm(W3CRMFormMixin, forms.ModelForm):
    class Meta:
        model = BenevolenceRequest
        fields = ['fund', 'amount_requested', 'reason']
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'fund': _('Fonds'),
            'amount_requested': _('Montant demandé ($)'),
            'reason': _('Raison de la demande'),
        }


class BenevolenceApprovalForm(W3CRMFormMixin, forms.Form):
    """Form for approving/denying a benevolence request."""
    action = forms.ChoiceField(
        choices=[
            ('approve', _('Approuver')),
            ('deny', _('Refuser')),
        ],
        label=_('Action'),
    )
    amount_granted = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        label=_('Montant accordé ($)'),
    )


class BenevolenceFundForm(W3CRMFormMixin, forms.ModelForm):
    class Meta:
        model = BenevolenceFund
        fields = ['name', 'total_balance', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'name': _('Nom du fonds'),
            'total_balance': _('Solde ($)'),
            'description': _('Description'),
        }


# ─── Meal Train Forms ────────────────────────────────────────────────────────


class MealTrainForm(W3CRMFormMixin, forms.ModelForm):
    class Meta:
        model = MealTrain
        fields = ['recipient', 'reason', 'start_date', 'end_date', 'dietary_restrictions']
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 3}),
            'dietary_restrictions': forms.Textarea(attrs={'rows': 2}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'recipient': _('Bénéficiaire'),
            'reason': _('Raison'),
            'start_date': _('Date de début'),
            'end_date': _('Date de fin'),
            'dietary_restrictions': _('Restrictions alimentaires'),
        }


class MealSignupForm(W3CRMFormMixin, forms.ModelForm):
    class Meta:
        model = MealSignup
        fields = ['date', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }
        labels = {
            'date': _('Date de livraison'),
            'notes': _('Notes (ex: menu prévu)'),
        }


# ─── Crisis Response Forms ───────────────────────────────────────────────────


class CrisisProtocolForm(W3CRMFormMixin, forms.ModelForm):
    class Meta:
        model = CrisisProtocol
        fields = ['title', 'protocol_type', 'steps_json', 'is_active']
        widgets = {
            'steps_json': forms.Textarea(attrs={'rows': 6}),
        }
        labels = {
            'title': _('Titre'),
            'protocol_type': _('Type de protocole'),
            'steps_json': _('Étapes (JSON)'),
            'is_active': _('Actif'),
        }


class CrisisResourceForm(W3CRMFormMixin, forms.ModelForm):
    class Meta:
        model = CrisisResource
        fields = ['title', 'description', 'contact_info', 'url', 'category']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'contact_info': forms.Textarea(attrs={'rows': 2}),
        }
        labels = {
            'title': _('Titre'),
            'description': _('Description'),
            'contact_info': _('Coordonnées'),
            'url': _('Lien web'),
            'category': _('Catégorie'),
        }
