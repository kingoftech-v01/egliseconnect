"""Reports frontend views."""
import csv
import json
from datetime import date, timedelta
from decimal import Decimal

from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from apps.core.mixins import PastorRequiredMixin
from .services import DashboardService, ReportService


@login_required
def dashboard(request):
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in ['pastor', 'admin', 'treasurer']:
        messages.error(request, "Acces non autorise au tableau de bord.")
        return redirect('frontend:members:member_detail', pk=member.pk if member else '')

    summary = DashboardService.get_dashboard_summary()

    # Onboarding pipeline stats widget
    onboarding_pipeline = DashboardService.get_onboarding_pipeline_stats()

    # Financial summary widget (monthly giving trend)
    financial_summary = DashboardService.get_financial_summary()

    # Member growth trend data for Chart.js
    growth_data = DashboardService.get_member_growth_trend()

    return render(request, 'reports/dashboard.html', {
        'summary': summary,
        'onboarding_pipeline': onboarding_pipeline,
        'financial_summary': financial_summary,
        'growth_data_json': json.dumps(growth_data),
    })


@login_required
def member_stats(request):
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in ['pastor', 'admin']:
        messages.error(request, "Acces non autorise.")
        return redirect('frontend:reports:dashboard')

    stats = DashboardService.get_member_stats()

    # Growth trend data for chart
    growth_data = DashboardService.get_member_growth_trend()

    return render(request, 'reports/member_stats.html', {
        'stats': stats,
        'growth_data_json': json.dumps(growth_data),
    })


@login_required
def donation_report(request):
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in ['pastor', 'admin', 'treasurer']:
        messages.error(request, "Acces non autorise.")
        return redirect('frontend:reports:dashboard')

    year = request.GET.get('year', date.today().year)
    try:
        year = int(year)
    except ValueError:
        year = date.today().year

    report = ReportService.get_donation_report(year)
    stats = DashboardService.get_donation_stats(year)

    available_years = range(date.today().year, date.today().year - 5, -1)

    # Year-over-year comparison
    prev_year_stats = DashboardService.get_donation_stats(year - 1)
    yoy_comparison = {
        'current_year': year,
        'prev_year': year - 1,
        'current_total': float(stats['total_amount']),
        'prev_total': float(prev_year_stats['total_amount']),
        'change_amount': float(stats['total_amount'] - prev_year_stats['total_amount']),
    }
    if prev_year_stats['total_amount'] > 0:
        yoy_comparison['change_percent'] = round(
            float((stats['total_amount'] - prev_year_stats['total_amount'])
                  / prev_year_stats['total_amount'] * 100), 1
        )
    else:
        yoy_comparison['change_percent'] = 0

    # Monthly data for chart
    monthly_chart_data = {
        'labels': [],
        'current': [],
        'previous': [],
    }
    prev_report = ReportService.get_donation_report(year - 1)
    month_names = [
        'Jan', 'Fev', 'Mar', 'Avr', 'Mai', 'Jun',
        'Jul', 'Aou', 'Sep', 'Oct', 'Nov', 'Dec'
    ]
    for i, item in enumerate(report['monthly']):
        monthly_chart_data['labels'].append(month_names[i])
        monthly_chart_data['current'].append(float(item['total']))
    for item in prev_report['monthly']:
        monthly_chart_data['previous'].append(float(item['total']))

    return render(request, 'reports/donation_report.html', {
        'report': report,
        'stats': stats,
        'current_year': year,
        'available_years': available_years,
        'yoy_comparison': yoy_comparison,
        'monthly_chart_json': json.dumps(monthly_chart_data),
    })


@login_required
def attendance_report(request):
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in ['pastor', 'admin']:
        messages.error(request, "Acces non autorise.")
        return redirect('frontend:reports:dashboard')

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date:
        try:
            start_date = date.fromisoformat(start_date)
        except ValueError:
            start_date = None
    if end_date:
        try:
            end_date = date.fromisoformat(end_date)
        except ValueError:
            end_date = None

    report = ReportService.get_attendance_report(start_date, end_date)
    event_stats = DashboardService.get_event_stats()

    # Attendance session integration
    session_stats = ReportService.get_attendance_session_stats(
        start_date or date.today() - timedelta(days=90),
        end_date or date.today()
    )

    return render(request, 'reports/attendance_report.html', {
        'report': report,
        'event_stats': event_stats,
        'session_stats': session_stats,
        'start_date': report['start_date'],
        'end_date': report['end_date'],
    })


@login_required
def volunteer_report(request):
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in ['pastor', 'admin']:
        messages.error(request, "Acces non autorise.")
        return redirect('frontend:reports:dashboard')

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date:
        try:
            start_date = date.fromisoformat(start_date)
        except ValueError:
            start_date = None
    if end_date:
        try:
            end_date = date.fromisoformat(end_date)
        except ValueError:
            end_date = None

    report = ReportService.get_volunteer_report(start_date, end_date)
    volunteer_stats = DashboardService.get_volunteer_stats()

    return render(request, 'reports/volunteer_report.html', {
        'report': report,
        'volunteer_stats': volunteer_stats,
        'start_date': report['start_date'],
        'end_date': report['end_date'],
    })


@login_required
def birthday_report(request):
    member = getattr(request.user, 'member_profile', None)
    if not member:
        messages.error(request, "Profil membre requis.")
        return redirect('frontend:members:member_list')

    days = request.GET.get('days', 30)
    try:
        days = int(days)
    except ValueError:
        days = 30

    birthdays = DashboardService.get_upcoming_birthdays(days)

    return render(request, 'reports/birthday_report.html', {
        'birthdays': birthdays,
        'days': days,
    })


# ---------------------------------------------------------------------------
# CSV/PDF Export views
# ---------------------------------------------------------------------------

@login_required
def export_members_csv(request):
    """Export member statistics as CSV."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in ['pastor', 'admin']:
        messages.error(request, "Acces non autorise.")
        return redirect('frontend:reports:dashboard')

    from apps.members.models import Member
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="membres_rapport.csv"'
    response.write('\ufeff')  # BOM for Excel

    writer = csv.writer(response)
    writer.writerow(['Nom', 'Prenom', 'Courriel', 'Role', 'Statut', 'Date inscription'])

    members = Member.objects.filter(is_active=True).order_by('last_name')
    for m in members:
        writer.writerow([
            m.last_name, m.first_name, m.email,
            m.get_role_display(), m.get_membership_status_display(),
            m.registration_date.strftime('%d/%m/%Y') if m.registration_date else '-',
        ])

    return response


@login_required
def export_donations_csv(request):
    """Export donation report as CSV."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in ['pastor', 'admin', 'treasurer']:
        messages.error(request, "Acces non autorise.")
        return redirect('frontend:reports:dashboard')

    year = request.GET.get('year', date.today().year)
    try:
        year = int(year)
    except ValueError:
        year = date.today().year

    from apps.donations.models import Donation
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="dons_rapport_{year}.csv"'
    response.write('\ufeff')

    writer = csv.writer(response)
    writer.writerow(['Date', 'Montant', 'Type', 'Methode paiement'])

    donations = Donation.objects.filter(date__year=year).order_by('date')
    for d in donations:
        writer.writerow([
            d.date.strftime('%d/%m/%Y'),
            str(d.amount),
            d.get_donation_type_display(),
            d.get_payment_method_display(),
        ])

    return response


@login_required
def export_attendance_csv(request):
    """Export attendance report as CSV."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in ['pastor', 'admin']:
        messages.error(request, "Acces non autorise.")
        return redirect('frontend:reports:dashboard')

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        try:
            start_date = date.fromisoformat(start_date)
        except ValueError:
            start_date = None
    if end_date:
        try:
            end_date = date.fromisoformat(end_date)
        except ValueError:
            end_date = None

    report = ReportService.get_attendance_report(start_date, end_date)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="presence_rapport.csv"'
    response.write('\ufeff')

    writer = csv.writer(response)
    writer.writerow(['Evenement', 'Date', 'Type', 'RSVP total', 'Confirmes', 'Refuses', 'Invites'])

    for event in report['events']:
        writer.writerow([
            event['title'], event['date'], event['event_type'],
            event['total_rsvps'], event['confirmed'],
            event['declined'], event['total_guests'],
        ])

    return response


@login_required
def export_volunteers_csv(request):
    """Export volunteer report as CSV."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in ['pastor', 'admin']:
        messages.error(request, "Acces non autorise.")
        return redirect('frontend:reports:dashboard')

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        try:
            start_date = date.fromisoformat(start_date)
        except ValueError:
            start_date = None
    if end_date:
        try:
            end_date = date.fromisoformat(end_date)
        except ValueError:
            end_date = None

    report = ReportService.get_volunteer_report(start_date, end_date)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="volontaires_rapport.csv"'
    response.write('\ufeff')

    writer = csv.writer(response)
    writer.writerow(['Nom', 'Prenom', 'Quarts completes'])

    for vol in report['top_volunteers']:
        writer.writerow([
            vol['member__last_name'], vol['member__first_name'], vol['count'],
        ])

    return response
