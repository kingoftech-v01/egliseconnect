"""Volunteers URLs."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_frontend, views_api

api_router = DefaultRouter()
api_router.register(r'positions', views_api.VolunteerPositionViewSet, basename='position')
api_router.register(r'schedules', views_api.VolunteerScheduleViewSet, basename='schedule')
api_router.register(r'availability', views_api.VolunteerAvailabilityViewSet, basename='availability')
api_router.register(r'swap-requests', views_api.SwapRequestViewSet, basename='swap-request')

api_urlpatterns = [path('', include(api_router.urls))]

frontend_urlpatterns = [
    path('positions/', views_frontend.position_list, name='position_list'),
    path('positions/create/', views_frontend.position_create, name='position_create'),
    path('positions/<uuid:pk>/edit/', views_frontend.position_update, name='position_update'),
    path('positions/<uuid:pk>/delete/', views_frontend.position_delete, name='position_delete'),
    path('schedule/', views_frontend.schedule_list, name='schedule_list'),
    path('schedule/create/', views_frontend.schedule_create, name='schedule_create'),
    path('schedule/<uuid:pk>/edit/', views_frontend.schedule_update, name='schedule_update'),
    path('schedule/<uuid:pk>/delete/', views_frontend.schedule_delete, name='schedule_delete'),
    path('my-schedule/', views_frontend.my_schedule, name='my_schedule'),
    path('availability/', views_frontend.availability_update, name='availability_update'),
    path('planned-absences/', views_frontend.planned_absence_list, name='planned_absence_list'),
    path('planned-absences/create/', views_frontend.planned_absence_create, name='planned_absence_create'),
    path('planned-absences/<uuid:pk>/edit/', views_frontend.planned_absence_edit, name='planned_absence_edit'),
    path('planned-absences/<uuid:pk>/delete/', views_frontend.planned_absence_delete, name='planned_absence_delete'),
    path('swap-requests/', views_frontend.swap_request_list, name='swap_request_list'),
    path('swap-requests/create/', views_frontend.swap_request_create, name='swap_request_create'),
]

app_name = 'volunteers'
urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
    path('', include((frontend_urlpatterns, 'frontend'))),
]
