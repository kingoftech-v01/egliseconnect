"""Help Requests forms."""
from django import forms
from .models import HelpRequest, HelpRequestComment


class HelpRequestForm(forms.ModelForm):
    class Meta:
        model = HelpRequest
        fields = ['category', 'title', 'description', 'urgency', 'is_confidential']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }
        labels = {
            'category': 'Catégorie',
            'title': 'Titre',
            'description': 'Description',
            'urgency': 'Urgence',
            'is_confidential': 'Confidentiel (visible uniquement par les pasteurs)',
        }


class HelpRequestCommentForm(forms.ModelForm):
    class Meta:
        model = HelpRequestComment
        fields = ['content', 'is_internal']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'content': 'Commentaire',
            'is_internal': 'Note interne (visible uniquement par le staff)',
        }


class HelpRequestAssignForm(forms.Form):
    assigned_to = forms.UUIDField(
        label='Assigner à',
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


class HelpRequestResolveForm(forms.Form):
    resolution_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3}),
        label='Notes de résolution'
    )
