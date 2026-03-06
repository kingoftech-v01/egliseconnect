"""Donation import service for CSV/OFX files."""
import csv
import io
import json
import logging
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from apps.core.constants import DonationType, PaymentMethod

logger = logging.getLogger(__name__)


class DonationImportService:
    """Parse, validate, preview, and import donation files."""

    REQUIRED_CSV_COLUMNS = ['member_number', 'amount', 'date']
    OPTIONAL_CSV_COLUMNS = ['donation_type', 'payment_method', 'notes', 'campaign', 'check_number']

    @classmethod
    def parse_file(cls, donation_import):
        """
        Parse the uploaded file and create import rows.

        Returns (row_count, errors).
        """
        from .models import DonationImportRow

        filename = donation_import.file.name.lower()
        try:
            if filename.endswith('.csv'):
                rows, errors = cls._parse_csv(donation_import)
            elif filename.endswith('.ofx'):
                rows, errors = cls._parse_ofx(donation_import)
            else:
                return 0, ['Format de fichier non supporté.']
        except Exception as e:
            logger.error(f'Error parsing import file: {e}')
            return 0, [f'Erreur de lecture du fichier: {str(e)}']

        # Create import rows
        for i, row_data in enumerate(rows, start=1):
            DonationImportRow.objects.create(
                donation_import=donation_import,
                row_number=i,
                data_json=row_data,
                status='pending',
            )

        donation_import.total_rows = len(rows)
        donation_import.save(update_fields=['total_rows', 'updated_at'])

        return len(rows), errors

    @classmethod
    def validate_rows(cls, donation_import):
        """Validate all pending rows and mark them valid/invalid."""
        from .models import DonationImportRow
        from apps.members.models import Member

        rows = donation_import.rows.filter(status='pending')
        valid_count = 0
        invalid_count = 0

        for row in rows:
            errors = []
            data = row.data_json

            # Validate member
            member_number = data.get('member_number', '').strip()
            if not member_number:
                errors.append('Numero de membre manquant.')
            else:
                if not Member.objects.filter(member_number=member_number, is_active=True).exists():
                    errors.append(f'Membre {member_number} introuvable.')

            # Validate amount
            try:
                amount = Decimal(str(data.get('amount', '0')))
                if amount <= 0:
                    errors.append('Le montant doit etre positif.')
            except (InvalidOperation, ValueError):
                errors.append('Montant invalide.')

            # Validate date
            date_str = data.get('date', '')
            if not date_str:
                errors.append('Date manquante.')
            else:
                try:
                    cls._parse_date(date_str)
                except ValueError:
                    errors.append('Format de date invalide.')

            # Check for duplicates
            if not errors:
                duplicate = cls._check_duplicate(data)
                if duplicate:
                    row.status = 'duplicate'
                    row.error_message = 'Doublon detecte.'
                    row.save(update_fields=['status', 'error_message', 'updated_at'])
                    invalid_count += 1
                    continue

            if errors:
                row.status = 'invalid'
                row.error_message = ' | '.join(errors)
                invalid_count += 1
            else:
                row.status = 'valid'
                valid_count += 1

            row.save(update_fields=['status', 'error_message', 'updated_at'])

        return valid_count, invalid_count

    @classmethod
    def import_rows(cls, donation_import):
        """Import all valid rows, creating Donation objects."""
        from .models import Donation, DonationImportRow, DonationCampaign
        from apps.members.models import Member

        rows = donation_import.rows.filter(status='valid')
        imported = 0
        skipped = 0

        for row in rows:
            data = row.data_json

            try:
                member = Member.objects.get(
                    member_number=data['member_number'].strip(),
                    is_active=True,
                )
                amount = Decimal(str(data['amount']))
                donation_date = cls._parse_date(data['date'])
                donation_type = data.get('donation_type', DonationType.OFFERING)
                payment_method = data.get('payment_method', PaymentMethod.OTHER)

                # Validate donation_type and payment_method
                valid_types = [c[0] for c in DonationType.CHOICES]
                if donation_type not in valid_types:
                    donation_type = DonationType.OFFERING

                valid_methods = [c[0] for c in PaymentMethod.CHOICES]
                if payment_method not in valid_methods:
                    payment_method = PaymentMethod.OTHER

                campaign = None
                campaign_name = data.get('campaign', '').strip()
                if campaign_name:
                    campaign = DonationCampaign.objects.filter(
                        name__iexact=campaign_name, is_active=True
                    ).first()

                donation = Donation.objects.create(
                    member=member,
                    amount=amount,
                    date=donation_date,
                    donation_type=donation_type,
                    payment_method=payment_method,
                    campaign=campaign,
                    notes=data.get('notes', ''),
                    check_number=data.get('check_number', ''),
                )

                row.donation = donation
                row.status = 'imported'
                row.save(update_fields=['donation', 'status', 'updated_at'])
                imported += 1

            except Exception as e:
                row.status = 'invalid'
                row.error_message = f'Erreur: {str(e)}'
                row.save(update_fields=['status', 'error_message', 'updated_at'])
                skipped += 1

        donation_import.imported_count = imported
        donation_import.skipped_count = skipped
        donation_import.status = 'completed'
        donation_import.save(update_fields=[
            'imported_count', 'skipped_count', 'status', 'updated_at'
        ])

        return imported, skipped

    @classmethod
    def get_preview(cls, donation_import, limit=20):
        """Return a preview of the import rows."""
        rows = donation_import.rows.all()[:limit]
        return [{
            'row_number': row.row_number,
            'data': row.data_json,
            'status': row.status,
            'error': row.error_message,
        } for row in rows]

    @classmethod
    def _parse_csv(cls, donation_import):
        """Parse a CSV file into row dicts."""
        rows = []
        errors = []

        donation_import.file.seek(0)
        content = donation_import.file.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(content))

        if not reader.fieldnames:
            errors.append('Fichier CSV vide ou mal formate.')
            return rows, errors

        # Check required columns
        field_names_lower = [f.lower().strip() for f in reader.fieldnames]
        for col in cls.REQUIRED_CSV_COLUMNS:
            if col not in field_names_lower:
                errors.append(f'Colonne requise manquante: {col}')

        if errors:
            return rows, errors

        # Normalize field names
        for row in reader:
            normalized = {}
            for key, value in row.items():
                normalized[key.lower().strip()] = (value or '').strip()
            rows.append(normalized)

        return rows, errors

    @classmethod
    def _parse_ofx(cls, donation_import):
        """Parse OFX file into row dicts (basic implementation)."""
        rows = []
        errors = []

        try:
            donation_import.file.seek(0)
            content = donation_import.file.read().decode('utf-8', errors='replace')

            # Basic OFX parsing - look for STMTTRN blocks
            import re
            transactions = re.findall(
                r'<STMTTRN>(.*?)</STMTTRN>',
                content,
                re.DOTALL
            )

            for txn in transactions:
                row = {}

                # Extract fields
                amount_match = re.search(r'<TRNAMT>([-\d.]+)', txn)
                date_match = re.search(r'<DTPOSTED>(\d{8})', txn)
                memo_match = re.search(r'<MEMO>(.+?)(?:<|\n)', txn)
                name_match = re.search(r'<NAME>(.+?)(?:<|\n)', txn)

                if amount_match:
                    amount = float(amount_match.group(1))
                    if amount > 0:  # Only positive amounts (deposits)
                        row['amount'] = str(amount)
                        row['member_number'] = ''  # Must be matched manually
                        row['notes'] = (memo_match.group(1) if memo_match else '') or (
                            name_match.group(1) if name_match else ''
                        )

                        if date_match:
                            d = date_match.group(1)
                            row['date'] = f'{d[:4]}-{d[4:6]}-{d[6:8]}'

                        if row.get('amount') and row.get('date'):
                            rows.append(row)

        except Exception as e:
            errors.append(f'Erreur de lecture OFX: {str(e)}')

        return rows, errors

    @staticmethod
    def _parse_date(date_str):
        """Parse a date string in various formats."""
        formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y%m%d']
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue
        raise ValueError(f'Cannot parse date: {date_str}')

    @classmethod
    def _check_duplicate(cls, data):
        """Check if this import row is a duplicate of an existing donation."""
        from .models import Donation
        from apps.members.models import Member

        try:
            member = Member.objects.get(
                member_number=data.get('member_number', '').strip(),
                is_active=True,
            )
            amount = Decimal(str(data.get('amount', '0')))
            donation_date = cls._parse_date(data.get('date', ''))

            return Donation.objects.filter(
                member=member,
                amount=amount,
                date=donation_date,
            ).exists()
        except Exception:
            return False
