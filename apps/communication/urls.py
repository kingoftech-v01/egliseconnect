"""Communication URLs."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_frontend, views_api

api_router = DefaultRouter()
api_router.register(r'newsletters', views_api.NewsletterViewSet, basename='newsletter')
api_router.register(r'notifications', views_api.NotificationViewSet, basename='notification')
api_router.register(r'preferences', views_api.NotificationPreferenceViewSet, basename='preference')

api_urlpatterns = [path('', include(api_router.urls))]

frontend_urlpatterns = [
    path('newsletters/', views_frontend.newsletter_list, name='newsletter_list'),
    path('newsletters/create/', views_frontend.newsletter_create, name='newsletter_create'),
    path('newsletters/<uuid:pk>/', views_frontend.newsletter_detail, name='newsletter_detail'),
    path('newsletters/<uuid:pk>/edit/', views_frontend.newsletter_edit, name='newsletter_edit'),
    path('newsletters/<uuid:pk>/delete/', views_frontend.newsletter_delete, name='newsletter_delete'),
    path('newsletters/<uuid:pk>/send/', views_frontend.newsletter_send, name='newsletter_send'),
    path('notifications/', views_frontend.notification_list, name='notification_list'),
    path('notifications/mark-all-read/', views_frontend.mark_all_read, name='mark_all_read'),
    path('preferences/', views_frontend.preferences, name='preferences'),
]

app_name = 'communication'
urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
    path('', include((frontend_urlpatterns, 'frontend'))),
]
