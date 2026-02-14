"""Worship URLs."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_frontend, views_api

api_router = DefaultRouter()
api_router.register(r'services', views_api.WorshipServiceViewSet, basename='service')
api_router.register(r'sections', views_api.ServiceSectionViewSet, basename='section')
api_router.register(r'assignments', views_api.ServiceAssignmentViewSet, basename='assignment')
api_router.register(r'eligible', views_api.EligibleMemberListViewSet, basename='eligible')
api_router.register(r'sermons', views_api.SermonViewSet, basename='sermon')
api_router.register(r'sermon-series', views_api.SermonSeriesViewSet, basename='sermon-series')
api_router.register(r'songs', views_api.SongViewSet, basename='song')
api_router.register(r'setlists', views_api.SetlistViewSet, basename='setlist')
api_router.register(r'setlist-songs', views_api.SetlistSongViewSet, basename='setlist-song')
api_router.register(r'preferences', views_api.VolunteerPreferenceViewSet, basename='preference')
api_router.register(r'livestreams', views_api.LiveStreamViewSet, basename='livestream')
api_router.register(r'rehearsals', views_api.RehearsalViewSet, basename='rehearsal')
api_router.register(r'song-requests', views_api.SongRequestViewSet, basename='song-request')

api_urlpatterns = [path('', include(api_router.urls))]

frontend_urlpatterns = [
    # Service CRUD
    path('services/', views_frontend.service_list, name='service_list'),
    path('services/create/', views_frontend.service_create, name='service_create'),
    path('services/<uuid:pk>/', views_frontend.service_detail, name='service_detail'),
    path('services/<uuid:pk>/edit/', views_frontend.service_edit, name='service_edit'),
    path('services/<uuid:pk>/delete/', views_frontend.service_delete, name='service_delete'),
    path('services/<uuid:pk>/publish/', views_frontend.service_publish, name='service_publish'),
    path('services/<uuid:pk>/print/', views_frontend.service_print, name='service_print'),
    path('services/<uuid:pk>/duplicate/', views_frontend.service_duplicate, name='service_duplicate'),

    # Sections
    path('services/<uuid:pk>/sections/', views_frontend.section_manage, name='section_manage'),
    path('services/<uuid:pk>/sections/reorder/', views_frontend.section_reorder, name='section_reorder'),
    path('sections/<uuid:pk>/edit/', views_frontend.section_edit, name='section_edit'),
    path('sections/<uuid:pk>/delete/', views_frontend.section_delete, name='section_delete'),

    # Assignments
    path('sections/<uuid:section_pk>/assign/', views_frontend.assign_members, name='assign_members'),
    path('assignments/<uuid:pk>/remove/', views_frontend.assignment_remove, name='assignment_remove'),
    path('my-assignments/', views_frontend.my_assignments, name='my_assignments'),
    path('assignments/<uuid:pk>/respond/', views_frontend.assignment_respond, name='assignment_respond'),

    # Eligible Lists
    path('eligible/', views_frontend.eligible_list, name='eligible_list'),
    path('eligible/create/', views_frontend.eligible_list_create, name='eligible_list_create'),
    path('eligible/<uuid:pk>/edit/', views_frontend.eligible_list_edit, name='eligible_list_edit'),
    path('eligible/<uuid:pk>/delete/', views_frontend.eligible_list_delete, name='eligible_list_delete'),

    # Sermons
    path('sermons/', views_frontend.sermon_list, name='sermon_list'),
    path('sermons/create/', views_frontend.sermon_create, name='sermon_create'),
    path('sermons/archive/', views_frontend.sermon_archive, name='sermon_archive'),
    path('sermons/feed/', views_frontend.SermonRssFeed(), name='sermon_feed'),
    path('sermons/<uuid:pk>/', views_frontend.sermon_detail, name='sermon_detail'),
    path('sermons/<uuid:pk>/edit/', views_frontend.sermon_edit, name='sermon_edit'),
    path('sermons/<uuid:pk>/delete/', views_frontend.sermon_delete, name='sermon_delete'),

    # Songs
    path('songs/', views_frontend.song_list, name='song_list'),
    path('songs/create/', views_frontend.song_create, name='song_create'),
    path('songs/most-played/', views_frontend.most_played_songs, name='most_played_songs'),
    path('songs/rotation/', views_frontend.song_rotation, name='song_rotation'),
    path('songs/<uuid:pk>/', views_frontend.song_detail, name='song_detail'),
    path('songs/<uuid:pk>/edit/', views_frontend.song_edit, name='song_edit'),
    path('songs/<uuid:pk>/delete/', views_frontend.song_delete, name='song_delete'),
    path('songs/<uuid:pk>/chord-chart/', views_frontend.chord_chart_view, name='chord_chart_view'),
    path('songs/<uuid:pk>/chord-chart/print/', views_frontend.chord_chart_print, name='chord_chart_print'),

    # Setlists
    path('services/<uuid:service_pk>/setlist/', views_frontend.setlist_builder, name='setlist_builder'),
    path('services/<uuid:service_pk>/setlist/reorder/', views_frontend.setlist_reorder, name='setlist_reorder'),
    path('setlist-songs/<uuid:pk>/remove/', views_frontend.setlist_song_remove, name='setlist_song_remove'),

    # CCLI Report
    path('ccli-report/', views_frontend.ccli_report, name='ccli_report'),

    # Calendar
    path('calendar/', views_frontend.calendar_view, name='calendar_view'),
    path('calendar/data/', views_frontend.calendar_data, name='calendar_data'),
    path('services/<uuid:pk>/timeline/', views_frontend.planning_timeline, name='planning_timeline'),

    # Auto-scheduling
    path('services/<uuid:pk>/auto-schedule/', views_frontend.auto_schedule_preview, name='auto_schedule_preview'),

    # Live Streaming
    path('services/<uuid:service_pk>/livestream/', views_frontend.livestream_manage, name='livestream_manage'),
    path('livestreams/<uuid:pk>/delete/', views_frontend.livestream_delete, name='livestream_delete'),

    # Rehearsals
    path('rehearsals/', views_frontend.rehearsal_list, name='rehearsal_list'),
    path('rehearsals/create/', views_frontend.rehearsal_create, name='rehearsal_create'),
    path('rehearsals/<uuid:pk>/', views_frontend.rehearsal_detail, name='rehearsal_detail'),
    path('rehearsals/<uuid:pk>/edit/', views_frontend.rehearsal_edit, name='rehearsal_edit'),
    path('rehearsals/<uuid:pk>/delete/', views_frontend.rehearsal_delete, name='rehearsal_delete'),
    path('rehearsals/<uuid:pk>/rsvp/', views_frontend.rehearsal_rsvp, name='rehearsal_rsvp'),

    # Song Requests
    path('song-requests/', views_frontend.song_request_list, name='song_request_list'),
    path('song-requests/create/', views_frontend.song_request_create, name='song_request_create'),
    path('song-requests/<uuid:pk>/vote/', views_frontend.song_request_vote, name='song_request_vote'),
    path('song-requests/<uuid:pk>/moderate/', views_frontend.song_request_moderate, name='song_request_moderate'),

    # Exports
    path('services/<uuid:pk>/export/propresenter/', views_frontend.propresenter_export, name='propresenter_export'),
    path('services/<uuid:pk>/export/easyworship/', views_frontend.easyworship_export, name='easyworship_export'),
]

app_name = 'worship'
urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
    path('', include((frontend_urlpatterns, 'frontend'))),
]
