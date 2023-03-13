import os
from celery import Celery

# установка модуля настройки по умолчанию
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'int_shop.settings')

app = Celery('int_shop', broker='amqp://guest@localhost//', backend='rpc://')  # создание экземпляра celery
# все параметры конфигурации будут начинаться с префикса CELERY
app.config_from_object('django.conf:settings', namespace='CELERY')

# автопоиск задач для выполнения
app.autodiscover_tasks()
