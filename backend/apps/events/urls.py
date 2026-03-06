"""Events URLs."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_frontend, views_api

api_router = DefaultRouter()
api_router.register(r'events', views_api.EventViewSet, basename='event')
api_router.register(r'rooms', views_api.RoomViewSet, basename='room')
api_router.register(r'room-bookings', views_api.RoomBookingViewSet, basename='room-booking')
api_router.register(r'event-templates', views_api.EventTemplateViewSet, basename='event-template')
api_router.register(r'volunteer-needs', views_api.EventVolunteerNeedViewSet, basename='volunteer-need')
api_router.register(r'event-photos', views_api.EventPhotoViewSet, basename='event-photo')
api_router.register(r'event-surveys', views_api.EventSurveyViewSet, basename='event-survey')

api_urlpatterns = [path('', include(api_router.urls))]

frontend_urlpatterns = [
    # Event CRUD
    path('', views_frontend.event_list, name='event_list'),
    path('calendar/', views_frontend.event_calendar, name='event_calendar'),
    path('create/', views_frontend.event_create, name='event_create'),
    path('<uuid:pk>/', views_frontend.event_detail, name='event_detail'),
    path('<uuid:pk>/edit/', views_frontend.event_update, name='event_update'),
    path('<uuid:pk>/delete/', views_frontend.event_delete, name='event_delete'),
    path('<uuid:pk>/cancel/', views_frontend.event_cancel, name='event_cancel'),
    path('<uuid:pk>/rsvp/', views_frontend.event_rsvp, name='event_rsvp'),

    # Calendar export / .ics
    path('<uuid:pk>/ics/', views_frontend.event_ics_download, name='event_ics_download'),
    path('feed.ics', views_frontend.event_ics_feed, name='event_ics_feed'),

    # Rooms
    path('rooms/', views_frontend.room_list, name='room_list'),
    path('rooms/create/', views_frontend.room_create, name='room_create'),
    path('rooms/<uuid:pk>/edit/', views_frontend.room_update, name='room_update'),
    path('rooms/<uuid:pk>/delete/', views_frontend.room_delete, name='room_delete'),
    path('rooms/<uuid:pk>/calendar/', views_frontend.room_calendar, name='room_calendar'),

    # Bookings
    path('bookings/', views_frontend.booking_list, name='booking_list'),
    path('bookings/create/', views_frontend.booking_create, name='booking_create'),
    path('bookings/<uuid:pk>/<str:action>/', views_frontend.booking_action, name='booking_action'),

    # Kiosk
    path('<uuid:pk>/kiosk/', views_frontend.kiosk_checkin, name='kiosk_checkin'),

    # Templates
    path('templates/', views_frontend.template_list, name='template_list'),
    path('templates/create/', views_frontend.template_create, name='template_create'),
    path('create-from-template/', views_frontend.event_create_from_template, name='event_create_from_template'),

    # Waitlist
    path('<uuid:pk>/waitlist/', views_frontend.waitlist_view, name='waitlist_view'),
    path('<uuid:pk>/waitlist/join/', views_frontend.waitlist_join, name='waitlist_join'),
    path('<uuid:pk>/waitlist/<uuid:entry_pk>/promote/', views_frontend.waitlist_promote, name='waitlist_promote'),

    # Volunteer needs
    path('<uuid:pk>/volunteers/', views_frontend.volunteer_needs_view, name='volunteer_needs_view'),
    path('<uuid:pk>/volunteers/create/', views_frontend.volunteer_need_create, name='volunteer_need_create'),
    path('<uuid:pk>/volunteers/<uuid:need_pk>/signup/', views_frontend.volunteer_signup, name='volunteer_signup'),

    # Photos
    path('<uuid:pk>/photos/', views_frontend.photo_gallery, name='photo_gallery'),
    path('<uuid:pk>/photos/upload/', views_frontend.photo_upload, name='photo_upload'),
    path('<uuid:pk>/photos/<uuid:photo_pk>/approve/', views_frontend.photo_approve, name='photo_approve'),

    # Surveys
    path('<uuid:pk>/survey/', views_frontend.survey_builder, name='survey_builder'),
    path('<uuid:pk>/survey/<uuid:survey_pk>/respond/', views_frontend.survey_respond, name='survey_respond'),
    path('<uuid:pk>/survey/<uuid:survey_pk>/results/', views_frontend.survey_results, name='survey_results'),
]

app_name = 'events'
urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
    path('', include((frontend_urlpatterns, 'frontend'))),
]
