import os
import sys
import dj_database_url
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SECRET_KEY")


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG", "False") == "True"

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    ".herokuapp.com",
    ".ngrok-free.app",
    ".ngrok-free.dev",
]


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "accounts",
    "core",
    "products",
    "cart",
    "orders",
    "wishlist",
    "reviews",
    "sommelier",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "uncorked.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "products.context_processors.countries",
                "sommelier.context_processors.sommelier_questions",
                "orders.context_processors.promotions",
                "cart.context_processors.cart_bottle_count",
            ],
        },
    },
]

WSGI_APPLICATION = "uncorked.wsgi.application"


# Database: DATABASE_URL in production (Neon), local SQLite otherwise.
# Connections are reused for up to 10 minutes; the health check pings a
# reused connection first, so one closed while Neon was idle is replaced
# with a fresh connection instead of failing the request.
DATABASES = {
    "default": dj_database_url.config(
        default=f'sqlite:///{BASE_DIR / "db.sqlite3"}',
        conn_max_age=600,
        conn_health_checks=True,
    )
}


# Password validation

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
# https://docs.djangoproject.com/en/6.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images) are served by WhiteNoise
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files: Cloudinary when CLOUDINARY_URL is set, local folder otherwise
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

if os.environ.get("CLOUDINARY_URL"):
    MEDIA_STORAGE = "uncorked.storages.CloudinaryMediaStorage"
else:
    MEDIA_STORAGE = "django.core.files.storage.FileSystemStorage"
STATIC_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Tests never upload media, don't need a collectstatic manifest, always use
# a local SQLite database and hash passwords with a fast test-only hasher
if "test" in sys.argv:
    MEDIA_STORAGE = "django.core.files.storage.InMemoryStorage"
    STATIC_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
    PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

STORAGES = {
    "default": {"BACKEND": MEDIA_STORAGE},
    "staticfiles": {"BACKEND": STATIC_STORAGE},
}

# Email
if os.environ.get("EMAIL_HOST_PASS"):
    MAILERS = {
        "default": {
            "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
            "OPTIONS": {
                "host": "smtp.gmail.com",
                "port": 587,
                "use_tls": True,
                "username": os.environ.get("EMAIL_HOST_USER"),
                "password": os.environ.get("EMAIL_HOST_PASS"),
            },
        },
    }
    DEFAULT_FROM_EMAIL = os.environ.get("EMAIL_HOST_USER")
else:
    MAILERS = {
        "default": {
            "BACKEND": "django.core.mail.backends.console.EmailBackend",
        },
    }

AUTH_USER_MODEL = "accounts.CustomUser"


SITE_ID = 1
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_ADAPTER = "accounts.adapter.AccountAdapter"
# Subjects already name Uncorked, so no "[Site] " prefix
ACCOUNT_EMAIL_SUBJECT_PREFIX = ""

# Stripe
STRIPE_PUBLIC_KEY = os.environ.get("STRIPE_PUBLIC_KEY")
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

# Logging: app messages go to the console, which Heroku collects in its logs
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "loggers": {
        "orders": {
            "handlers": ["console"],
            # Tests check log output with assertLogs instead of printing it
            "level": "CRITICAL" if "test" in sys.argv else "INFO",
        },
    },
}
