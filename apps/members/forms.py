"""Forms for member management."""
from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from .models import Member, Family, Group, GroupMembership, DirectoryPrivacy

User = get_user_model()


class MemberRegistrationForm(forms.ModelForm):
    """Public registration form - collects essential info, more can be added via profile."""

    create_account = forms.BooleanField(
        required=False,
        initial=True,
        label=_('Créer un compte utilisateur'),
        help_text=_('Permet de se connecter pour mettre à jour le profil')
    )

    password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        label=_('Mot de passe'),
        help_text=_('Minimum 8 caractères')
    )

    password_confirm = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        label=_('Confirmer le mot de passe')
    )

    class Meta:
        model = Member
        fields = [
            'first_name',
            'last_name',
            'email',
            'phone',
            'birth_date',
            'address',
            'city',
            'province',
            'postal_code',
            'family_status',
        ]
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 2}),
        }

    def clean_email(self):
        """Validate email is unique if creating account."""
        email = self.cleaned_data.get('email')
        create_account = self.cleaned_data.get('create_account')

        if create_account and email:
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError(
                    _('Un compte avec ce courriel existe déjà.')
                )

        return email

    def clean(self):
        """Validate password fields using Django's password validators."""
        cleaned_data = super().clean()
        create_account = cleaned_data.get('create_account')
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if create_account:
            if not password:
                self.add_error('password', _('Le mot de passe est requis.'))
            elif password != password_confirm:
                self.add_error('password_confirm', _('Les mots de passe ne correspondent pas.'))
            else:
                from django.contrib.auth.password_validation import validate_password
                from django.core.exceptions import ValidationError
                try:
                    validate_password(password)
                except ValidationError as e:
                    self.add_error('password', e.messages)

        return cleaned_data

    def save(self, commit=True):
        """Save member and optionally create user account."""
        member = super().save(commit=False)

        if commit:
            member.save()

            if self.cleaned_data.get('create_account'):
                user = User.objects.create_user(
                    username=self.cleaned_data['email'],
                    email=self.cleaned_data['email'],
                    password=self.cleaned_data['password'],
                    first_name=self.cleaned_data['first_name'],
                    last_name=self.cleaned_data['last_name'],
                )
                member.user = user
                member.save(update_fields=['user'])

            DirectoryPrivacy.objects.create(member=member)

        return member


class MemberProfileForm(forms.ModelForm):
    """Profile update form - excludes role, notes, and other staff-only fields."""

    class Meta:
        model = Member
        fields = [
            'first_name',
            'last_name',
            'email',
            'phone',
            'phone_secondary',
            'birth_date',
            'address',
            'city',
            'province',
            'postal_code',
            'photo',
            'family_status',
        ]
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 2}),
        }


class MemberAdminForm(forms.ModelForm):
    """Full admin form with all fields including role and notes."""

    class Meta:
        model = Member
        fields = [
            'first_name',
            'last_name',
            'email',
            'phone',
            'phone_secondary',
            'birth_date',
            'address',
            'city',
            'province',
            'postal_code',
            'photo',
            'role',
            'family_status',
            'family',
            'joined_date',
            'baptism_date',
            'notes',
            'is_active',
        ]
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'joined_date': forms.DateInput(attrs={'type': 'date'}),
            'baptism_date': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 2}),
            'notes': forms.Textarea(attrs={'rows': 4}),
        }


class FamilyForm(forms.ModelForm):
    """Form for creating and editing families."""

    class Meta:
        model = Family
        fields = [
            'name',
            'address',
            'city',
            'province',
            'postal_code',
            'notes',
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 2}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class GroupForm(forms.ModelForm):
    """Form for creating and editing groups."""

    class Meta:
        model = Group
        fields = [
            'name',
            'group_type',
            'description',
            'leader',
            'meeting_day',
            'meeting_time',
            'meeting_location',
            'email',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'meeting_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only allow group leaders and above to be selected as leader
        from apps.core.constants import Roles
        self.fields['leader'].queryset = Member.objects.filter(
            role__in=[Roles.GROUP_LEADER, Roles.PASTOR, Roles.ADMIN]
        )


class GroupMembershipForm(forms.ModelForm):
    """Form for adding members to groups."""

    class Meta:
        model = GroupMembership
        fields = ['member', 'group', 'role', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
        }


class DirectoryPrivacyForm(forms.ModelForm):
    """Form for members to manage their privacy settings."""

    class Meta:
        model = DirectoryPrivacy
        fields = [
            'visibility',
            'show_email',
            'show_phone',
            'show_address',
            'show_birth_date',
            'show_photo',
        ]


class MemberSearchForm(forms.Form):
    """Search and filter form for member list."""

    search = forms.CharField(
        required=False,
        label=_('Recherche'),
        widget=forms.TextInput(attrs={'placeholder': _('Nom, courriel, numéro...')})
    )

    role = forms.ChoiceField(
        required=False,
        label=_('Rôle'),
        choices=[('', _('Tous les rôles'))] + list(Member._meta.get_field('role').choices)
    )

    family_status = forms.ChoiceField(
        required=False,
        label=_('État civil'),
        choices=[('', _('Tous'))] + list(Member._meta.get_field('family_status').choices)
    )

    group = forms.ModelChoiceField(
        required=False,
        label=_('Groupe'),
        queryset=Group.objects.all(),
        empty_label=_('Tous les groupes')
    )

    birth_month = forms.ChoiceField(
        required=False,
        label=_('Mois de naissance'),
        choices=[('', _('Tous les mois'))] + [
            (str(i), _(month)) for i, month in enumerate([
                'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
            ], 1)
        ]
    )
