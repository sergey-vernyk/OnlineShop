import os
from .base import BASE_DIR, env

DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'web']
INTERNAL_IPS = ['127.0.0.1']

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'assets/')
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # print all email messages to shell (without SMTP)
EMAIL_HOST = env('TEST_EMAIL_HOST')
EMAIL_HOST_USER = env('TEST_EMAIL_USER')
EMAIL_HOST_PASSWORD = env('TEST_EMAIL_PASSWORD')
EMAIL_PORT = env('TEST_EMAIL_PORT')

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

# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'handlers': {
#         'console': {
#             'class': 'logging.StreamHandler',
#         },
#     },
#     'loggers': {
#         'django.db.backends': {
#             'handlers': ['console'],
#             'level': 'DEBUG',
#         },
#     },
# }
