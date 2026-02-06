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

api_urlpatterns = [path('', include(api_router.urls))]

frontend_urlpatterns = [
    path('dashboard/', views_frontend.dashboard, name='dashboard'),
    path('form/', views_frontend.onboarding_form, name='form'),
    path('training/', views_frontend.my_training, name='training'),
    path('interview/', views_frontend.my_interview, name='interview'),
    # Admin
    path('admin/pipeline/', views_frontend.admin_pipeline, name='admin_pipeline'),
    path('admin/review/<uuid:pk>/', views_frontend.admin_review, name='admin_review'),
    path('admin/schedule-interview/<uuid:pk>/', views_frontend.admin_schedule_interview, name='admin_schedule_interview'),
    path('admin/interview-result/<uuid:pk>/', views_frontend.admin_interview_result, name='admin_interview_result'),
    path('admin/schedule-lessons/<uuid:training_pk>/', views_frontend.admin_schedule_lessons, name='admin_schedule_lessons'),
    path('admin/courses/', views_frontend.admin_courses, name='admin_courses'),
    path('admin/courses/create/', views_frontend.admin_course_create, name='admin_course_create'),
    path('admin/courses/<uuid:pk>/', views_frontend.admin_course_detail, name='admin_course_detail'),
]

app_name = 'onboarding'
