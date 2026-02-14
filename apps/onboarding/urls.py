"""Onboarding URLs."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_frontend, views_api

api_router = DefaultRouter()
api_router.register(r'courses', views_api.TrainingCourseViewSet, basename='course')
api_router.register(r'lessons', views_api.LessonViewSet, basename='lesson')
api_router.register(r'trainings', views_api.MemberTrainingViewSet, basename='training')
api_router.register(r'interviews', views_api.InterviewViewSet, basename='interview')
api_router.register(r'status', views_api.OnboardingStatusView, basename='status')
api_router.register(r'stats', views_api.OnboardingStatsView, basename='onboarding-stats')
# P1: Mentor assignments
api_router.register(r'mentor-assignments', views_api.MentorAssignmentViewSet, basename='mentor-assignment')
# P1: Custom form fields
api_router.register(r'form-fields', views_api.OnboardingFormFieldViewSet, basename='form-field')
api_router.register(r'form-responses', views_api.OnboardingFormResponseViewSet, basename='form-response')
# P1: Welcome sequences
api_router.register(r'welcome-sequences', views_api.WelcomeSequenceViewSet, basename='welcome-sequence')
api_router.register(r'welcome-progress', views_api.WelcomeProgressViewSet, basename='welcome-progress')
# P2: Documents
api_router.register(r'documents', views_api.OnboardingDocumentViewSet, basename='document')
api_router.register(r'signatures', views_api.DocumentSignatureViewSet, basename='signature')
# P2: Visitor follow-ups
api_router.register(r'visitors', views_api.VisitorFollowUpViewSet, basename='visitor')
# P3: Multi-track
api_router.register(r'tracks', views_api.OnboardingTrackViewSet, basename='track')
# P3: Gamification
api_router.register(r'achievements', views_api.AchievementViewSet, basename='achievement')
api_router.register(r'member-achievements', views_api.MemberAchievementViewSet, basename='member-achievement')
# P3: Quizzes
api_router.register(r'quizzes', views_api.QuizViewSet, basename='quiz')
api_router.register(r'quiz-attempts', views_api.QuizAttemptViewSet, basename='quiz-attempt')

api_urlpatterns = [path('', include(api_router.urls))]

frontend_urlpatterns = [
    # ─── Member-facing views ─────────────────────────────────────────────
    path('dashboard/', views_frontend.dashboard, name='dashboard'),
    path('form/', views_frontend.onboarding_form, name='form'),
    path('training/', views_frontend.my_training, name='training'),
    path('interview/', views_frontend.my_interview, name='interview'),

    # P1: Mentee/Mentor views
    path('mentee/', views_frontend.mentee_view, name='mentee_view'),
    path('mentor/dashboard/', views_frontend.mentor_dashboard, name='mentor_dashboard'),
    path('mentor/checkin/<uuid:pk>/', views_frontend.mentor_checkin, name='mentor_checkin'),

    # P2: Journey map and congratulations
    path('journey/', views_frontend.journey_map, name='journey_map'),
    path('congratulations/', views_frontend.congratulations, name='congratulations'),

    # P2: Document signing
    path('documents/', views_frontend.document_list, name='document_list'),
    path('documents/<uuid:pk>/sign/', views_frontend.sign_document, name='sign_document'),

    # P3: Achievements
    path('achievements/', views_frontend.my_achievements, name='my_achievements'),
    path('leaderboard/', views_frontend.leaderboard, name='leaderboard'),

    # P1: Invitation (member-facing)
    path('invitation/', views_frontend.accept_invitation, name='accept_invitation'),

    # ─── Admin views ─────────────────────────────────────────────────────
    path('admin/pipeline/', views_frontend.admin_pipeline, name='admin_pipeline'),
    path('admin/review/<uuid:pk>/', views_frontend.admin_review, name='admin_review'),
    path('admin/schedule-interview/<uuid:pk>/', views_frontend.admin_schedule_interview, name='admin_schedule_interview'),
    path('admin/interview-result/<uuid:pk>/', views_frontend.admin_interview_result, name='admin_interview_result'),
    path('admin/schedule-lessons/<uuid:training_pk>/', views_frontend.admin_schedule_lessons, name='admin_schedule_lessons'),

    # Training courses
    path('admin/courses/', views_frontend.admin_courses, name='admin_courses'),
    path('admin/courses/create/', views_frontend.admin_course_create, name='admin_course_create'),
    path('admin/courses/<uuid:pk>/', views_frontend.admin_course_detail, name='admin_course_detail'),
    path('admin/courses/<uuid:pk>/edit/', views_frontend.admin_course_edit, name='admin_course_edit'),
    path('admin/courses/<uuid:course_pk>/lessons/<uuid:pk>/edit/', views_frontend.admin_lesson_edit, name='admin_lesson_edit'),
    path('admin/courses/<uuid:course_pk>/lessons/<uuid:pk>/delete/', views_frontend.admin_lesson_delete, name='admin_lesson_delete'),
    # P1: Lesson reordering
    path('admin/courses/<uuid:course_pk>/lessons/reorder/', views_frontend.admin_lesson_reorder, name='admin_lesson_reorder'),

    # Stats
    path('admin/stats/', views_frontend.admin_stats, name='admin_stats'),

    # Invitations
    path('admin/invitations/', views_frontend.admin_invitations, name='admin_invitations'),
    path('admin/invitations/create/', views_frontend.admin_invitation_create, name='admin_invitation_create'),
    path('admin/invitations/<uuid:pk>/edit/', views_frontend.admin_invitation_edit, name='admin_invitation_edit'),
    path('admin/invitations/<uuid:pk>/delete/', views_frontend.admin_invitation_delete, name='admin_invitation_delete'),

    # P1: Mentor admin
    path('admin/mentors/assign/', views_frontend.admin_mentor_assign, name='admin_mentor_assign'),

    # P1: Custom form fields
    path('admin/form-fields/', views_frontend.admin_form_fields, name='admin_form_fields'),
    path('admin/form-fields/create/', views_frontend.admin_form_field_create, name='admin_form_field_create'),
    path('admin/form-fields/<uuid:pk>/edit/', views_frontend.admin_form_field_edit, name='admin_form_field_edit'),
    path('admin/form-fields/<uuid:pk>/delete/', views_frontend.admin_form_field_delete, name='admin_form_field_delete'),
    path('admin/form-fields/export/', views_frontend.admin_form_export_csv, name='admin_form_export_csv'),

    # P1: Welcome sequences
    path('admin/welcome-sequences/', views_frontend.admin_welcome_sequences, name='admin_welcome_sequences'),
    path('admin/welcome-sequences/create/', views_frontend.admin_welcome_sequence_create, name='admin_welcome_sequence_create'),
    path('admin/welcome-sequences/<uuid:pk>/', views_frontend.admin_welcome_sequence_detail, name='admin_welcome_sequence_detail'),

    # P1: Bulk pipeline actions
    path('admin/bulk-action/', views_frontend.admin_bulk_action, name='admin_bulk_action'),

    # P2: Visitor follow-up
    path('admin/visitors/', views_frontend.admin_visitors, name='admin_visitors'),
    path('admin/visitors/create/', views_frontend.admin_visitor_create, name='admin_visitor_create'),

    # P2: Documents admin
    path('admin/documents/', views_frontend.admin_documents, name='admin_documents'),
    path('admin/documents/create/', views_frontend.admin_document_create, name='admin_document_create'),
    path('admin/documents/<uuid:pk>/signatures/', views_frontend.admin_document_signatures, name='admin_document_signatures'),

    # P3: Multi-track
    path('admin/tracks/', views_frontend.admin_tracks, name='admin_tracks'),
    path('admin/tracks/create/', views_frontend.admin_track_create, name='admin_track_create'),
    path('admin/tracks/analytics/', views_frontend.admin_track_analytics, name='admin_track_analytics'),

    # P3: Achievements admin
    path('admin/achievements/', views_frontend.admin_achievements, name='admin_achievements'),
    path('admin/achievements/create/', views_frontend.admin_achievement_create, name='admin_achievement_create'),
]

app_name = 'onboarding'
