import os
from django.conf import settings
from celery import Celery

# set default module's settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'int_shop.settings')
# create celery instance
app = Celery('int_shop', broker=settings.CELERY_BROKER_URL, backend=settings.CELERY_RESULT_BACKEND)
# all configuration parameters will be starts with CELERY prefix 
app.config_from_object('django.conf:settings', namespace='CELERY')

# auto search tasks
app.autodiscover_tasks()
