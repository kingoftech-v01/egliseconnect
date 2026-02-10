"""Worship URLs."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_frontend, views_api

api_router = DefaultRouter()
api_router.register(r'services', views_api.WorshipServiceViewSet, basename='service')
api_router.register(r'sections', views_api.ServiceSectionViewSet, basename='section')
api_router.register(r'assignments', views_api.ServiceAssignmentViewSet, basename='assignment')
api_router.register(r'eligible', views_api.EligibleMemberListViewSet, basename='eligible')

api_urlpatterns = [path('', include(api_router.urls))]

frontend_urlpatterns = [
    path('services/', views_frontend.service_list, name='service_list'),
    path('services/create/', views_frontend.service_create, name='service_create'),
    path('services/<uuid:pk>/', views_frontend.service_detail, name='service_detail'),
    path('services/<uuid:pk>/edit/', views_frontend.service_edit, name='service_edit'),
    path('services/<uuid:pk>/delete/', views_frontend.service_delete, name='service_delete'),
    path('services/<uuid:pk>/publish/', views_frontend.service_publish, name='service_publish'),
    path('services/<uuid:pk>/print/', views_frontend.service_print, name='service_print'),
    path('services/<uuid:pk>/duplicate/', views_frontend.service_duplicate, name='service_duplicate'),
    path('services/<uuid:pk>/sections/', views_frontend.section_manage, name='section_manage'),
    path('services/<uuid:pk>/sections/reorder/', views_frontend.section_reorder, name='section_reorder'),
    path('sections/<uuid:pk>/edit/', views_frontend.section_edit, name='section_edit'),
    path('sections/<uuid:pk>/delete/', views_frontend.section_delete, name='section_delete'),
    path('sections/<uuid:section_pk>/assign/', views_frontend.assign_members, name='assign_members'),
    path('assignments/<uuid:pk>/remove/', views_frontend.assignment_remove, name='assignment_remove'),
    path('my-assignments/', views_frontend.my_assignments, name='my_assignments'),
    path('assignments/<uuid:pk>/respond/', views_frontend.assignment_respond, name='assignment_respond'),
    path('eligible/', views_frontend.eligible_list, name='eligible_list'),
    path('eligible/create/', views_frontend.eligible_list_create, name='eligible_list_create'),
    path('eligible/<uuid:pk>/edit/', views_frontend.eligible_list_edit, name='eligible_list_edit'),
    path('eligible/<uuid:pk>/delete/', views_frontend.eligible_list_delete, name='eligible_list_delete'),
]

app_name = 'worship'
urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
    path('', include((frontend_urlpatterns, 'frontend'))),
]
