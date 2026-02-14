"""Attendance URLs."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_frontend, views_api

api_router = DefaultRouter()
api_router.register(r'qr', views_api.MemberQRCodeViewSet, basename='qr')
api_router.register(r'sessions', views_api.AttendanceSessionViewSet, basename='session')
api_router.register(r'checkin', views_api.CheckInViewSet, basename='checkin')
api_router.register(r'alerts', views_api.AbsenceAlertViewSet, basename='alert')
api_router.register(r'children', views_api.ChildCheckInViewSet, basename='child-checkin')
api_router.register(r'nfc', views_api.NFCTagViewSet, basename='nfc')
api_router.register(r'geofences', views_api.GeoFenceViewSet, basename='geofence')
api_router.register(r'visitors', views_api.VisitorInfoViewSet, basename='visitor')
api_router.register(r'checkout', views_api.CheckOutViewSet, basename='checkout')
api_router.register(r'family-checkin', views_api.FamilyCheckInViewSet, basename='family-checkin')
api_router.register(r'analytics', views_api.AttendanceAnalyticsViewSet, basename='analytics')

api_urlpatterns = [path('', include(api_router.urls))]

frontend_urlpatterns = [
    # Original views
    path('my-qr/', views_frontend.my_qr, name='my_qr'),
    path('scanner/', views_frontend.scanner, name='scanner'),
    path('scanner/checkin/', views_frontend.process_checkin, name='process_checkin'),
    path('scanner/checkin-ajax/', views_frontend.process_checkin_ajax, name='process_checkin_ajax'),
    path('sessions/', views_frontend.session_list, name='session_list'),
    path('sessions/create/', views_frontend.create_session, name='create_session'),
    path('sessions/<uuid:pk>/edit/', views_frontend.edit_session, name='edit_session'),
    path('sessions/<uuid:pk>/toggle/', views_frontend.toggle_session, name='toggle_session'),
    path('sessions/<uuid:pk>/delete/', views_frontend.delete_session, name='delete_session'),
    path('sessions/<uuid:pk>/add-record/', views_frontend.add_manual_record, name='add_manual_record'),
    path('records/<uuid:pk>/delete/', views_frontend.delete_record, name='delete_record'),
    path('sessions/<uuid:pk>/', views_frontend.session_detail, name='session_detail'),
    path('my-history/', views_frontend.my_history, name='my_history'),

    # P1: Child Check-In/Check-Out
    path('child/checkin/', views_frontend.child_checkin, name='child_checkin'),
    path('child/receipt/<uuid:pk>/', views_frontend.child_checkin_receipt, name='child_checkin_receipt'),
    path('child/checkout/', views_frontend.child_checkout, name='child_checkout'),
    path('child/history/', views_frontend.child_checkin_history, name='child_checkin_history'),

    # P1: Kiosk
    path('kiosk/<uuid:kiosk_id>/', views_frontend.kiosk_home, name='kiosk_home'),
    path('kiosk/<uuid:kiosk_id>/search/', views_frontend.kiosk_search, name='kiosk_search'),
    path('kiosk/<uuid:kiosk_id>/checkin/', views_frontend.kiosk_checkin, name='kiosk_checkin'),
    path('kiosk/<uuid:kiosk_id>/family-checkin/', views_frontend.kiosk_family_checkin, name='kiosk_family_checkin'),
    path('kiosk/<uuid:kiosk_id>/family-search/', views_frontend.kiosk_family_search, name='kiosk_family_search'),
    path('kiosk/<uuid:kiosk_id>/admin/', views_frontend.kiosk_admin, name='kiosk_admin'),

    # P1: Analytics
    path('analytics/', views_frontend.analytics_dashboard, name='analytics_dashboard'),
    path('analytics/trends/', views_frontend.analytics_trends_api, name='analytics_trends_api'),
    path('analytics/member/<uuid:member_id>/rate/', views_frontend.member_attendance_rate_api, name='member_rate_api'),

    # P1: Frontend refinements
    path('api/member-search/', views_frontend.member_search_api, name='member_search_api'),

    # P2: Family Check-In
    path('family/checkin/', views_frontend.family_checkin, name='family_checkin'),
    path('family/<uuid:family_id>/summary/', views_frontend.family_attendance_summary, name='family_summary'),

    # P2: NFC
    path('nfc/register/', views_frontend.nfc_register, name='nfc_register'),
    path('nfc/reader/', views_frontend.nfc_reader_config, name='nfc_reader_config'),

    # P2: Check-Out
    path('records/<uuid:pk>/checkout/', views_frontend.checkout_member, name='checkout_member'),

    # P3: Geo Check-In
    path('geo/checkin/', views_frontend.geo_checkin, name='geo_checkin'),

    # P3: Predictions
    path('predictions/', views_frontend.prediction_dashboard, name='prediction_dashboard'),

    # P3: Visitors
    path('visitors/', views_frontend.visitor_list, name='visitor_list'),
    path('visitors/create/', views_frontend.visitor_create, name='visitor_create'),
    path('visitors/<uuid:pk>/followup/', views_frontend.visitor_followup, name='visitor_followup'),

    # P3: Alerts
    path('alerts/', views_frontend.absence_alert_list, name='absence_alert_list'),
    path('alerts/<uuid:pk>/acknowledge/', views_frontend.acknowledge_alert, name='acknowledge_alert'),
]

app_name = 'attendance'
