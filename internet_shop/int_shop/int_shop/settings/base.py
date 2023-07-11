"""
Django settings for int_shop project.

Generated by 'django-admin startproject' using Django 4.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""
from pathlib import Path
import environ

# инициализация переменных окружения
env = environ.Env()
environ.Env.read_env()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
SITE_ID = 1
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('DJANGO_SECRET_KEY')

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
    'storages',

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

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_REDIRECT_URL = 'goods:product_list'
LOGOUT_REDIRECT_URL = 'login'
LOGIN_URL = 'login'
CART_SESSION_ID = 'cart'

STRIPE_PUBLISHABLE_KEY = env('STRIPE_PUBLISHABLE_KEY')
STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = env('STRIPE_WEBHOOK_SECRET')

FROM_EMAIL = env('FROM_EMAIL')

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