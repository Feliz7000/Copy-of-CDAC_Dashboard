"""
WSGI config for Student Analytics Platform.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.dev_settings')
application = get_wsgi_application()
