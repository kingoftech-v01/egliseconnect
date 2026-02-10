"""Members URLs."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_frontend, views_api

api_router = DefaultRouter()
api_router.register(r'members', views_api.MemberViewSet, basename='member')
api_router.register(r'families', views_api.FamilyViewSet, basename='family')
api_router.register(r'groups', views_api.GroupViewSet, basename='group')
api_router.register(r'privacy', views_api.DirectoryPrivacyViewSet, basename='privacy')

api_urlpatterns = [path('', include(api_router.urls))]

frontend_urlpatterns = [
    path('', views_frontend.member_list, name='member_list'),
    path('my-profile/', views_frontend.my_profile, name='my_profile'),
    path('register/', views_frontend.member_create, name='member_create'),
    path('export/', views_frontend.member_list_export, name='member_list_export'),
    path('modification-requests/', views_frontend.modification_request_list, name='modification_request_list'),
    path('modification-requests/<uuid:pk>/complete/', views_frontend.complete_modification_request, name='complete_modification_request'),
    path('birthdays/', views_frontend.birthday_list, name='birthday_list'),
    path('directory/', views_frontend.directory, name='directory'),
    path('privacy-settings/', views_frontend.privacy_settings, name='privacy_settings'),
    # Groups
    path('groups/', views_frontend.group_list, name='group_list'),
    path('groups/create/', views_frontend.group_create, name='group_create'),
    path('groups/<uuid:pk>/', views_frontend.group_detail, name='group_detail'),
    path('groups/<uuid:pk>/edit/', views_frontend.group_edit, name='group_edit'),
    path('groups/<uuid:pk>/delete/', views_frontend.group_delete, name='group_delete'),
    path('groups/<uuid:pk>/add-member/', views_frontend.group_add_member, name='group_add_member'),
    path('groups/<uuid:pk>/remove-member/<uuid:membership_pk>/', views_frontend.group_remove_member, name='group_remove_member'),
    # Families
    path('families/', views_frontend.family_list, name='family_list'),
    path('families/create/', views_frontend.family_create, name='family_create'),
    path('families/<uuid:pk>/', views_frontend.family_detail, name='family_detail'),
    path('families/<uuid:pk>/edit/', views_frontend.family_edit, name='family_edit'),
    path('families/<uuid:pk>/delete/', views_frontend.family_delete, name='family_delete'),
    # Departments
    path('departments/', views_frontend.department_list, name='department_list'),
    path('departments/create/', views_frontend.department_create, name='department_create'),
    path('departments/<uuid:pk>/', views_frontend.department_detail, name='department_detail'),
    path('departments/<uuid:pk>/edit/', views_frontend.department_edit, name='department_edit'),
    path('departments/<uuid:pk>/delete/', views_frontend.department_delete, name='department_delete'),
    path('departments/<uuid:pk>/add-member/', views_frontend.department_add_member, name='department_add_member'),
    path('departments/<uuid:pk>/remove-member/<uuid:membership_pk>/', views_frontend.department_remove_member, name='department_remove_member'),
    path('departments/<uuid:pk>/task-types/', views_frontend.department_task_types, name='department_task_types'),
    # Disciplinary actions
    path('disciplinary/', views_frontend.disciplinary_list, name='disciplinary_list'),
    path('disciplinary/create/', views_frontend.disciplinary_create, name='disciplinary_create'),
    path('disciplinary/<uuid:pk>/', views_frontend.disciplinary_detail, name='disciplinary_detail'),
    path('disciplinary/<uuid:pk>/approve/', views_frontend.disciplinary_approve, name='disciplinary_approve'),
    # Member detail/edit (catch-all UUID patterns must be last)
    path('<uuid:pk>/', views_frontend.member_detail, name='member_detail'),
    path('<uuid:pk>/edit/', views_frontend.member_update, name='member_update'),
    path('<uuid:pk>/request-modification/', views_frontend.request_modification, name='request_modification'),
]

app_name = 'members'
urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
    path('', include((frontend_urlpatterns, 'frontend'))),
]
