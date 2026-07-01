import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.dev_settings')

app = Celery('student_analytics')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Beat schedule disabled until tasks are implemented in apps.analytics.tasks
