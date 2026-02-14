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
    # Positions
    path('positions/', views_frontend.position_list, name='position_list'),
    path('positions/create/', views_frontend.position_create, name='position_create'),
    path('positions/<uuid:pk>/', views_frontend.position_detail, name='position_detail'),
    path('positions/<uuid:pk>/edit/', views_frontend.position_update, name='position_update'),
    path('positions/<uuid:pk>/delete/', views_frontend.position_delete, name='position_delete'),
    path('positions/<uuid:position_pk>/checklist/', views_frontend.checklist_manage, name='checklist_manage'),

    # Schedules
    path('schedule/', views_frontend.schedule_list, name='schedule_list'),
    path('schedule/create/', views_frontend.schedule_create, name='schedule_create'),
    path('schedule/<uuid:pk>/edit/', views_frontend.schedule_update, name='schedule_update'),
    path('schedule/<uuid:pk>/delete/', views_frontend.schedule_delete, name='schedule_delete'),
    path('schedule/bulk-action/', views_frontend.schedule_bulk_action, name='schedule_bulk_action'),
    path('my-schedule/', views_frontend.my_schedule, name='my_schedule'),
    path('mobile-schedule/', views_frontend.mobile_schedule, name='mobile_schedule'),

    # Availability
    path('availability/', views_frontend.availability_update, name='availability_update'),
    path('availability-slots/', views_frontend.availability_slots, name='availability_slots'),
    path('availability-heatmap/', views_frontend.availability_heatmap, name='availability_heatmap'),
    path('availability-calendar/', views_frontend.availability_calendar, name='availability_calendar'),

    # Planned absences
    path('planned-absences/', views_frontend.planned_absence_list, name='planned_absence_list'),
    path('planned-absences/create/', views_frontend.planned_absence_create, name='planned_absence_create'),
    path('planned-absences/<uuid:pk>/edit/', views_frontend.planned_absence_edit, name='planned_absence_edit'),
    path('planned-absences/<uuid:pk>/delete/', views_frontend.planned_absence_delete, name='planned_absence_delete'),

    # Swap requests
    path('swap-requests/', views_frontend.swap_request_list, name='swap_request_list'),
    path('swap-requests/create/', views_frontend.swap_request_create, name='swap_request_create'),
    path('swap-requests/<uuid:pk>/', views_frontend.swap_request_detail, name='swap_request_detail'),

    # Volunteer hours
    path('hours/log/', views_frontend.hours_log, name='hours_log'),
    path('hours/my-summary/', views_frontend.hours_my_summary, name='hours_my_summary'),
    path('hours/report/', views_frontend.hours_admin_report, name='hours_admin_report'),

    # Background checks
    path('background-checks/', views_frontend.background_check_list, name='background_check_list'),
    path('background-checks/create/', views_frontend.background_check_create, name='background_check_create'),
    path('background-checks/<uuid:pk>/edit/', views_frontend.background_check_update, name='background_check_update'),

    # Team announcements
    path('announcements/', views_frontend.announcement_list, name='announcement_list'),
    path('announcements/create/', views_frontend.announcement_create, name='announcement_create'),

    # Onboarding checklist
    path('onboarding/<uuid:position_pk>/', views_frontend.onboarding_checklist, name='onboarding_checklist'),

    # Skills
    path('skills/', views_frontend.skills_list, name='skills_list'),
    path('skills/profile/', views_frontend.skills_profile, name='skills_profile'),

    # Recognition / Milestones
    path('milestones/', views_frontend.milestones_page, name='milestones_page'),
    path('volunteer-of-month/', views_frontend.volunteer_of_month, name='volunteer_of_month'),

    # Cross-training
    path('cross-training/', views_frontend.cross_training_list, name='cross_training_list'),
    path('cross-training/create/', views_frontend.cross_training_create, name='cross_training_create'),
    path('cross-training/suggestions/', views_frontend.cross_training_suggestions, name='cross_training_suggestions'),
]

app_name = 'volunteers'
urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
    path('', include((frontend_urlpatterns, 'frontend'))),
]
