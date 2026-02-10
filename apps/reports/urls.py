"""Reports URLs."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_frontend, views_api

api_router = DefaultRouter()
api_router.register(r'dashboard', views_api.DashboardViewSet, basename='dashboard')
api_router.register(r'reports', views_api.ReportViewSet, basename='report')

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
