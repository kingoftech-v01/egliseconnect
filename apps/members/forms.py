"""Forms for member management."""
from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from apps.core.mixins import W3CRMFormMixin
from .models import (
    Member, Family, Group, GroupMembership, DirectoryPrivacy,
    Department, DepartmentMembership, DepartmentTaskType,
    DisciplinaryAction, ProfileModificationRequest,
    Child, PastoralCare, BackgroundCheck, CustomField, CustomFieldValue,
)

User = get_user_model()


class MemberRegistrationForm(W3CRMFormMixin, forms.ModelForm):
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


class MemberProfileForm(W3CRMFormMixin, forms.ModelForm):
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


class MemberAdminForm(W3CRMFormMixin, forms.ModelForm):
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


class MemberStaffForm(W3CRMFormMixin, forms.ModelForm):
    """Staff form for editing administrative fields only (no personal info)."""

    class Meta:
        model = Member
        fields = [
            'role',
            'family',
            'joined_date',
            'baptism_date',
            'membership_status',
            'notes',
            'is_active',
        ]
        widgets = {
            'joined_date': forms.DateInput(attrs={'type': 'date'}),
            'baptism_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 4}),
        }


class ProfileModificationRequestForm(W3CRMFormMixin, forms.ModelForm):
    """Form for staff to request a member to update their personal information."""

    class Meta:
        model = ProfileModificationRequest
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': _('Ex: Veuillez mettre à jour votre numéro de téléphone...')
            }),
        }


class FamilyForm(W3CRMFormMixin, forms.ModelForm):
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


class GroupForm(W3CRMFormMixin, forms.ModelForm):
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


class GroupMembershipForm(W3CRMFormMixin, forms.ModelForm):
    """Form for adding members to groups."""

    class Meta:
        model = GroupMembership
        fields = ['member', 'group', 'role', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, group=None, **kwargs):
        super().__init__(*args, **kwargs)
        if group:
            # Hide group field when adding via a specific group
            self.fields.pop('group', None)
            # Exclude members already in the group
            existing = group.memberships.values_list('member_id', flat=True)
            self.fields['member'].queryset = Member.objects.filter(
                is_active=True
            ).exclude(pk__in=existing)


class DirectoryPrivacyForm(W3CRMFormMixin, forms.ModelForm):
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


class MemberSearchForm(W3CRMFormMixin, forms.Form):
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


class DepartmentForm(W3CRMFormMixin, forms.ModelForm):
    """Form for creating/editing departments."""

    class Meta:
        model = Department
        fields = ['name', 'description', 'leader', 'parent_department',
                  'meeting_day', 'meeting_time', 'meeting_location']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'meeting_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['leader'].queryset = Member.objects.filter(
            is_active=True,
            role__in=['group_leader', 'deacon', 'pastor', 'admin'],
        )
        self.fields['leader'].required = False
        self.fields['parent_department'].required = False


class DepartmentTaskTypeForm(W3CRMFormMixin, forms.ModelForm):
    """Form for creating/editing task types within a department."""

    class Meta:
        model = DepartmentTaskType
        fields = ['name', 'description', 'max_assignees']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }


class DepartmentMembershipForm(W3CRMFormMixin, forms.ModelForm):
    """Form for adding a member to a department."""

    class Meta:
        model = DepartmentMembership
        fields = ['member', 'role']

    def __init__(self, *args, department=None, **kwargs):
        super().__init__(*args, **kwargs)
        if department:
            existing = department.memberships.values_list('member_id', flat=True)
            self.fields['member'].queryset = Member.objects.filter(
                is_active=True
            ).exclude(pk__in=existing)


class DisciplinaryActionForm(W3CRMFormMixin, forms.ModelForm):
    """Form for creating disciplinary actions."""

    class Meta:
        model = DisciplinaryAction
        fields = ['member', 'action_type', 'reason', 'start_date',
                  'end_date', 'auto_suspend_membership', 'notes']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'reason': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['member'].queryset = Member.objects.filter(is_active=True)
        self.fields['end_date'].required = False


# ═══════════════════════════════════════════════════════════════════════════════
# Child / Dependent Forms
# ═══════════════════════════════════════════════════════════════════════════════


class ChildForm(W3CRMFormMixin, forms.ModelForm):
    """Form for creating/editing child profiles."""

    class Meta:
        model = Child
        fields = [
            'first_name', 'last_name', 'date_of_birth',
            'allergies', 'medical_notes', 'authorized_pickups', 'photo',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'allergies': forms.Textarea(attrs={'rows': 2}),
            'medical_notes': forms.Textarea(attrs={'rows': 2}),
            'authorized_pickups': forms.Textarea(attrs={'rows': 2}),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Pastoral Care Forms
# ═══════════════════════════════════════════════════════════════════════════════


class PastoralCareForm(W3CRMFormMixin, forms.ModelForm):
    """Form for creating/editing pastoral care records."""

    class Meta:
        model = PastoralCare
        fields = [
            'member', 'care_type', 'assigned_to', 'date',
            'notes', 'follow_up_date', 'status',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'follow_up_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['member'].queryset = Member.objects.filter(is_active=True)
        from apps.core.constants import Roles
        self.fields['assigned_to'].queryset = Member.objects.filter(
            role__in=Roles.STAFF_ROLES, is_active=True
        )
        self.fields['assigned_to'].required = False
        self.fields['follow_up_date'].required = False


# ═══════════════════════════════════════════════════════════════════════════════
# Background Check Forms
# ═══════════════════════════════════════════════════════════════════════════════


class BackgroundCheckForm(W3CRMFormMixin, forms.ModelForm):
    """Form for creating/editing background check records."""

    class Meta:
        model = BackgroundCheck
        fields = [
            'member', 'status', 'check_date', 'expiry_date',
            'provider', 'reference_number', 'notes',
        ]
        widgets = {
            'check_date': forms.DateInput(attrs={'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['member'].queryset = Member.objects.filter(is_active=True)
        self.fields['check_date'].required = False
        self.fields['expiry_date'].required = False


# ═══════════════════════════════════════════════════════════════════════════════
# Import Wizard Form
# ═══════════════════════════════════════════════════════════════════════════════


class MemberImportForm(W3CRMFormMixin, forms.Form):
    """Form for uploading CSV/Excel file for member import."""

    file = forms.FileField(
        label=_('Fichier CSV ou Excel'),
        help_text=_('Formats acceptés: .csv, .xlsx')
    )


class MemberImportMappingForm(W3CRMFormMixin, forms.Form):
    """Dynamic form for mapping CSV columns to Member fields."""

    def __init__(self, *args, csv_columns=None, **kwargs):
        super().__init__(*args, **kwargs)
        if csv_columns:
            member_fields = [
                ('', _('-- Ignorer --')),
                ('first_name', _('Prénom')),
                ('last_name', _('Nom')),
                ('email', _('Courriel')),
                ('phone', _('Téléphone')),
                ('birth_date', _('Date de naissance')),
                ('address', _('Adresse')),
                ('city', _('Ville')),
                ('province', _('Province')),
                ('postal_code', _('Code postal')),
                ('role', _('Rôle')),
                ('family_status', _('État civil')),
            ]
            for col in csv_columns:
                self.fields[f'col_{col}'] = forms.ChoiceField(
                    choices=member_fields,
                    required=False,
                    label=col,
                )


# ═══════════════════════════════════════════════════════════════════════════════
# Custom Field Forms
# ═══════════════════════════════════════════════════════════════════════════════


class CustomFieldForm(W3CRMFormMixin, forms.ModelForm):
    """Form for creating/editing custom field definitions."""

    class Meta:
        model = CustomField
        fields = ['name', 'field_type', 'options_json', 'is_required', 'order']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['options_json'].widget = forms.Textarea(attrs={
            'rows': 3,
            'class': 'form-control',
            'placeholder': _('["Option 1", "Option 2", "Option 3"]'),
        })
        self.fields['options_json'].required = False


class CustomFieldValueForm(W3CRMFormMixin, forms.ModelForm):
    """Form for setting a custom field value for a member."""

    class Meta:
        model = CustomFieldValue
        fields = ['value']


# ═══════════════════════════════════════════════════════════════════════════════
# Group Extended Form (with lifecycle_stage)
# ═══════════════════════════════════════════════════════════════════════════════


class GroupExtendedForm(W3CRMFormMixin, forms.ModelForm):
    """Extended group form including lifecycle stage."""

    class Meta:
        model = Group
        fields = [
            'name', 'group_type', 'description', 'leader',
            'meeting_day', 'meeting_time', 'meeting_location',
            'email', 'lifecycle_stage',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'meeting_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.core.constants import Roles
        self.fields['leader'].queryset = Member.objects.filter(
            role__in=[Roles.GROUP_LEADER, Roles.PASTOR, Roles.ADMIN]
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Group Finder Search Form
# ═══════════════════════════════════════════════════════════════════════════════


class GroupFinderForm(W3CRMFormMixin, forms.Form):
    """Search form for the group finder."""

    search = forms.CharField(
        required=False,
        label=_('Recherche'),
        widget=forms.TextInput(attrs={'placeholder': _('Nom du groupe, description...')})
    )

    group_type = forms.ChoiceField(
        required=False,
        label=_('Type'),
        choices=[('', _('Tous les types'))] + list(Group._meta.get_field('group_type').choices)
    )

    meeting_day = forms.CharField(
        required=False,
        label=_('Jour de réunion'),
        widget=forms.TextInput(attrs={'placeholder': _('Ex: Mercredi')})
    )
