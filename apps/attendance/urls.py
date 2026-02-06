"""Attendance URLs."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_frontend, views_api

api_router = DefaultRouter()
api_router.register(r'qr', views_api.MemberQRCodeViewSet, basename='qr')
api_router.register(r'sessions', views_api.AttendanceSessionViewSet, basename='session')
api_router.register(r'checkin', views_api.CheckInViewSet, basename='checkin')
api_router.register(r'alerts', views_api.AbsenceAlertViewSet, basename='alert')

api_urlpatterns = [path('', include(api_router.urls))]

frontend_urlpatterns = [
    path('my-qr/', views_frontend.my_qr, name='my_qr'),
    path('scanner/', views_frontend.scanner, name='scanner'),
    path('scanner/checkin/', views_frontend.process_checkin, name='process_checkin'),
    path('sessions/', views_frontend.session_list, name='session_list'),
    path('sessions/create/', views_frontend.create_session, name='create_session'),
    path('sessions/<uuid:pk>/', views_frontend.session_detail, name='session_detail'),
    path('my-history/', views_frontend.my_history, name='my_history'),
]

app_name = 'attendance'
