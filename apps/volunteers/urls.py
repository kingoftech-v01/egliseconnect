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
    path('positions/', views_frontend.position_list, name='position_list'),
    path('schedule/', views_frontend.schedule_list, name='schedule_list'),
    path('my-schedule/', views_frontend.my_schedule, name='my_schedule'),
    path('availability/', views_frontend.availability_update, name='availability_update'),
]

app_name = 'volunteers'
urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
    path('', include((frontend_urlpatterns, 'frontend'))),
]
