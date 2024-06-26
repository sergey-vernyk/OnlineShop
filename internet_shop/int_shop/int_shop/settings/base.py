import os
from pathlib import Path

import environ
from django.utils.translation import gettext_lazy as _

# init environment variables
env = environ.Env()
environ.Env.read_env()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
SITE_ID = 1

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('DJANGO_SECRET_KEY')

# Application definition

INSTALLED_APPS = [
    'account.apps.AccountConfig',
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
    'rest_framework',
    'rest_framework.authtoken',
    'django_summernote',
    'storages',
    'django_filters',
    'drf_yasg',
    'parler',

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
    'django.middleware.locale.LocaleMiddleware',  # middleware for localization the project
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.contrib.sites.middleware.CurrentSiteMiddleware',
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

                'goods.context_processors.product_categories',  # goods categories in all templates
                'cart.context_processors.cart',  # cart in all templates
                'goods.context_processors.search_form',  # search field in all templates
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]

WSGI_APPLICATION = 'int_shop.wsgi.application'

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

LANGUAGE_CODE = 'en'

LANGUAGES = (
    ('en', _('English')),
    ('uk', _('Ukrainian')),
)

# path where Django looks for translations files
LOCALE_PATHS = (
    os.path.join(BASE_DIR, './locale/'),
    os.path.join(BASE_DIR, './goods/locale/'),
    os.path.join(BASE_DIR, './account/locale/'),
    os.path.join(BASE_DIR, './cart/locale/'),
    os.path.join(BASE_DIR, './coupon/locale/'),
    os.path.join(BASE_DIR, './present_cards/locale/'),
    os.path.join(BASE_DIR, './orders/locale/'),
    os.path.join(BASE_DIR, './payment/locale/'),
)

PARLER_LANGUAGES = {
    SITE_ID: (
        {'code': 'en'},
        {'code': 'uk'},
    ),
    'default': {
        'fallbacks': ['en'],  # translation language by default
        'hide_untranslated': False,  # settings for display no translated content
    }
}

TIME_ZONE = 'Europe/Kyiv'

USE_I18N = True

USE_TZ = True

USE_L10N = False  # displaying date, using another format (not current) locale

DATETIME_FORMAT = 'd/m/y l H:i:s'  # 24-hours time format (day/month/year weekday hours:minutes:seconds)

DATE_INPUT_FORMATS = ('%d-%m-%Y',)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_REDIRECT_URL = 'goods:product_list'
LOGOUT_REDIRECT_URL = 'login'
LOGIN_URL = 'login'
CART_SESSION_ID = 'cart'

STRIPE_PUBLISHABLE_KEY = env('STRIPE_PUBLISHABLE_KEY')
STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = env('STRIPE_WEBHOOK_SECRET')

FROM_EMAIL = env('FROM_EMAIL')

# duration for validity link for reset password (validity of token)
PASSWORD_RESET_TIMEOUT = 14400

# config Redis as simple DB
REDIS_PORT = env('REDIS_PORT')
REDIS_HOST = env('REDIS_HOST')
REDIS_DB_NUM = env('REDIS_DB_NUM')
REDIS_USER = env('REDIS_USER')
REDIS_PASSWORD = env('REDIS_PASSWORD')

# celery config
CELERY_BROKER_URL = env('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND')

# Redis Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': f'redis://{REDIS_USER}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{env("REDIS_CACHE_NUM")}',
    }
}

# Users Authentication models
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',  # built-in model
    'social_core.backends.facebook.FacebookOAuth2',  # authorization through Facebook
    'social_core.backends.google.GoogleOAuth2',  # authorization through Google
)

SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'account.utils.create_user',  # overriding the method for replacing `.` in username
    'account.views.save_social_user_to_profile',  # save user to Profile while login through social
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
)

# Facebook
ACCESS_FACEBOOK_USER_TOKEN = env('ACCESS_FACEBOOK_USER_TOKEN')
SOCIAL_AUTH_FACEBOOK_KEY = env('SOCIAL_AUTH_FACEBOOK_KEY')
SOCIAL_AUTH_FACEBOOK_SECRET = env('SOCIAL_AUTH_FACEBOOK_SECRET')
SOCIAL_AUTH_FACEBOOK_SCOPE = ['email', 'user_gender', 'user_birthday']  # additional permissions for authorization

# passing additional parameters from facebook account
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {
    'fields': 'id, name, first_name, last_name, birthday, email, gender, picture.width(80).height(80)',
}

# Google
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = env('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = env('SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET')
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = ['https://www.googleapis.com/auth/user.gender.read',
                                   'https://www.googleapis.com/auth/user.birthday.read']
API_KEY_GOOGLE = env('API_KEY_GOOGLE')
BEARER_AUTHORIZATION_TOKEN_GOOGLE = env('BEARER_AUTHORIZATION_TOKEN_GOOGLE')

# summernote setting for editing Description field in Product model
SUMMERNOTE_CONFIG = {
    'summernote': {
        'width': '80%',
        'height': '480',
    }
}

# DRF settings
REST_FRAMEWORK = {
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES':
        ('rest_framework.authentication.TokenAuthentication',
         'rest_framework.authentication.BasicAuthentication',
         'rest_framework.authentication.SessionAuthentication'),
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning',
    'DEFAULT_VERSION': 'v1',
    'ALLOWED_VERSIONS': ['v1', 'v2'],
}

SWAGGER_SETTINGS = {
    'USE_SESSION_AUTH': True,
    'LOGIN_URL': '/account/login/',
    'LOGOUT_URL': '/account/logout/',
    'REFETCH_SCHEMA_WITH_AUTH': True,
    'REFETCH_SCHEMA_ON_LOGOUT': True,
    'DEFAULT_MODEL_RENDERING': 'example',
    'VALIDATOR_URL': 'http://127.0.0.1:8189',
    'PERSIST_AUTH': True,
}

REDOC_SETTINGS = {
    'PATH_IN_MIDDLE': True
}
