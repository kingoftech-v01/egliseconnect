"""Giving statement generation and delivery service."""
import io
import logging
from datetime import date
from decimal import Decimal

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from django.db.models import Sum
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class StatementService:
    """Service for generating, storing, and emailing giving statements."""

    @staticmethod
    def get_period_dates(year, period):
        """Return (start_date, end_date) for a given period."""
        if period == 'mid_year':
            return date(year, 1, 1), date(year, 6, 30)
        else:  # annual
            return date(year, 1, 1), date(year, 12, 31)

    @classmethod
    def generate_statement(cls, member, year, period):
        """
        Generate a giving statement for a member.

        Returns the GivingStatement instance (created or existing).
        """
        from .models import GivingStatement, Donation

        start_date, end_date = cls.get_period_dates(year, period)

        # Check for existing
        existing = GivingStatement.objects.filter(
            member=member, year=year, period=period
        ).first()
        if existing:
            return existing

        # Calculate total
        donations = Donation.objects.filter(
            member=member,
            date__gte=start_date,
            date__lte=end_date,
            is_active=True,
        )
        total = donations.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        # Create statement
        statement = GivingStatement.objects.create(
            member=member,
            year=year,
            period=period,
            start_date=start_date,
            end_date=end_date,
            total_amount=total,
        )

        # Generate PDF
        try:
            pdf_content = cls._generate_pdf(statement, donations)
            if pdf_content:
                filename = f'releve_{member.pk}_{year}_{period}.pdf'
                statement.pdf_file.save(filename, ContentFile(pdf_content), save=True)
        except Exception as e:
            logger.error(f'Failed to generate PDF for statement {statement.pk}: {e}')

        return statement

    @classmethod
    def bulk_generate(cls, year, period):
        """Generate statements for all members with donations in the period."""
        from apps.members.models import Member
        from .models import Donation

        start_date, end_date = cls.get_period_dates(year, period)

        members_with_donations = Member.objects.filter(
            donations__date__gte=start_date,
            donations__date__lte=end_date,
            donations__is_active=True,
        ).distinct()

        generated = []
        for member in members_with_donations:
            statement = cls.generate_statement(member, year, period)
            if statement:
                generated.append(statement)

        return generated

    @classmethod
    def email_statement(cls, statement):
        """Email a giving statement to the member."""
        member = statement.member
        if not member.email:
            logger.warning(f'No email for member {member.pk}, skipping statement email.')
            return False

        church_name = getattr(settings, 'CHURCH_NAME', 'EgliseConnect')

        subject = f'{church_name} - Releve de dons {statement.year}'
        body = render_to_string('donations/email_statement.html', {
            'member': member,
            'statement': statement,
            'church_name': church_name,
        })

        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[member.email],
        )
        email.content_subtype = 'html'

        if statement.pdf_file:
            email.attach_file(statement.pdf_file.path)

        try:
            email.send()
            statement.emailed_at = timezone.now()
            statement.save(update_fields=['emailed_at', 'updated_at'])
            return True
        except Exception as e:
            logger.error(f'Failed to email statement {statement.pk}: {e}')
            return False

    @classmethod
    def bulk_email(cls, statements):
        """Email multiple statements."""
        sent = 0
        for statement in statements:
            if cls.email_statement(statement):
                sent += 1
        return sent

    @classmethod
    def _generate_pdf(cls, statement, donations):
        """Generate PDF content for a giving statement."""
        try:
            from xhtml2pdf import pisa
        except ImportError:
            logger.error('xhtml2pdf not installed, cannot generate statement PDF.')
            return None

        church_name = getattr(settings, 'CHURCH_NAME', 'EgliseConnect')
        church_address = getattr(settings, 'CHURCH_ADDRESS', '')
        church_registration = getattr(settings, 'CHURCH_REGISTRATION', '')

        html_string = render_to_string('donations/statement_pdf.html', {
            'statement': statement,
            'donations': donations,
            'member': statement.member,
            'church_name': church_name,
            'church_address': church_address,
            'church_registration': church_registration,
        })

        output = io.BytesIO()
        pisa_status = pisa.CreatePDF(io.StringIO(html_string), dest=output)

        if pisa_status.err:
            logger.error(f'PDF generation error for statement {statement.pk}')
            return None

        return output.getvalue()
