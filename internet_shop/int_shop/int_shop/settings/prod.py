import os

from .base import MIDDLEWARE, BASE_DIR, env

DEBUG = False

ALLOWED_HOSTS = env('ALLOWED_HOSTS').split(',')

# django доверяет заголовку X-Forwarded-Proto, который исходит от прокси
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
CSRF_TRUSTED_ORIGINS = env('CSRF_TRUSTED_ORIGINS').split(',')

SESSION_COOKIE_SECURE = True  # избежание случайной передачи сеанса файла cookie по HTTP
# SECURE_SSL_REDIRECT = True  # перенаправление всех запросов на протокол HTTPS
CSRF_COOKIE_SECURE = True  # браузеры будут передавать куки только через HTTPS

# отправка email на почту пользователям из списка, когда происходят ошибки сервера
ADMINS = (
    ('Sergey V', 'volt.awp@gmail.com'),
)

# отправка email на почту пользователям из списка, когда происходят ошибки ссылок на страницы 404
# когда у запроса есть Referer
# MANAGERS = (
#     ('John Doe', 'sergey.vernyk@petalmail.com'),
# )


# middleware для списка MANAGERS
MIDDLEWARE.insert(0, 'django.middleware.common.BrokenLinkEmailsMiddleware')
# почта с которой будут отправляться письма для списка ADMINS
SERVER_EMAIL = 'errors@onlineshop.com'
EMAIL_SUBJECT_PREFIX = ['Django Onlineshopproj']

# (python manage.py collectstatic - собирает все статические файлы проекта и сохраняет их по этому пути)
STATIC_ROOT = os.path.join(BASE_DIR, '/vol/web/static')
MEDIA_ROOT = os.path.join(BASE_DIR, '/vol/web/media')  # путь, по которому находятся эти файлы
STATICFILES_DIRS = (os.path.join(BASE_DIR, 'static'),)

# настройки для хранения файлов в AWS облаке (пока не используются)
# STATIC_ROOT = os.path.join(BASE_DIR, 'assets/')
# MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')  # путь, по которому находятся эти файлы


# места сохранения файлов в AWS облаке (пока не используются)
# автоматическое добавление статических файлов в S3 bucket, когда запускается команда collectstatic
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

# URL для AWS (пока не используются)
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
    'version': 1,  # версия dictConfig
    'disable_existing_loggers': False,  # сохранение логера по умолчанию
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
