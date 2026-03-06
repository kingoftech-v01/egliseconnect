"""Celery configuration for async tasks (newsletters, reports, etc)."""
import os

from celery import Celery

# Production must set DJANGO_SETTINGS_MODULE to 'config.settings.production'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

app = Celery('egliseconnect')

# String config avoids serializing configuration object to child processes
app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
