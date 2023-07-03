import os

from .base import MIDDLEWARE, BASE_DIR, env

DEBUG = False

ALLOWED_HOSTS = ['onlineshopproj.com']

SESSION_COOKIE_SECURE = True  # избежание случайной передачи сеанса файла cookie по HTTP
SECURE_SSL_REDIRECT = True  # перенаправление всех запросов на протокол HTTPS
CSRF_COOKIE_SECURE = True  # браузеры будут передавать куки только через HTTPS

# отправка email на почту пользователям из списка, когда происходят ошибки сервера
ADMINS = (
    ('Sergey V', 'volt.awp@gmail.com'),
)

# отправка email на почту пользователям из списка, когда происходят ошибки ссылок на страницы 404
# когда у запроса есть Referer
MANAGERS = (
    ('John Doe', 'sergey.vernyk@petalmail.com'),
)

# middleware для списка MANAGERS
MIDDLEWARE.insert(0, 'django.middleware.common.BrokenLinkEmailsMiddleware')
# почта с которой будут отправляться письма для списка ADMINS
SERVER_EMAIL = 'errors@onlineshop.com'

# (python manage.py collectstatic - собирает все статические файлы проекта и сохраняет их по этому пути)
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')

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
