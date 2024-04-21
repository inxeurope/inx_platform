from dotenv import load_dotenv
import os
from pathlib import Path

# Load environment variables from .env
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# Changing the secret key will log out all users
# No impact on teh databse data
SECRET_KEY = os.getenv("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '159.223.26.141', 'platform.inxeurope.dev']

CORS_ALLOWED_ORIGINS = [
    "https://platform.inxeurope.dev",
]

# Application definition

INSTALLED_APPS = [
    'daphne',
    # 'admin_tabler.apps.AdminTablerConfig',
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "debug_toolbar",
    "django_extensions",
    "django_htmx",
    "inx_platform_app.apps.InxPlatformAppConfig",
]

CSRF_COOKIE_SAMESITE = 'None'

ASGI_APPLICATION = "django_inx_platform.asgi.application"

AUTH_USER_MODEL = 'inx_platform_app.User'

MIDDLEWARE = [
    
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]

ROOT_URLCONF = "django_inx_platform.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "inx_platform_app.context_processors.server_status",
            ],
        },
    },
]

WSGI_APPLICATION = "django_inx_platform.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "mssql",
        "NAME": os.getenv("DB_NAME", default="inx_platform"),
        "HOST": os.getenv("DB_SERVER", default="inx-eugwc-inxdigital-svr.database.windows.net"),
        "PORT": os.getenv("DB_PORT", default="1433"),
        "USER": os.getenv("DB_USER", default="sa"),
        "PASSWORD": os.getenv("DB_PASSWORD", default="dellaBiella2!"),
         
        # "HOST": "inxeu.database.windows.net",
        # "PORT": "1433",
        # "USER": "inxeu_admin ",
        # "PASSWORD": "2zs$SgD*D8aNPtr@",

        # "HOST": "inxeu.database.windows.net",
        # "OPTIONS": {
        #     "driver": "ODBC Driver 18 for SQL Server",
        #     "MARS_Connection": "True",
        #     'TrustServerCertificate': "Yes",
        # }

        "OPTIONS": {
            "driver": os.getenv("DB_DRIVER", default="ODBC Driver 18 for SQL Server"),
            "extra_params": f"TrustServerCertificate=yes; Connection Timout={os.getenv('DB_CONNECTION_TIMEOUT', default=10)};"
        }
    },
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/
# STATICFILES_DIRS is a list of additional directories where Django should look for static files

STATIC_URL = "static/"
STATICFILES_DIRS = [
    BASE_DIR / "inx_platform_app/static"
    ]

# STATIC_ROOT is the directory where Django will collect all static files before deployment
STATIC_ROOT = BASE_DIR / "static_files"

# Required by whitenoise
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "/"

DATA_UPLOAD_MAX_NUMBER_FIELDS  = 25000

MEDIA_ROOT = BASE_DIR / "media_root"
MEDIA_URL = "/media/"


WHITENOISE_DEBUG = True

INTERNAL_IPS = [
    # ...
    "127.0.0.1",
    "0.0.0.0",
]
