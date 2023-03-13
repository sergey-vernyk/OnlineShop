# обеспечение запуска при запуске проекта
# shared_task использует это приложение
from .celery import app as celery_app

__all__ = ('celery_app',)
