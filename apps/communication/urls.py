"""Communication URLs."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_frontend, views_api

api_router = DefaultRouter()
api_router.register(r'newsletters', views_api.NewsletterViewSet, basename='newsletter')
api_router.register(r'notifications', views_api.NotificationViewSet, basename='notification')
api_router.register(r'preferences', views_api.NotificationPreferenceViewSet, basename='preference')
api_router.register(r'sms', views_api.SMSMessageViewSet, basename='sms')
api_router.register(r'sms-templates', views_api.SMSTemplateViewSet, basename='sms-template')
api_router.register(r'sms-optouts', views_api.SMSOptOutViewSet, basename='sms-optout')
api_router.register(r'push-subscriptions', views_api.PushSubscriptionViewSet, basename='push-subscription')
api_router.register(r'email-templates', views_api.EmailTemplateViewSet, basename='email-template')
api_router.register(r'automations', views_api.AutomationViewSet, basename='automation')
api_router.register(r'automation-steps', views_api.AutomationStepViewSet, basename='automation-step')
api_router.register(r'automation-enrollments', views_api.AutomationEnrollmentViewSet, basename='automation-enrollment')
api_router.register(r'ab-tests', views_api.ABTestViewSet, basename='ab-test')
api_router.register(r'direct-messages', views_api.DirectMessageViewSet, basename='direct-message')
api_router.register(r'group-chats', views_api.GroupChatViewSet, basename='group-chat')
api_router.register(r'group-chat-messages', views_api.GroupChatMessageViewSet, basename='group-chat-message')

api_urlpatterns = [path('', include(api_router.urls))]

frontend_urlpatterns = [
    # Newsletters
    path('newsletters/', views_frontend.newsletter_list, name='newsletter_list'),
    path('newsletters/create/', views_frontend.newsletter_create, name='newsletter_create'),
    path('newsletters/<uuid:pk>/', views_frontend.newsletter_detail, name='newsletter_detail'),
    path('newsletters/<uuid:pk>/edit/', views_frontend.newsletter_edit, name='newsletter_edit'),
    path('newsletters/<uuid:pk>/delete/', views_frontend.newsletter_delete, name='newsletter_delete'),
    path('newsletters/<uuid:pk>/send/', views_frontend.newsletter_send, name='newsletter_send'),

    # Notifications
    path('notifications/', views_frontend.notification_list, name='notification_list'),
    path('notifications/mark-all-read/', views_frontend.mark_all_read, name='mark_all_read'),
    path('preferences/', views_frontend.preferences, name='preferences'),

    # SMS
    path('sms/', views_frontend.sms_list, name='sms_list'),
    path('sms/compose/', views_frontend.sms_compose, name='sms_compose'),
    path('sms/templates/', views_frontend.sms_template_list, name='sms_template_list'),
    path('sms/templates/create/', views_frontend.sms_template_create, name='sms_template_create'),
    path('sms/templates/<uuid:pk>/edit/', views_frontend.sms_template_edit, name='sms_template_edit'),

    # Email Templates
    path('email-templates/', views_frontend.email_template_list, name='email_template_list'),
    path('email-templates/create/', views_frontend.email_template_create, name='email_template_create'),
    path('email-templates/<uuid:pk>/edit/', views_frontend.email_template_edit, name='email_template_edit'),
    path('email-templates/<uuid:pk>/preview/', views_frontend.email_template_preview, name='email_template_preview'),

    # Push Notifications
    path('push/test/', views_frontend.push_test, name='push_test'),

    # Automation
    path('automations/', views_frontend.automation_list, name='automation_list'),
    path('automations/create/', views_frontend.automation_create, name='automation_create'),
    path('automations/<uuid:pk>/', views_frontend.automation_detail, name='automation_detail'),
    path('automations/<uuid:pk>/steps/add/', views_frontend.automation_step_add, name='automation_step_add'),

    # Analytics
    path('analytics/', views_frontend.analytics_dashboard, name='analytics_dashboard'),

    # A/B Tests
    path('ab-tests/<uuid:pk>/results/', views_frontend.abtest_results, name='abtest_results'),

    # Direct Messaging
    path('messages/', views_frontend.message_inbox, name='message_inbox'),
    path('messages/compose/', views_frontend.message_compose, name='message_compose'),
    path('messages/<uuid:pk>/', views_frontend.message_detail, name='message_detail'),

    # Group Chats
    path('group-chats/', views_frontend.group_chat_list, name='group_chat_list'),
    path('group-chats/create/', views_frontend.group_chat_create, name='group_chat_create'),
    path('group-chats/<uuid:pk>/', views_frontend.group_chat_detail, name='group_chat_detail'),

    # Social Media (stubs)
    path('social-media/', views_frontend.social_media_dashboard, name='social_media_dashboard'),
]

app_name = 'communication'
urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
    path('', include((frontend_urlpatterns, 'frontend'))),
]
