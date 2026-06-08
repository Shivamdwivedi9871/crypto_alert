import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crypto_system_alert.settings')
app = Celery('crypto_system_alert')
app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()
