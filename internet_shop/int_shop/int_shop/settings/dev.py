import os
from .base import BASE_DIR

DEBUG = True
ALLOWED_HOSTS = ['onlineshopproj.com', '127.0.0.1', 'localhost', 'web']
INTERNAL_IPS = ['127.0.0.1']

STATIC_ROOT = os.path.join(BASE_DIR, 'assets/')
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # вывод всех сообщений с почты в shell (без SMTP)

EMAIL_HOST = 'sandbox.smtp.mailtrap.io'
EMAIL_HOST_USER = '46817091728879'
EMAIL_HOST_PASSWORD = '1110aaff92a1c8'
EMAIL_PORT = '2525'
