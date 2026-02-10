"""Help Requests URLs."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_frontend, views_api

api_router = DefaultRouter()
api_router.register(r'requests', views_api.HelpRequestViewSet, basename='request')
api_router.register(r'categories', views_api.HelpRequestCategoryViewSet, basename='category')

api_urlpatterns = [path('', include(api_router.urls))]

frontend_urlpatterns = [
    path('create/', views_frontend.request_create, name='request_create'),
    path('', views_frontend.request_list, name='request_list'),
    path('my-requests/', views_frontend.my_requests, name='my_requests'),
    path('<uuid:pk>/', views_frontend.request_detail, name='request_detail'),
    path('<uuid:pk>/update/', views_frontend.request_update, name='request_update'),
    path('<uuid:pk>/comment/', views_frontend.request_comment, name='request_comment'),
    path('categories/', views_frontend.category_list, name='category_list'),
    path('categories/create/', views_frontend.category_create, name='category_create'),
    path('categories/<uuid:pk>/edit/', views_frontend.category_edit, name='category_edit'),
    path('categories/<uuid:pk>/delete/', views_frontend.category_delete, name='category_delete'),
]

app_name = 'help_requests'
urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
    path('', include((frontend_urlpatterns, 'frontend'))),
]
