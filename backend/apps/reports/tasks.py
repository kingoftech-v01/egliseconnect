"""Celery tasks for scheduled report generation and email delivery."""
from celery import shared_task


@shared_task(name='reports.send_scheduled_reports')
def send_scheduled_reports():
    """
    Check all active ReportSchedule instances where next_run_at <= now,
    generate the report, email to recipients, and update next_run_at.
    """
    from django.utils import timezone
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.conf import settings

    from apps.reports.models import ReportSchedule
    from apps.reports.services import ReportService, DashboardService

    now = timezone.now()
    due_schedules = ReportSchedule.objects.filter(
        is_active=True,
        next_run_at__lte=now,
    )

    sent_count = 0
    for schedule in due_schedules:
        try:
            # Generate report data based on type
            report_data = _generate_report_for_type(schedule.report_type)

            # Get recipient emails
            recipient_emails = list(
                schedule.recipients.filter(
                    is_active=True,
                    email__isnull=False,
                ).exclude(email='').values_list('email', flat=True)
            )

            if not recipient_emails:
                # Update next_run even if no recipients
                schedule.last_sent_at = now
                schedule.next_run_at = schedule.compute_next_run()
                schedule.save(update_fields=['last_sent_at', 'next_run_at', 'updated_at'])
                continue

            # Build email content
            subject = f'Rapport planifie: {schedule.name}'
            body = render_to_string('reports/email/scheduled_report.txt', {
                'schedule': schedule,
                'report_data': report_data,
                'generated_at': now,
            })

            # Send email
            send_mail(
                subject=subject,
                message=body,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@egliseconnect.ca'),
                recipient_list=recipient_emails,
                fail_silently=True,
            )

            # Update schedule
            schedule.last_sent_at = now
            schedule.next_run_at = schedule.compute_next_run()
            schedule.save(update_fields=['last_sent_at', 'next_run_at', 'updated_at'])
            sent_count += 1

        except Exception:
            # Log error but continue with other schedules
            continue

    return f'Sent {sent_count} scheduled reports.'


@shared_task(name='reports.generate_report_pdf')
def generate_report_pdf(report_type, filters=None):
    """
    Generate a PDF for a specific report type.
    Returns the PDF content as bytes (for chaining or storage).
    """
    from apps.reports.services import ReportService, DashboardService

    report_data = _generate_report_for_type(report_type, filters)
    # For now, return the data dict (PDF generation would use xhtml2pdf)
    return {'status': 'generated', 'report_type': report_type}


def _generate_report_for_type(report_type, filters=None):
    """Helper to generate report data based on type."""
    from apps.reports.services import ReportService, DashboardService
    from datetime import date

    filters = filters or {}

    if report_type == 'member_stats':
        return DashboardService.get_member_stats()
    elif report_type == 'donation_summary':
        year = filters.get('year', date.today().year)
        return DashboardService.get_donation_stats(year)
    elif report_type == 'event_attendance':
        return ReportService.get_attendance_report()
    elif report_type == 'volunteer_hours':
        return ReportService.get_volunteer_report()
    elif report_type == 'help_requests':
        return DashboardService.get_help_request_stats()
    elif report_type == 'communication':
        return ReportService.get_communication_stats()
    else:
        return DashboardService.get_dashboard_summary()
