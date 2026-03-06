"""Reports URLs."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_frontend, views_api

api_router = DefaultRouter()
api_router.register(r'dashboard', views_api.DashboardViewSet, basename='dashboard')
api_router.register(r'reports', views_api.ReportViewSet, basename='report')
api_router.register(r'schedules', views_api.ReportScheduleViewSet, basename='report-schedule')
api_router.register(r'saved-reports', views_api.SavedReportViewSet, basename='saved-report')

api_urlpatterns = [
    path('', include(api_router.urls)),
    path('treasurer/donations/', views_api.TreasurerDonationReportView.as_view(), name='treasurer-donations'),
    path('treasurer/donations/<int:year>/', views_api.TreasurerDonationReportView.as_view(), name='treasurer-donations-year'),
]

frontend_urlpatterns = [
    path('', views_frontend.dashboard, name='dashboard'),
    path('members/', views_frontend.member_stats, name='member_stats'),
    path('donations/', views_frontend.donation_report, name='donation_report'),
    path('attendance/', views_frontend.attendance_report, name='attendance_report'),
    path('volunteers/', views_frontend.volunteer_report, name='volunteer_report'),
    path('birthdays/', views_frontend.birthday_report, name='birthday_report'),
    # New report views (TODOs 5, 6, 14, 15, 16, 17, 18, 19)
    path('help-requests/', views_frontend.help_request_report, name='help_request_report'),
    path('communication/', views_frontend.communication_report, name='communication_report'),
    path('yoy/', views_frontend.yoy_comparison, name='yoy_comparison'),
    path('giving-trends/', views_frontend.giving_trends, name='giving_trends'),
    path('pipeline/', views_frontend.pipeline_stats, name='pipeline_stats'),
    path('predictive/', views_frontend.predictive_dashboard, name='predictive_dashboard'),
    path('bi-api/', views_frontend.bi_api_endpoint, name='bi_api_endpoint'),
    path('health-scorecard/', views_frontend.church_health_scorecard, name='church_health_scorecard'),
    # Report Schedule CRUD (TODO 9)
    path('schedules/', views_frontend.report_schedule_list, name='report_schedule_list'),
    path('schedules/create/', views_frontend.report_schedule_create, name='report_schedule_create'),
    path('schedules/<uuid:pk>/edit/', views_frontend.report_schedule_edit, name='report_schedule_edit'),
    path('schedules/<uuid:pk>/delete/', views_frontend.report_schedule_delete, name='report_schedule_delete'),
    # Saved Report CRUD (TODO 13, 20, 21)
    path('saved/', views_frontend.saved_report_list, name='saved_report_list'),
    path('saved/create/', views_frontend.saved_report_create, name='saved_report_create'),
    path('saved/<uuid:pk>/edit/', views_frontend.saved_report_edit, name='saved_report_edit'),
    path('saved/<uuid:pk>/delete/', views_frontend.saved_report_delete, name='saved_report_delete'),
    path('saved/<uuid:pk>/preview/', views_frontend.saved_report_preview, name='saved_report_preview'),
    # CSV Export
    path('export/members/', views_frontend.export_members_csv, name='export_members_csv'),
    path('export/donations/', views_frontend.export_donations_csv, name='export_donations_csv'),
    path('export/attendance/', views_frontend.export_attendance_csv, name='export_attendance_csv'),
    path('export/volunteers/', views_frontend.export_volunteers_csv, name='export_volunteers_csv'),
]

app_name = 'reports'
urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
    path('', include((frontend_urlpatterns, 'frontend'))),
]
