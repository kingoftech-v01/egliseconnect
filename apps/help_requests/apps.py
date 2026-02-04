"""Help Requests app configuration."""
from django.apps import AppConfig


class HelpRequestsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.help_requests'
    verbose_name = 'Help Requests'
