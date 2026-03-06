"""Member merge and duplicate detection service."""
from django.db.models import Q
from django.utils.translation import gettext_lazy as _


class MemberMergeService:
    """Detects duplicate members and merges records."""

    @classmethod
    def find_duplicates(cls, threshold=0.7):
        """
        Find potential duplicate members using fuzzy matching on name, email, phone.

        Returns:
            list of tuples: [(member_a, member_b, score, reason)]
        """
        from .models import Member

        members = list(Member.objects.filter(is_active=True).order_by('last_name', 'first_name'))
        duplicates = []

        for i, a in enumerate(members):
            for b in members[i + 1:]:
                score, reasons = cls._compute_similarity(a, b)
                if score >= threshold:
                    duplicates.append((a, b, score, reasons))

        # Sort by score descending
        duplicates.sort(key=lambda x: x[2], reverse=True)
        return duplicates

    @classmethod
    def _compute_similarity(cls, a, b):
        """
        Compute similarity score between two members.

        Returns:
            tuple: (score: float 0-1, reasons: list[str])
        """
        score = 0.0
        reasons = []

        # Exact name match (high confidence)
        if a.first_name.lower() == b.first_name.lower() and a.last_name.lower() == b.last_name.lower():
            score += 0.7
            reasons.append(_('Même nom complet'))
        else:
            # Partial name match
            name_sim = cls._name_similarity(a, b)
            if name_sim > 0.6:
                score += name_sim * 0.3
                reasons.append(_('Noms similaires'))

        # Email match
        if a.email and b.email and a.email.lower() == b.email.lower():
            score += 0.7
            reasons.append(_('Même courriel'))

        # Phone match
        phone_a = cls._normalize_phone(a.phone)
        phone_b = cls._normalize_phone(b.phone)
        if phone_a and phone_b and phone_a == phone_b:
            score += 0.2
            reasons.append(_('Même téléphone'))

        return min(score, 1.0), reasons

    @classmethod
    def _name_similarity(cls, a, b):
        """Simple name similarity using character overlap."""
        name_a = f'{a.first_name} {a.last_name}'.lower()
        name_b = f'{b.first_name} {b.last_name}'.lower()

        if not name_a or not name_b:
            return 0.0

        # Jaccard similarity on character trigrams
        trigrams_a = set(name_a[i:i+3] for i in range(len(name_a) - 2))
        trigrams_b = set(name_b[i:i+3] for i in range(len(name_b) - 2))

        if not trigrams_a or not trigrams_b:
            return 0.0

        intersection = trigrams_a & trigrams_b
        union = trigrams_a | trigrams_b
        return len(intersection) / len(union)

    @classmethod
    def _normalize_phone(cls, phone):
        """Strip non-digit characters from phone number."""
        if not phone:
            return ''
        return ''.join(c for c in phone if c.isdigit())

    @classmethod
    def merge_members(cls, primary, secondary, merged_by=None):
        """
        Merge secondary member into primary member.
        Transfers all relationships and creates audit log.

        Args:
            primary: Member to keep
            secondary: Member to be merged (will be deactivated)
            merged_by: Member performing the merge

        Returns:
            MemberMergeLog instance
        """
        from .models import (
            MemberMergeLog, GroupMembership, DepartmentMembership,
            DisciplinaryAction, PastoralCare, BackgroundCheck,
            CustomFieldValue, ProfileModificationRequest,
        )

        # Snapshot secondary member data before merge
        snapshot = {
            'id': str(secondary.id),
            'member_number': secondary.member_number,
            'first_name': secondary.first_name,
            'last_name': secondary.last_name,
            'email': secondary.email,
            'phone': secondary.phone,
            'address': secondary.address,
            'city': secondary.city,
            'role': secondary.role,
        }

        # Fill blank fields on primary from secondary
        for field in ['email', 'phone', 'phone_secondary', 'address', 'city',
                      'postal_code', 'birth_date', 'joined_date', 'baptism_date']:
            primary_val = getattr(primary, field)
            secondary_val = getattr(secondary, field)
            if not primary_val and secondary_val:
                setattr(primary, field, secondary_val)

        primary.save()

        # Transfer group memberships
        for gm in GroupMembership.objects.filter(member=secondary):
            if not GroupMembership.objects.filter(member=primary, group=gm.group).exists():
                gm.member = primary
                gm.save()
            else:
                gm.delete()

        # Transfer department memberships
        for dm in DepartmentMembership.objects.filter(member=secondary):
            if not DepartmentMembership.objects.filter(member=primary, department=dm.department).exists():
                dm.member = primary
                dm.save()
            else:
                dm.delete()

        # Transfer disciplinary actions
        DisciplinaryAction.objects.filter(member=secondary).update(member=primary)

        # Transfer pastoral care records
        PastoralCare.objects.filter(member=secondary).update(member=primary)

        # Transfer background checks
        BackgroundCheck.objects.filter(member=secondary).update(member=primary)

        # Transfer custom field values
        for cfv in CustomFieldValue.objects.filter(member=secondary):
            if not CustomFieldValue.objects.filter(member=primary, custom_field=cfv.custom_field).exists():
                cfv.member = primary
                cfv.save()
            else:
                cfv.delete()

        # Transfer modification requests
        ProfileModificationRequest.objects.filter(target_member=secondary).update(target_member=primary)

        # Transfer donations if they exist
        try:
            from apps.donations.models import Donation
            Donation.objects.filter(member=secondary).update(member=primary)
        except (ImportError, Exception):
            pass

        # Transfer volunteer records if they exist
        try:
            from apps.volunteers.models import Volunteer
            Volunteer.objects.filter(member=secondary).update(member=primary)
        except (ImportError, Exception):
            pass

        # Deactivate secondary
        secondary.is_active = False
        secondary.notes = (secondary.notes or '') + f'\n[Fusionné avec {primary.member_number}]'
        secondary.save()

        # Create audit log
        log = MemberMergeLog.objects.create(
            primary_member=primary,
            merged_member_data=snapshot,
            merged_by=merged_by,
        )

        return log
