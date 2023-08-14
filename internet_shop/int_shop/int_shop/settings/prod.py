import os

from .base import MIDDLEWARE, BASE_DIR, env

DEBUG = False

ALLOWED_HOSTS = env('ALLOWED_HOSTS').split(',')

# django trusts header X-Forwarded-Proto, which come from proxy который исходит от прокси
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
CSRF_TRUSTED_ORIGINS = env('CSRF_TRUSTED_ORIGINS').split(',')

SESSION_COOKIE_SECURE = True  # avoiding accidental transferring cookies over HTTP
# SECURE_SSL_REDIRECT = True  # redirection all requests to HTTPS protocol
CSRF_COOKIE_SECURE = True  # browsers will transfer cookies only over HTTPS

# sending email to users in list below, when server errors occurred
ADMINS = (
    ('Sergey V', 'volt.awp@gmail.com'),
)

# sending email to users in list below, when occurred 404 pages links errors
# when request has Referer header
# MANAGERS = (
#     ('John Doe', 'sergey.vernyk@petalmail.com'),
# )


# middleware for list MANAGERS
MIDDLEWARE.insert(0, 'django.middleware.common.BrokenLinkEmailsMiddleware')
# email, from which will be sending emails for ADMINS list
SERVER_EMAIL = 'errors@onlineshop.com'
EMAIL_SUBJECT_PREFIX = ['Django Onlineshopproj']

# (python manage.py collectstatic - gathers all static file in project and saving their to this path)
STATIC_ROOT = os.path.join(BASE_DIR, '/vol/web/static')  # path, where these files are located
MEDIA_ROOT = os.path.join(BASE_DIR, '/vol/web/media')
STATICFILES_DIRS = (os.path.join(BASE_DIR, 'static'),)

# settings for saving files in AWS Cloud (not used for now)
# STATIC_ROOT = os.path.join(BASE_DIR, 'assets/')
# MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')  # path, where these files are located


# places for saving files in AWS Cloud (not used for now)
# auto adding static files to S3 Bucket, when collectstatic command starts
# STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
# DEFAULT_FILE_STORAGE = 'common.storage_backends.MediaStorage'

AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
AWS_DEFAULT_ACL = env('AWS_DEFAULT_ACL')

AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
AWS_LOCATION = 'static'
PUBLIC_MEDIA_LOCATION = 'media'
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'

# URL for AWS (not used for now)
# STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_LOCATION}/'
# MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{PUBLIC_MEDIA_LOCATION}/'

STATIC_URL = 'static/'
MEDIA_URL = 'media/'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
EMAIL_PORT = env('EMAIL_PORT')
EMAIL_USE_SSL = False
EMAIL_USE_TLS = True

LOGGING = {
    'version': 1,  # dictConfig version
    'disable_existing_loggers': False,  # keep save logger by default
    'handlers': {
        'handler_log': {
            'class': 'logging.FileHandler',
            'filename': 'main_log.log',
            'level': 'DEBUG',
        },
    },
    'loggers': {
        '': {
            'level': 'DEBUG',
            'handlers': ['handler_log'],
        }
    }

}

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
