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

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-#3zoxjm74+ulis&afz#b@*15&6u1eq3t48mi1)jxwcv&r63v4!'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = [
    'account.apps.AccountConfig',  # должно быть на первом месте для собственного вывода шаблона logged_out.html
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'goods.apps.GoodsConfig',
    'django_bootstrap5',
    'django_extensions',
    'orders.apps.OrdersConfig',
    'coupons.apps.CouponsConfig',
    'present_cards.apps.PresentCardsConfig',
    'cart.apps.CartConfig',
    'payment.apps.PaymentConfig',
    'easy_thumbnails',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'int_shop.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'goods.context_processors.product_categories',  # категории товаров на любом шаблоне
                'cart.context_processors.cart'  # корзина в любом шаблоне

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

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = 'static/'
# (python manage.py collectstatic - собирает все статические файлы проекта и сохраняет их по этому пути)
# STATIC_ROOT = os.path.join(BASE_DIR, 'static/')
STATICFILES_DIRS = [
    BASE_DIR / "static"
]

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# пути для сохранения пользовательских файлов с сайта
MEDIA_URL = '/media/'  # файлы загружены пользователем
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')  # путь, по которому находятся эти файлы

LOGIN_REDIRECT_URL = 'goods:product_list'
LOGOUT_REDIRECT_URL = 'login'
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # вывод всех сообщений с почты в shell (без SMTP)
CART_SESSION_ID = 'cart'

STRIPE_PUBLISHABLE_KEY = env('STRIPE_PUBLISHABLE_KEY')
STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = env('STRIPE_WEBHOOK_SECRET')

EMAIL_HOST = env('EMAIL_HOST')
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
EMAIL_PORT = env('EMAIL_PORT')
EMAIL_USE_SSL = False
EMAIL_USE_TLS = True
FROM_EMAIL = env('FROM_EMAIL')

# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
