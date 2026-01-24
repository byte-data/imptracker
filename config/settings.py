
from pathlib import Path
import os
from dotenv import load_dotenv

ENV_FILE = os.getenv("ENV_FILE", os.getenv("DJANGO_ENV_FILE", ".env"))
load_dotenv(ENV_FILE)

# Define the base directory of your project
BASE_DIR = Path(__file__).resolve().parent.parent

# Core settings from environment
SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
DEBUG = os.getenv("DEBUG", "True") == "True"

# Hosts and site metadata
ALLOWED_HOSTS = [host.strip() for host in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if host.strip()]
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if origin.strip()]
SITE_URL = os.getenv("SITE_URL", "http://localhost:8000")

INSTALLED_APPS = [
 'jet.dashboard',
 'jet',
	'django.contrib.humanize',
	"crispy_forms",
		"crispy_bootstrap5",
 'django.contrib.admin','django.contrib.auth','django.contrib.contenttypes',
 'django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles',
 'import_export',
 'accounts','activities','masters','uploads','audit','dashboards',
]
AUTH_USER_MODEL='accounts.User'

# Database configuration (default to PostgreSQL)
DATABASES={
		'default':{
				'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.postgresql'),
				'NAME': os.getenv('DB_NAME', 'imptracker'),
				'USER': os.getenv('DB_USER', 'postgres'),
				'PASSWORD': os.getenv('DB_PASSWORD', 'password'),
				'HOST': os.getenv('DB_HOST', 'db' if not DEBUG else 'localhost'),
				'PORT': os.getenv('DB_PORT', '5432'),
		}
}

MIDDLEWARE = [
	'django.middleware.security.SecurityMiddleware',
	'django.contrib.sessions.middleware.SessionMiddleware',
	'django.middleware.common.CommonMiddleware',
	'django.middleware.csrf.CsrfViewMiddleware',
	'django.contrib.auth.middleware.AuthenticationMiddleware',
	'django.contrib.messages.middleware.MessageMiddleware',
	'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

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
			],
		},
	},
]
ROOT_URLCONF = 'config.urls'
STATIC_URL = '/static/'
# Optional: Directory where 'collectstatic' will gather all static files for deployment
STATIC_ROOT = BASE_DIR / 'staticfiles'
# Define the directory where your general static files are located
STATICFILES_DIRS = [BASE_DIR / 'static']
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================================================
# EMAIL CONFIGURATION - GMAIL SMTP
# ============================================================================

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', os.getenv('GMAIL_EMAIL', ''))
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', os.getenv('GMAIL_APP_PASSWORD', ''))
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER or 'no-reply@example.com')

# ============================================================================
# NOTIFICATION SETTINGS
# ============================================================================

# Enable/disable notifications
NOTIFICATIONS_ENABLED = os.getenv('NOTIFICATIONS_ENABLED', 'True') == 'True'

# Due date alert days (send alert X days before deadline)
DUE_DATE_ALERT_DAYS = int(os.getenv('DUE_DATE_ALERT_DAYS', '7'))

# Send test email (for debugging)
SEND_TEST_EMAIL = os.getenv('SEND_TEST_EMAIL', 'False') == 'True'
# Locale / TZ defaults
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/login/"


#JET_DEFAULT_THEME = 'light-gray' # green, light-violet, light-green, light-blue, light-gray
JET_SIDE_MENU_COMPACT = True


CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"

CRISPY_TEMPLATE_PACK = "bootstrap5"

# Security defaults for production
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'False') == 'True'
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False') == 'True'
CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', 'False') == 'True'
