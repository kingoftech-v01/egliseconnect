"""Help Requests URLs."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_frontend, views_api

api_router = DefaultRouter()
api_router.register(r'requests', views_api.HelpRequestViewSet, basename='request')
api_router.register(r'categories', views_api.HelpRequestCategoryViewSet, basename='category')
api_router.register(r'pastoral-care', views_api.PastoralCareViewSet, basename='pastoral-care')
api_router.register(r'prayer-requests', views_api.PrayerRequestViewSet, basename='prayer-request')
api_router.register(r'care-teams', views_api.CareTeamViewSet, basename='care-team')
api_router.register(r'care-team-members', views_api.CareTeamMemberViewSet, basename='care-team-member')
api_router.register(r'benevolence-funds', views_api.BenevolenceFundViewSet, basename='benevolence-fund')
api_router.register(r'benevolence-requests', views_api.BenevolenceRequestViewSet, basename='benevolence-request')
api_router.register(r'meal-trains', views_api.MealTrainViewSet, basename='meal-train')
api_router.register(r'meal-signups', views_api.MealSignupViewSet, basename='meal-signup')
api_router.register(r'crisis-protocols', views_api.CrisisProtocolViewSet, basename='crisis-protocol')
api_router.register(r'crisis-resources', views_api.CrisisResourceViewSet, basename='crisis-resource')

api_urlpatterns = [path('', include(api_router.urls))]

frontend_urlpatterns = [
    # Existing help request views
    path('create/', views_frontend.request_create, name='request_create'),
    path('', views_frontend.request_list, name='request_list'),
    path('my-requests/', views_frontend.my_requests, name='my_requests'),
    path('<uuid:pk>/', views_frontend.request_detail, name='request_detail'),
    path('<uuid:pk>/update/', views_frontend.request_update, name='request_update'),
    path('<uuid:pk>/comment/', views_frontend.request_comment, name='request_comment'),

    # Category CRUD (P1)
    path('categories/', views_frontend.category_list, name='category_list'),
    path('categories/create/', views_frontend.category_create, name='category_create'),
    path('categories/<uuid:pk>/edit/', views_frontend.category_edit, name='category_edit'),
    path('categories/<uuid:pk>/delete/', views_frontend.category_delete, name='category_delete'),

    # Pastoral Care (P1)
    path('care/', views_frontend.care_dashboard, name='care_dashboard'),
    path('care/create/', views_frontend.care_create, name='care_create'),
    path('care/calendar/', views_frontend.care_calendar, name='care_calendar'),
    path('care/<uuid:pk>/', views_frontend.care_detail, name='care_detail'),
    path('care/<uuid:pk>/update/', views_frontend.care_update, name='care_update'),

    # Care Teams (P1)
    path('care/teams/', views_frontend.care_team_list, name='care_team_list'),
    path('care/teams/create/', views_frontend.care_team_create, name='care_team_create'),
    path('care/teams/<uuid:pk>/', views_frontend.care_team_detail, name='care_team_detail'),
    path('care/teams/<uuid:pk>/add-member/', views_frontend.care_team_add_member, name='care_team_add_member'),
    path('care/teams/<uuid:pk>/remove-member/<uuid:member_pk>/', views_frontend.care_team_remove_member, name='care_team_remove_member'),

    # Prayer Requests (P1)
    path('prayer/create/', views_frontend.prayer_request_create, name='prayer_create'),
    path('prayer/wall/', views_frontend.prayer_wall, name='prayer_wall'),
    path('prayer/anonymous/', views_frontend.prayer_request_anonymous, name='prayer_anonymous'),
    path('prayer/anonymous/done/', views_frontend.prayer_anonymous_done, name='prayer_anonymous_done'),
    path('prayer/moderation/', views_frontend.prayer_moderation, name='prayer_moderation'),
    path('prayer/<uuid:pk>/', views_frontend.prayer_request_detail, name='prayer_detail'),
    path('prayer/<uuid:pk>/answered/', views_frontend.prayer_mark_answered, name='prayer_answered'),
    path('prayer/<uuid:pk>/moderate/', views_frontend.prayer_moderate_action, name='prayer_moderate'),

    # Benevolence Fund (P3)
    path('benevolence/', views_frontend.benevolence_list, name='benevolence_list'),
    path('benevolence/create/', views_frontend.benevolence_request_create, name='benevolence_create'),
    path('benevolence/<uuid:pk>/', views_frontend.benevolence_detail, name='benevolence_detail'),
    path('benevolence/<uuid:pk>/approve/', views_frontend.benevolence_approve, name='benevolence_approve'),
    path('benevolence/<uuid:pk>/disburse/', views_frontend.benevolence_disburse, name='benevolence_disburse'),

    # Meal Train (P3)
    path('meals/', views_frontend.meal_train_list, name='meal_train_list'),
    path('meals/create/', views_frontend.meal_train_create, name='meal_train_create'),
    path('meals/<uuid:pk>/', views_frontend.meal_train_detail, name='meal_train_detail'),
    path('meals/<uuid:pk>/signup/', views_frontend.meal_train_signup, name='meal_train_signup'),

    # Crisis Response (P3)
    path('crisis/protocols/', views_frontend.crisis_protocol_list, name='crisis_protocol_list'),
    path('crisis/protocols/create/', views_frontend.crisis_protocol_create, name='crisis_protocol_create'),
    path('crisis/protocols/<uuid:pk>/', views_frontend.crisis_protocol_detail, name='crisis_protocol_detail'),
    path('crisis/resources/', views_frontend.crisis_resource_list, name='crisis_resource_list'),
    path('crisis/resources/create/', views_frontend.crisis_resource_create, name='crisis_resource_create'),
    path('crisis/notify/', views_frontend.crisis_notify, name='crisis_notify'),
]

app_name = 'help_requests'
urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
    path('', include((frontend_urlpatterns, 'frontend'))),
]
