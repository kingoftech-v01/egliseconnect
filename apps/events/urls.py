"""Events URLs."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_frontend, views_api

api_router = DefaultRouter()
api_router.register(r'events', views_api.EventViewSet, basename='event')

api_urlpatterns = [path('', include(api_router.urls))]

frontend_urlpatterns = [
    path('', views_frontend.event_list, name='event_list'),
    path('calendar/', views_frontend.event_calendar, name='event_calendar'),
    path('<uuid:pk>/', views_frontend.event_detail, name='event_detail'),
    path('<uuid:pk>/rsvp/', views_frontend.event_rsvp, name='event_rsvp'),
]

app_name = 'events'
urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
    path('', include((frontend_urlpatterns, 'frontend'))),
]
