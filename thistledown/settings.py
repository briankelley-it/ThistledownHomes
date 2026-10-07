"""
Django settings for the Thistledown Homes site.

Configuration comes from environment variables so the same code runs locally
and in production. See .env.example for the full list.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in {'1', 'true', 'yes', 'on'}


def env_list(name, default=''):
    return [item.strip() for item in os.environ.get(name, default).split(',') if item.strip()]


DEBUG = env_bool('DJANGO_DEBUG', True)

# A real secret key is required when DEBUG is off.
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', '')
if not SECRET_KEY:
    if not DEBUG:
        raise RuntimeError('Set DJANGO_SECRET_KEY when DJANGO_DEBUG is off.')
    SECRET_KEY = 'dev-only-insecure-key-change-me'

ALLOWED_HOSTS = env_list('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,[::1]')
CSRF_TRUSTED_ORIGINS = env_list('DJANGO_CSRF_TRUSTED_ORIGINS')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    # WhiteNoise also serves static files in development, with byte-range support (needed for video looping and Safari).
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'django.contrib.humanize',
    # Google sign-in for the admin.
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'website',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'thistledown.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'website.context_processors.site',
            ],
        },
    },
]

WSGI_APPLICATION = 'thistledown.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.environ.get('DJANGO_DB_PATH', BASE_DIR / 'db.sqlite3'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/Chicago'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
WHITENOISE_USE_FINDERS = DEBUG
WHITENOISE_AUTOREFRESH = DEBUG
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage' if not DEBUG
        else 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
}

# Photos uploaded in the admin.
MEDIA_URL = 'media/'
MEDIA_ROOT = Path(os.environ.get('DJANGO_MEDIA_ROOT', BASE_DIR / 'media'))

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Email: contact form notifications. Prints to the console unless SMTP is configured.
EMAIL_BACKEND = os.environ.get('DJANGO_EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', '')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = env_bool('EMAIL_USE_TLS', True)
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'webmaster@localhost')

# Business details shown across the site.
SITE_INFO = {
    'name': 'Thistledown Homes',
    'email': os.environ.get('SITE_EMAIL', 'hello@example.com'),
    'phone': os.environ.get('SITE_PHONE', '(555) 010-0199'),
    'phone_link': os.environ.get('SITE_PHONE_LINK', '+15550100199'),
    'area': os.environ.get('SITE_AREA', 'Central Texas (fictional demo)'),
    'domain': os.environ.get('SITE_DOMAIN', 'https://www.example.com'),
    # Trustpilot: leave empty to show the footer placeholder. Add your business unit ID to show the real TrustBox.
    'trustpilot_business_id': os.environ.get('TRUSTPILOT_BUSINESS_UNIT_ID', ''),
    'trustpilot_url': os.environ.get('TRUSTPILOT_REVIEW_URL', ''),
    # Live chat: leave empty to use the built-in message bubble. Add Tawk.to IDs for real-time chat.
    'tawk_property_id': os.environ.get('TAWK_PROPERTY_ID', ''),
    'tawk_widget_id': os.environ.get('TAWK_WIDGET_ID', 'default'),
    # Map styles for the /map/ page. OpenFreeMap is free (including commercial use) with no key or limits.
    # Any MapLibre-compatible style URL works, e.g. from MapTiler or Stadia Maps.
    'map_style_light': os.environ.get('MAP_STYLE_LIGHT') or 'https://tiles.openfreemap.org/styles/positron',
    'map_style_dark': os.environ.get('MAP_STYLE_DARK') or 'https://tiles.openfreemap.org/styles/dark',
}
# Google sign-in for /admin/. Create an OAuth client at console.cloud.google.com (APIs & Services > Credentials),
# add https://YOUR-DOMAIN/accounts/google/login/callback/ as an authorized redirect URI, then set these two.
# The Google button stays disabled until both are set.
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APPS': [{'client_id': GOOGLE_CLIENT_ID, 'secret': GOOGLE_CLIENT_SECRET}] if GOOGLE_CLIENT_ID else [],
        'SCOPE': ['profile', 'email'],
    },
}
ACCOUNT_ADAPTER = 'website.adapters.AccountAdapter'
SOCIALACCOUNT_ADAPTER = 'website.adapters.SocialAccountAdapter'
ACCOUNT_LOGIN_METHODS = {'username', 'email'}
ACCOUNT_EMAIL_VERIFICATION = 'none'
# Google verifies emails, so an existing user (like you) can sign in with the Google account matching their email.
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True
LOGIN_URL = 'admin:login'
LOGIN_REDIRECT_URL = 'admin:index'

# Where new contact messages are emailed. Leave empty to only store them in the admin.
CONTACT_NOTIFY_EMAIL = os.environ.get('CONTACT_NOTIFY_EMAIL', '')

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = env_bool('DJANGO_SSL_REDIRECT', True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.environ.get('DJANGO_HSTS_SECONDS', '3600'))
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
