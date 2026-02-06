"""Reports frontend views."""
from datetime import date
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
        messages.error(request, "Accès non autorisé au tableau de bord.")
        return redirect('frontend:members:member_detail', pk=member.pk if member else '')

    summary = DashboardService.get_dashboard_summary()

    return render(request, 'reports/dashboard.html', {
        'summary': summary,
    })


@login_required
def member_stats(request):
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in ['pastor', 'admin']:
        messages.error(request, "Accès non autorisé.")
        return redirect('frontend:reports:dashboard')

    stats = DashboardService.get_member_stats()

    return render(request, 'reports/member_stats.html', {
        'stats': stats,
    })


@login_required
def donation_report(request):
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in ['pastor', 'admin', 'treasurer']:
        messages.error(request, "Accès non autorisé.")
        return redirect('frontend:reports:dashboard')

    year = request.GET.get('year', date.today().year)
    try:
        year = int(year)
    except ValueError:
        year = date.today().year

    report = ReportService.get_donation_report(year)
    stats = DashboardService.get_donation_stats(year)

    available_years = range(date.today().year, date.today().year - 5, -1)

    return render(request, 'reports/donation_report.html', {
        'report': report,
        'stats': stats,
        'current_year': year,
        'available_years': available_years,
    })


@login_required
def attendance_report(request):
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in ['pastor', 'admin']:
        messages.error(request, "Accès non autorisé.")
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

    return render(request, 'reports/attendance_report.html', {
        'report': report,
        'event_stats': event_stats,
    })


@login_required
def volunteer_report(request):
    member = getattr(request.user, 'member_profile', None)
    if not member or member.role not in ['pastor', 'admin']:
        messages.error(request, "Accès non autorisé.")
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
