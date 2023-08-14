import os
from .base import BASE_DIR, env

DEBUG = True
ALLOWED_HOSTS = ['onlineshopproj.com', '127.0.0.1', 'localhost', 'web']
INTERNAL_IPS = ['127.0.0.1']

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'assets/')
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # print all email messages to shell (without SMTP)
EMAIL_HOST = 'sandbox.smtp.mailtrap.io'
EMAIL_HOST_USER = '46817091728879'
EMAIL_HOST_PASSWORD = '1110aaff92a1c8'
EMAIL_PORT = '2525'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': '/var/run/postgresql',
        'NAME': env('DATABASE_NAME'),
        'USER': env('DATABASE_USER'),
        'PORT': env('DATABASE_PORT'),
        'PASSWORD': env('DATABASE_PASSWORD'),
    }
}
