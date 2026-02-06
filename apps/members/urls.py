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
    path('register/', views_frontend.member_create, name='member_create'),
    path('<uuid:pk>/', views_frontend.member_detail, name='member_detail'),
    path('<uuid:pk>/edit/', views_frontend.member_update, name='member_update'),
    path('birthdays/', views_frontend.birthday_list, name='birthday_list'),
    path('directory/', views_frontend.directory, name='directory'),
    path('privacy-settings/', views_frontend.privacy_settings, name='privacy_settings'),
    path('groups/', views_frontend.group_list, name='group_list'),
    path('groups/<uuid:pk>/', views_frontend.group_detail, name='group_detail'),
    path('families/<uuid:pk>/', views_frontend.family_detail, name='family_detail'),
]

app_name = 'members'
urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
    path('', include((frontend_urlpatterns, 'frontend'))),
]
