# App: Members (Gestion des membres)

## Description
Application centrale du systeme. Gere les profils membres, groupes, familles, departements, actions disciplinaires, soins pastoraux, verifications antecedents, import/export, champs personnalises et scores d'engagement.

## Modeles (19)

| Modele | Champs cles | Relations |
|--------|------------|-----------|
| `Member` (SoftDelete) | member_number, first/last_name, email, phone, birth_date, role, membership_status, photo, two_factor_enabled | FK: user, family, admin_reviewed_by |
| `Family` | name, address, city, province, postal_code | - |
| `Group` | name, group_type, meeting_day/time/location, lifecycle_stage | FK: leader(Member) |
| `GroupMembership` | role, joined_date | FK: member, group. Unique: [member, group] |
| `DirectoryPrivacy` | visibility (public/group/private), show_email/phone/address/birth_date/photo | OneToOne: Member |
| `MemberRole` | role | FK: member. Unique: [member, role] |
| `Department` | name, description, meeting_day/time/location | FK: leader, parent_department(self) |
| `DepartmentMembership` | role (member/leader/assistant), joined_date | FK: member, department |
| `DepartmentTaskType` | name, description, max_assignees | FK: department |
| `DisciplinaryAction` | action_type, reason, start/end_date, approval_status, auto_suspend | FK: member, created_by, approved_by |
| `ProfileModificationRequest` | message, status | FK: target_member, requested_by |
| `Child` | first/last_name, date_of_birth, allergies, medical_notes, authorized_pickups, photo | FK: family |
| `PastoralCare` | care_type, date, notes, follow_up_date, status | FK: member, assigned_to |
| `BackgroundCheck` | status, check_date, expiry_date, provider, reference_number | FK: member |
| `ImportHistory` | filename, total_rows, success_count, error_count, errors_json | FK: imported_by |
| `MemberMergeLog` | merged_member_data (JSON) | FK: primary_member, merged_by |
| `CustomField` | name, field_type, options_json, is_required, order | - |
| `CustomFieldValue` | value | FK: member, custom_field. Unique: [member, custom_field] |
| `MemberEngagementScore` | attendance/giving/volunteering/group_score, total_score | OneToOne: Member |

## Proprietes importantes de Member
- `full_name` → `f"{first_name} {last_name}"`
- `all_roles` → set de tous les roles (primary + MemberRole)
- `has_full_access` → True si membership_status == ACTIVE
- `is_staff_member` → role in STAFF_ROLES
- `can_manage_finances` → role in FINANCE_ROLES
- `is_2fa_overdue` → deadline passee et 2FA non activee
- `is_in_onboarding` → membership_status in IN_PROCESS
- `age` → calcule depuis birth_date
- `engagement_score.level` → Very Engaged / Engaged / Moderate / Weak / Inactive

## API ViewSets

| ViewSet | Permissions | Filtres | Actions custom |
|---------|------------|---------|---------------|
| `MemberViewSet` | Role-scoped | role, family_status, family | `me`, `birthdays`, `directory` |
| `FamilyViewSet` | Read: IsMember, Write: IsPastorOrAdmin | - | - |
| `GroupViewSet` | IsMember+ | group_type, leader | `members`, `add-member`, `remove-member` |
| `DirectoryPrivacyViewSet` | Own only | - | `me` |

## Frontend Views (60+)

### Membres
member_list, member_detail, member_create, member_update, my_profile, request_modification, modification_request_list, birthday_list, directory, directory_public, directory_export_pdf, privacy_settings, member_list_export

### Groupes
group_list, group_detail, group_create, group_edit, group_delete, group_add_member, group_remove_member, group_finder

### Familles
family_list, family_detail, family_create, family_edit, family_delete, family_dashboard, family_merge, family_sync_address

### Departements
department_list, department_detail, department_create, department_edit, department_delete, department_add_member, department_remove_member, department_task_types

### Import/Merge
import_upload, import_map, import_preview, import_history, merge_find_duplicates, merge_wizard, merge_history

### Autres
disciplinary_list/create/detail/approve, care_list/create/detail/edit/dashboard, background_check_list/create/detail/edit, custom_field_list/create/edit/delete, child_list/create/edit/delete, engagement_dashboard/recalculate

## Forms (17)
MemberRegistrationForm, MemberProfileForm, MemberAdminForm, MemberStaffForm, ProfileModificationRequestForm, FamilyForm, GroupForm, GroupMembershipForm, GroupExtendedForm, GroupFinderForm, DirectoryPrivacyForm, MemberSearchForm, DepartmentForm, DepartmentTaskTypeForm, DepartmentMembershipForm, DisciplinaryActionForm, ChildForm, PastoralCareForm, BackgroundCheckForm, MemberImportForm, MemberImportMappingForm, CustomFieldForm, CustomFieldValueForm

## Services
- `DisciplinaryService`: Enforce hierarchy, create/approve/reject actions, auto-suspend, notifications

## Signals
- `create_member_for_superuser`: Auto-cree un profil Member ADMIN pour les superusers

## Celery Tasks
- `send_care_follow_up_reminders` (daily)
- `check_background_check_expiry` (daily)
- `calculate_all_engagement_scores` (weekly)

## Fichiers cles
- `apps/members/models.py` - 19 modeles, centre du systeme
- `apps/members/views_api.py` - 4 ViewSets API
- `apps/members/views_frontend.py` - 60+ vues template
- `apps/members/forms.py` - 17 formulaires
- `apps/members/services.py` - DisciplinaryService
- `apps/members/signals.py` - Auto-create member profile
- `apps/members/tasks.py` - 3 taches Celery
