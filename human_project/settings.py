"""
Django settings for human_project project.

Generated by 'django-admin startproject' using Django 5.0.3.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""
import os
from aws_parameters import get_ssm_parameter
from pathlib import Path
from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-afojhqv$obqi4%$akoxw-tv-0$s3x!hreywopzp^01%vomz+=4'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework', 
    'corsheaders',
    'django_filters',
    'human_app.apps.HumanAppConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'human_project.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'human_project.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
DEBUG = get_ssm_parameter('/human/DEBUG', 'False') == 'True'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': get_ssm_parameter('/human/DB_NAME'),
        'USER': get_ssm_parameter('/human/DB_USER'),
        'PASSWORD': get_ssm_parameter('/human/DB_PASSWORD'),
        'HOST': get_ssm_parameter('/human/DB_HOST'),
        'PORT': get_ssm_parameter('/human/DB_PORT', '3306'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'America/Sao_Paulo'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

BACKEND_EC2_PUBLIC_IP = get_ssm_parameter('/human/BACKEND_EC2_PUBLIC_IP')
FRONTEND_URL_AWS_DOMAIN = get_ssm_parameter('/human/FRONTEND_URL_AWS_DOMAIN')

ALLOWED_HOSTS = [BACKEND_EC2_PUBLIC_IP, 'localhost', '127.0.0.1']
CORS_ALLOWED_ORIGINS = [
    f"http://{BACKEND_EC2_PUBLIC_IP}:8000",
    'http://localhost:5173',  # para desenvolvimento local
]
print("teste", ALLOWED_HOSTS, CORS_ALLOWED_ORIGINS)

CORS_ALLOW_CREDENTIALS = True

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'human_app.authentication.JWTAuthenticationFromCookie',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
}

signing_key = get_ssm_parameter('/human/SIMPLE_JWT_SIGNING_KEY')
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(hours=4),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': signing_key,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_COOKIE': 'access_token',  # Nome do cookie para os tokens
    'AUTH_COOKIE_DOMAIN': None,     # Domínio do cookie
    'AUTH_COOKIE_SECURE': True,    # True em produção (https)
    'AUTH_COOKIE_HTTP_ONLY': True,  # Acesso somente HTTP, não acessível por JS
    'AUTH_COOKIE_PATH': '/',        # Caminho do cookie
    'AUTH_COOKIE_SAMESITE': 'Lax',  # Protege contra CSRF
}

# Configuração de email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USER = get_ssm_parameter('/human/EMAIL_USER')
EMAIL_PASSWORD = get_ssm_parameter('/human/EMAIL_PASSWORD')
DEFAULT_FROM_EMAIL = EMAIL_USER

"""
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
"""
