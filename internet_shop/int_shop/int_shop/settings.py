"""
Django settings for int_shop project.

Generated by 'django-admin startproject' using Django 4.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""
import os
from pathlib import Path
import environ

# инициализация переменных окружения
env = environ.Env()
environ.Env.read_env()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
SITE_ID = 1
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('DJANGO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['onlineshopproj.com', '127.0.0.1', 'localhost', 'web']
INTERNAL_IPS = ['127.0.0.1']

# Application definition

INSTALLED_APPS = [
    'account.apps.AccountConfig',  # должно быть на первом месте для собственного вывода шаблона logged_out.html
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django_bootstrap5',
    'django_extensions',
    'debug_toolbar',
    'django.contrib.postgres',
    'social_django',
    'rest_framework.authtoken',
    'django_summernote',

    'goods.apps.GoodsConfig',
    'orders.apps.OrdersConfig',
    'coupons.apps.CouponsConfig',
    'present_cards.apps.PresentCardsConfig',
    'cart.apps.CartConfig',
    'payment.apps.PaymentConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.contrib.sites.middleware.CurrentSiteMiddleware',
    'common.middleware.previous_and_current_urls_middleware',  # сохраняет текущий и предыдущий URL адреса в сессию
]

ROOT_URLCONF = 'int_shop.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',

                'goods.context_processors.product_categories',  # категории товаров на любом шаблоне
                'cart.context_processors.cart',  # корзина в любом шаблоне
                'goods.context_processors.search_form',  # строка поиска в любом шаблоне
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]

WSGI_APPLICATION = 'int_shop.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

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

# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Kyiv'

USE_I18N = True

USE_TZ = True

USE_L10N = False  # отображение числа и даты, используя формат другой (не текущей локали) локали

DATETIME_FORMAT = 'd/m/y l H:i:s'  # формат времени 24 часа (день/месяц/год День недели часы:минуты:секунды)

DATE_INPUT_FORMATS = ('%d-%m-%Y',)

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = 'static/'
# (python manage.py collectstatic - собирает все статические файлы проекта и сохраняет их по этому пути)
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')
# STATICFILES_DIRS = [
#     BASE_DIR / "static",
# ]

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# пути для сохранения пользовательских файлов с сайта
MEDIA_URL = '/media/'  # файлы загружены пользователем
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')  # путь, по которому находятся эти файлы

LOGIN_REDIRECT_URL = 'goods:product_list'
LOGOUT_REDIRECT_URL = 'login'
LOGIN_URL = 'login'
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # вывод всех сообщений с почты в shell (без SMTP)
CART_SESSION_ID = 'cart'

STRIPE_PUBLISHABLE_KEY = env('STRIPE_PUBLISHABLE_KEY')
STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = env('STRIPE_WEBHOOK_SECRET')

# EMAIL_HOST = env('EMAIL_HOST')
# EMAIL_HOST_USER = env('EMAIL_HOST_USER')
# EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
# EMAIL_PORT = env('EMAIL_PORT')
# EMAIL_USE_SSL = False
# EMAIL_USE_TLS = True
FROM_EMAIL = env('FROM_EMAIL')

EMAIL_HOST = 'sandbox.smtp.mailtrap.io'
EMAIL_HOST_USER = '46817091728879'
EMAIL_HOST_PASSWORD = '1110aaff92a1c8'
EMAIL_PORT = '2525'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# длительность валидности ссылки для сброса пароля
PASSWORD_RESET_TIMEOUT = 14400

# конфигурация Redis в качестве БД
REDIS_PORT = env('REDIS_PORT')
REDIS_HOST = env('REDIS_HOST')
REDIS_DB_NUM = env('REDIS_DB_NUM')
REDIS_USER = env('REDIS_USER')
REDIS_PASSWORD = env('REDIS_PASSWORD')

CELERY_BROKER_URL = env('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND')

# конфигурация кеша на основе Redis
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': f'redis://{REDIS_USER}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{env("REDIS_CACHE_NUM")}',
    }
}

# Модели аутентификации пользователей
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',  # встроенная модель
    'social_core.backends.facebook.FacebookOAuth2',  # авторизация на сайте при помощи Facebook
    'social_core.backends.google.GoogleOAuth2',  # авторизация на сайте при помощи Google
)

SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'account.utils.create_user',  # переопределение метода для замены "." в username
    'account.views.save_social_user_to_profile',  # сохранение пользователя в Profile при входе через соц.сеть
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
)

# Facebook
SOCIAL_AUTH_FACEBOOK_KEY = env('SOCIAL_AUTH_FACEBOOK_KEY')
SOCIAL_AUTH_FACEBOOK_SECRET = env('SOCIAL_AUTH_FACEBOOK_SECRET')
SOCIAL_AUTH_FACEBOOK_SCOPE = ['email', 'user_gender', 'user_birthday']  # дополнительные разрешения для авторизации

# передача дополнительных параметров с facebook аккаунта
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {
    'fields': 'id, name, first_name, last_name, birthday, email, gender, picture.width(80).height(80)',
}

# Google
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = env('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = env('SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET')
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = ['https://www.googleapis.com/auth/user.gender.read',
                                   'https://www.googleapis.com/auth/user.birthday.read']

# настройки summernote для редактирования поля Description в модели Product
SUMMERNOTE_CONFIG = {
    'summernote': {
        'width': '80%',
        'height': '480',
    }
}
