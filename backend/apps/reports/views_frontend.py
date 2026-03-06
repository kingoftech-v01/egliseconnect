"""Reports frontend views."""
import csv
import json
from datetime import date, timedelta
from decimal import Decimal

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from apps.core.mixins import PastorRequiredMixin
from .services import DashboardService, ReportService
from .models import ReportSchedule, SavedReport
from .forms import ReportScheduleForm, SavedReportForm


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_date(value):
    """Parse a date string, returning None on failure."""
    if value:
        try:
            return date.fromisoformat(value)
        except (ValueError, TypeError):
            pass
    return None


def _check_role(request, roles):
    """Return (member, error_response) tuple. error_response is None if OK."""
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in roles:
        messages.error(request, "Acces non autorise.")
        if member:
            return member, redirect('frontend:reports:dashboard')
        return member, redirect('frontend:members:member_list')
    return member, None


def _staff_roles():
    return ['pastor', 'admin']


def _finance_roles():
    return ['pastor', 'admin', 'treasurer']


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# TODO 1: Member Statistics with Chart.js + date range + export
# ---------------------------------------------------------------------------

@login_required
def member_stats(request):
    member, error = _check_role(request, _staff_roles())
    if error:
        return error

    stats = DashboardService.get_member_stats()
    growth_data = DashboardService.get_member_growth_trend()

    # Chart.js data for role breakdown bar chart
    role_chart_data = {
        'labels': [item['role'] for item in stats['role_breakdown']],
        'counts': [item['count'] for item in stats['role_breakdown']],
    }

    return render(request, 'reports/member_stats.html', {
        'stats': stats,
        'growth_data_json': json.dumps(growth_data),
        'role_chart_json': json.dumps(role_chart_data),
    })


# ---------------------------------------------------------------------------
# TODO 2: Donation Summary with Chart.js + export
# ---------------------------------------------------------------------------

@login_required
def donation_report(request):
    member, error = _check_role(request, _finance_roles())
    if error:
        return error

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

    # Pie chart data by donation type (TODO 2)
    type_chart_data = {
        'labels': [item['donation_type'] for item in stats['by_type']],
        'values': [float(item['total']) for item in stats['by_type']],
    }

    return render(request, 'reports/donation_report.html', {
        'report': report,
        'stats': stats,
        'current_year': year,
        'available_years': available_years,
        'yoy_comparison': yoy_comparison,
        'monthly_chart_json': json.dumps(monthly_chart_data),
        'type_chart_json': json.dumps(type_chart_data),
    })


# ---------------------------------------------------------------------------
# TODO 3: Event Attendance with Chart.js + date range + export
# ---------------------------------------------------------------------------

@login_required
def attendance_report(request):
    member, error = _check_role(request, _staff_roles())
    if error:
        return error

    start_date = _parse_date(request.GET.get('start_date'))
    end_date = _parse_date(request.GET.get('end_date'))

    report = ReportService.get_attendance_report(start_date, end_date)
    event_stats = DashboardService.get_event_stats()

    # Attendance session integration
    session_stats = ReportService.get_attendance_session_stats(
        start_date or date.today() - timedelta(days=90),
        end_date or date.today()
    )

    # Chart.js attendance trend data (TODO 3)
    attendance_chart_data = {
        'labels': [e['date'] for e in report['events']],
        'confirmed': [e['confirmed'] for e in report['events']],
        'total_rsvps': [e['total_rsvps'] for e in report['events']],
    }

    return render(request, 'reports/attendance_report.html', {
        'report': report,
        'event_stats': event_stats,
        'session_stats': session_stats,
        'start_date': report['start_date'],
        'end_date': report['end_date'],
        'attendance_chart_json': json.dumps(attendance_chart_data),
    })


# ---------------------------------------------------------------------------
# TODO 4: Volunteer Hours with Chart.js (stacked bar by team)
# ---------------------------------------------------------------------------

@login_required
def volunteer_report(request):
    member, error = _check_role(request, _staff_roles())
    if error:
        return error

    start_date = _parse_date(request.GET.get('start_date'))
    end_date = _parse_date(request.GET.get('end_date'))

    report = ReportService.get_volunteer_report(start_date, end_date)
    volunteer_stats = DashboardService.get_volunteer_stats()

    # Stacked bar chart data by position (TODO 4)
    volunteer_chart_data = {
        'labels': [item['position__name'] for item in report['by_position']],
        'completed': [item['completed'] for item in report['by_position']],
        'no_show': [item['no_show'] for item in report['by_position']],
    }

    return render(request, 'reports/volunteer_report.html', {
        'report': report,
        'volunteer_stats': volunteer_stats,
        'start_date': report['start_date'],
        'end_date': report['end_date'],
        'volunteer_chart_json': json.dumps(volunteer_chart_data),
    })


# ---------------------------------------------------------------------------
# TODO 5: Help Request analytics with Chart.js
# ---------------------------------------------------------------------------

@login_required
def help_request_report(request):
    member, error = _check_role(request, _staff_roles())
    if error:
        return error

    stats = DashboardService.get_help_request_stats()

    # Pie chart by status (TODO 5)
    status_chart_data = {
        'labels': ['Ouvertes', 'Resolues ce mois'],
        'values': [stats['open'], stats['resolved_this_month']],
    }

    urgency_chart_data = {
        'labels': [item['urgency'] for item in stats['by_urgency']],
        'values': [item['count'] for item in stats['by_urgency']],
    }

    category_chart_data = {
        'labels': [item.get('category__name', 'N/A') for item in stats['by_category']],
        'values': [item['count'] for item in stats['by_category']],
    }

    return render(request, 'reports/help_request_report.html', {
        'stats': stats,
        'status_chart_json': json.dumps(status_chart_data),
        'urgency_chart_json': json.dumps(urgency_chart_data),
        'category_chart_json': json.dumps(category_chart_data),
    })


# ---------------------------------------------------------------------------
# TODO 6: Communication Analytics with Chart.js
# ---------------------------------------------------------------------------

@login_required
def communication_report(request):
    member, error = _check_role(request, _staff_roles())
    if error:
        return error

    comm_stats = ReportService.get_communication_stats()

    return render(request, 'reports/communication_report.html', {
        'comm_stats': comm_stats,
        'comm_stats_json': json.dumps(comm_stats),
    })


# ---------------------------------------------------------------------------
# Birthday report (existing)
# ---------------------------------------------------------------------------

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
# TODO 9: Report Schedule CRUD
# ---------------------------------------------------------------------------

@login_required
def report_schedule_list(request):
    member, error = _check_role(request, _staff_roles())
    if error:
        return error

    schedules = ReportSchedule.objects.all()
    return render(request, 'reports/report_schedule_list.html', {
        'schedules': schedules,
    })


@login_required
def report_schedule_create(request):
    member, error = _check_role(request, _staff_roles())
    if error:
        return error

    if request.method == 'POST':
        form = ReportScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.created_by = member
            if not schedule.next_run_at:
                schedule.next_run_at = schedule.compute_next_run()
            schedule.save()
            form.save_m2m()
            messages.success(request, "Rapport planifie cree avec succes.")
            return redirect('/reports/schedules/')
    else:
        form = ReportScheduleForm()

    return render(request, 'reports/report_schedule_form.html', {
        'form': form,
        'title': 'Creer un rapport planifie',
    })


@login_required
def report_schedule_edit(request, pk):
    member, error = _check_role(request, _staff_roles())
    if error:
        return error

    schedule = get_object_or_404(ReportSchedule, pk=pk)

    if request.method == 'POST':
        form = ReportScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            messages.success(request, "Rapport planifie mis a jour.")
            return redirect('/reports/schedules/')
    else:
        form = ReportScheduleForm(instance=schedule)

    return render(request, 'reports/report_schedule_form.html', {
        'form': form,
        'title': 'Modifier le rapport planifie',
        'schedule': schedule,
    })


@login_required
def report_schedule_delete(request, pk):
    member, error = _check_role(request, _staff_roles())
    if error:
        return error

    schedule = get_object_or_404(ReportSchedule, pk=pk)
    if request.method == 'POST':
        schedule.delete()
        messages.success(request, "Rapport planifie supprime.")
        return redirect('/reports/schedules/')

    return render(request, 'reports/report_schedule_confirm_delete.html', {
        'schedule': schedule,
    })


# ---------------------------------------------------------------------------
# TODO 13 + 20 + 21: Saved Report CRUD (custom report builder + sharing)
# ---------------------------------------------------------------------------

@login_required
def saved_report_list(request):
    member, error = _check_role(request, _staff_roles())
    if error:
        return error

    # Show own reports + reports shared with me
    from django.db.models import Q
    reports = SavedReport.objects.filter(
        Q(created_by=member) | Q(shared_with=member)
    ).distinct()

    return render(request, 'reports/saved_report_list.html', {
        'saved_reports': reports,
    })


@login_required
def saved_report_create(request):
    member, error = _check_role(request, _staff_roles())
    if error:
        return error

    if request.method == 'POST':
        form = SavedReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.created_by = member
            report.save()
            form.save_m2m()
            messages.success(request, "Rapport sauvegarde cree avec succes.")
            return redirect('/reports/saved/')
    else:
        form = SavedReportForm()

    return render(request, 'reports/saved_report_form.html', {
        'form': form,
        'title': 'Creer un rapport personnalise',
    })


@login_required
def saved_report_edit(request, pk):
    member, error = _check_role(request, _staff_roles())
    if error:
        return error

    report = get_object_or_404(SavedReport, pk=pk)

    if request.method == 'POST':
        form = SavedReportForm(request.POST, instance=report)
        if form.is_valid():
            form.save()
            messages.success(request, "Rapport sauvegarde mis a jour.")
            return redirect('/reports/saved/')
    else:
        form = SavedReportForm(instance=report)

    return render(request, 'reports/saved_report_form.html', {
        'form': form,
        'title': 'Modifier le rapport',
        'report': report,
    })


@login_required
def saved_report_delete(request, pk):
    member, error = _check_role(request, _staff_roles())
    if error:
        return error

    report = get_object_or_404(SavedReport, pk=pk)
    if request.method == 'POST':
        report.delete()
        messages.success(request, "Rapport sauvegarde supprime.")
        return redirect('/reports/saved/')

    return render(request, 'reports/saved_report_confirm_delete.html', {
        'report': report,
    })


@login_required
def saved_report_preview(request, pk):
    """Preview a saved report with its filters applied."""
    member, error = _check_role(request, _staff_roles())
    if error:
        return error

    report = get_object_or_404(SavedReport, pk=pk)
    preview_data = ReportService.generate_saved_report_preview(report)

    return render(request, 'reports/saved_report_preview.html', {
        'report': report,
        'preview_data': preview_data,
        'preview_data_json': json.dumps(preview_data, default=str),
    })


# ---------------------------------------------------------------------------
# TODO 14: Year-over-Year Comparison View
# ---------------------------------------------------------------------------

@login_required
def yoy_comparison(request):
    member, error = _check_role(request, _staff_roles())
    if error:
        return error

    year = request.GET.get('year', date.today().year)
    try:
        year = int(year)
    except ValueError:
        year = date.today().year

    data = ReportService.get_yoy_comparison(year)
    available_years = range(date.today().year, date.today().year - 5, -1)

    return render(request, 'reports/yoy_comparison.html', {
        'data': data,
        'current_year': year,
        'available_years': available_years,
        'data_json': json.dumps(data, default=str),
    })


# ---------------------------------------------------------------------------
# TODO 15: Giving Trend Analysis
# ---------------------------------------------------------------------------

@login_required
def giving_trends(request):
    member, error = _check_role(request, _finance_roles())
    if error:
        return error

    data = ReportService.get_giving_trends()

    return render(request, 'reports/giving_trends.html', {
        'data': data,
        'data_json': json.dumps(data, default=str),
    })


# ---------------------------------------------------------------------------
# TODO 16: Pipeline/Funnel Stats
# ---------------------------------------------------------------------------

@login_required
def pipeline_stats(request):
    member, error = _check_role(request, _staff_roles())
    if error:
        return error

    data = DashboardService.get_onboarding_pipeline_stats()
    total_registered = data.get('registered', 0)
    total_submitted = data.get('form_submitted', 0)
    total_training = data.get('in_training', 0)

    from apps.members.models import Member
    total_active = Member.objects.filter(membership_status='active').count()

    pipeline_data = {
        'stages': ['Inscrits', 'Formulaire soumis', 'En formation', 'Interview planifiee', 'Actifs'],
        'counts': [
            data.get('registered', 0),
            data.get('form_submitted', 0),
            data.get('in_training', 0),
            data.get('interview_scheduled', 0),
            total_active,
        ],
    }

    # Conversion rates
    stages = pipeline_data['counts']
    conversion_rates = []
    for i in range(1, len(stages)):
        if stages[i - 1] > 0:
            rate = round(stages[i] / stages[i - 1] * 100, 1)
        else:
            rate = 0.0
        conversion_rates.append(rate)

    return render(request, 'reports/pipeline_stats.html', {
        'pipeline_data': pipeline_data,
        'conversion_rates': conversion_rates,
        'pipeline_json': json.dumps(pipeline_data),
    })


# ---------------------------------------------------------------------------
# TODO 17: Predictive Analytics Dashboard
# ---------------------------------------------------------------------------

@login_required
def predictive_dashboard(request):
    member, error = _check_role(request, _staff_roles())
    if error:
        return error

    data = ReportService.get_predictive_analytics()

    return render(request, 'reports/predictive_dashboard.html', {
        'data': data,
        'data_json': json.dumps(data, default=str),
    })


# ---------------------------------------------------------------------------
# TODO 18: BI Tool Integration Endpoints (JSON API)
# ---------------------------------------------------------------------------

@login_required
def bi_api_endpoint(request):
    """JSON API endpoint compatible with Metabase/Grafana."""
    member, error = _check_role(request, _staff_roles())
    if error:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    report_type = request.GET.get('type', 'summary')
    data = ReportService.get_bi_data(report_type)

    return JsonResponse(data, safe=False)


# ---------------------------------------------------------------------------
# TODO 19: Church Health Scorecard
# ---------------------------------------------------------------------------

@login_required
def church_health_scorecard(request):
    member, error = _check_role(request, _staff_roles())
    if error:
        return error

    data = ReportService.get_church_health_scorecard()

    return render(request, 'reports/church_health_scorecard.html', {
        'data': data,
        'data_json': json.dumps(data, default=str),
    })


# ---------------------------------------------------------------------------
# CSV/PDF Export views (TODO 10: export buttons on every report page)
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

    start_date = _parse_date(request.GET.get('start_date'))
    end_date = _parse_date(request.GET.get('end_date'))

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

    start_date = _parse_date(request.GET.get('start_date'))
    end_date = _parse_date(request.GET.get('end_date'))

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
