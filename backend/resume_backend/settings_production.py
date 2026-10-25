"""
Django settings for backend project - VERSION PRODUCTION SÉCURISÉE
Utilise python-decouple pour la gestion des variables d'environnement
"""
from pathlib import Path
from datetime import timedelta
from decouple import config, Csv
import os
from celery.schedules import crontab

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY: Clé secrète depuis .env (OBLIGATOIRE en production)
SECRET_KEY = config('SECRET_KEY')

# SECURITY: DEBUG doit être False en production
DEBUG = False # Temporairement pour le développement

# ── DIAGNOSTIC SQL TEMPORAIRE (tâche 60) ─────────────────────────────────────
# Indépendant de DEBUG : permet d'activer Silk sur le serveur le temps d'une
# mesure, puis de le désactiver (ENABLE_SILK=False).
ENABLE_SILK = config('ENABLE_SILK', default=False, cast=bool)

# Hosts autorisés
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    'resumecours.gestionhospitaliare.site',  # Domaine de production
    'www.resumecours.gestionhospitaliare.site',  # Avec www si applicable
    '180.149.197.29',  # IP serveur de production
    'gestionhospitaliare.site',
    'vps114384.serveur-vps.net',
    'ftp.gestionhospitaliare.site',  # Domaine FTP (évite les DisallowedHost en logs)
]
#config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt',
    'corsheaders',
    'drf_yasg',
    'users',
    'django_celery_beat',
    'courses',
    'payments',
    'security',
    'notifications',
    'analytics'
]

if ENABLE_SILK:
    INSTALLED_APPS.append('silk')

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if ENABLE_SILK:
    MIDDLEWARE.insert(1, 'silk.middleware.SilkyMiddleware')

# Silk utilise `login_required` : pointer vers la connexion admin Django.
LOGIN_URL = '/admin/login/'
LOGIN_REDIRECT_URL = '/admin/'

# ── SILK — DIAGNOSTIC SQL TEMPORAIRE (tâche 60) ──────────────────────────────
if ENABLE_SILK:
    SILKY_AUTHENTICATION = True
    SILKY_AUTHORISATION = True
    SILKY_PERMISSIONS = lambda user: bool(user and user.is_superuser)
    SILKY_MAX_RECORDED_REQUESTS = 2000
    SILKY_PYTHON_PROFILER = False
    SILKY_ANALYZE_QUERIES = True

ROOT_URLCONF = 'backend.urls'

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

WSGI_APPLICATION = 'backend.wsgi.application'

# Database - Configuration sécurisée via .env
import pymysql
pymysql.install_as_MySQLdb()

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),

    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Kinshasa'
USE_I18N = True
USE_L10N = True
USE_TZ = False

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static'] if (BASE_DIR / 'static').exists() else []

# Media files
MEDIA_URL = '/media/'
#MEDIA_ROOT = '/home/jey/resumecours.gestionhospitaliare.site/backend/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

#EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='')

# Email(s) de l'administration pour les notifications de demandes CP
# (séparés par des virgules si plusieurs : 'admin1@x.com, admin2@y.com')
ADMIN_NOTIFICATION_EMAIL = config('ADMIN_NOTIFICATION_EMAIL', default='')

# Configuration timeout pour éviter les erreurs de connexion
EMAIL_TIMEOUT = 30  # 30 secondes
EMAIL_SSL_CERTFILE = None
EMAIL_SSL_KEYFILE = None

# ========================================
# REST_FRAMEWORK
# ========================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

# SIMPLE_JWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'TOKEN_TYPE_CLAIM': 'token_type',
    'JTI_CLAIM': 'jti',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
}

# ========================================
# CORS - Configuration Production
# ========================================
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^http://localhost:\d+$",
    r"^http://127\.0\.0\.1:\d+$",
]
CORS_ALLOW_ALL_ORIGINS = True  # Temporairement activé pour développement
CSRF_TRUSTED_ORIGINS = [
    "https://resumecours.gestionhospitaliare.site",
]

CORS_ALLOWED_ORIGINS = [
    "https://resumecours.gestionhospitaliare.site",
    "https://www.resumecours.gestionhospitaliare.site",
    "http://localhost:60837",
    "http://localhost:60837",  # Port Flutter actuel
    "http://127.0.0.1:56766",  # Alternative localhost
    "http://localhost:3000",  # Ajout pour ton test
    "http://127.0.0.1:3000"   # Ajout pour ton test
]

# Ajouter les origines de développement si DEBUG est activé
if DEBUG:
    CORS_ALLOWED_ORIGINS += [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:59548",
        "http://localhost:60837",  # Port Flutter actuel
        "http://127.0.0.1:56766"   # Alternative localhost
    ]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

CORS_ALLOW_METHODS = ['DELETE', 'GET', 'OPTIONS', 'PATCH', 'POST', 'PUT']

CORS_EXPOSE_HEADERS = ['content-type', 'x-content-type-options', 'authorization']

# ========================================
# SÉCURITÉ PRODUCTION
# ========================================
if not DEBUG:
    # HTTPS obligatoire
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    # Cookies sécurisés
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # Headers de sécurité
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

    # HSTS
    SECURE_HSTS_SECONDS = 31536000  # 1 an
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Swagger settings
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
    }
}

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB pour les fichiers audio
DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB
# Permissions explicites pour les fichiers uploadés
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755

# Deepgram API Key
DEEPGRAM_API_KEY = config('DEEPGRAM_API_KEY', default='')

# DeepSeek API - Génération de résumés intelligents (Étape 2)
DEEPSEEK_API_KEY = config('DEEPSEEK_API_KEY', default='')


# Custom user roles
USER_ROLES = (
    ('student', 'Étudiant'),
    ('cp', 'Chef de Promo'),
    ('admin', 'Administrateur'),
)

# Logging en production - utilise la console (Apache capture les logs)
if not DEBUG:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '{levelname} {asctime} {module} {message}',
                'style': '{',
            },
        },
        'handlers': {
            'console': {
                'level': 'ERROR',
                'class': 'logging.StreamHandler',
                'formatter': 'verbose',
            },
        },
        'loggers': {
            'django': {
                'handlers': ['console'],
                'level': 'ERROR',
                'propagate': True,
            },
        },
    }

URL_CALLBACK = config('URL_CALLBACK', default=[
    'https://resumecours.gestionhospitaliare.site',  # Production
    'https://calls-declined-sector-relevance.trycloudflare.com', # Cloudflare Tunnel
    'http://localhost:8080',                         # Développement
    'http://127.0.0.1:8080',                         # Développement alternatif
])

CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://127.0.0.1:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 3600  # 60 minutes max par tâche (audio longue durée)
CELERY_TASK_SOFT_TIME_LIMIT = 3300  # Alerte à 55 minutes


# Celery Beat Schedule
CELERY_BEAT_SCHEDULE = {
    'cleanup-inactive-tokens': {
        'task': 'notifications.tasks.cleanup_inactive_tokens',
        'schedule': crontab(hour=2, minute=0),  # Tous les jours à 2h du matin
    },
    'check-subscription-expiring-soon': {
        'task': 'notifications.periodic_tasks.check_subscription_expiring_soon',
        'schedule': crontab(hour=9, minute=0),  # Tous les jours à 9h du matin
    },
    'check-subscription-expired': {
        'task': 'notifications.periodic_tasks.check_subscription_expired',
        'schedule': crontab(hour=10, minute=0),  # Tous les jours à 10h du matin
    },
}



# Keccel SMS API - Envoi d'OTP par SMS
KECCEL_SMS_TOKEN = config('KECCEL_SMS_TOKEN', default='')
SMS_URL = config('SMS_URL', default='https://sms.keccel.com/api/v2/sms')

FIREBASE_CREDENTIALS_PATH = config('FIREBASE_CREDENTIALS_PATH', default='')


import json  # noqa: E402
OTP_TEST_MODE = config('OTP_TEST_MODE', default=False, cast=bool)

def _parse_phone_list(value):
    """Parse OTP_TEST_PHONE_NUMBERS de manière tolérante :
    - JSON valide : ["+243990000000", "+243990000001"]
    - Liste simple guillemets : ['+243...', '+243...']
    - Séparée par virgules : +243990000000,+243990000001
    """
    if not value or not value.strip():
        return []
    v = value.strip()
    # 1) Essayer JSON strict
    try:
        parsed = json.loads(v)
        if isinstance(parsed, list):
            return [str(x).strip() for x in parsed if str(x).strip()]
        return [str(parsed).strip()] if str(parsed).strip() else []
    except json.JSONDecodeError:
        pass
    # 2) Essayer JSON avec guillemets simples
    try:
        parsed = json.loads(v.replace("'", '"'))
        if isinstance(parsed, list):
            return [str(x).strip() for x in parsed if str(x).strip()]
    except json.JSONDecodeError:
        pass
    # 3) Fallback : séparé par virgules
    return [x.strip() for x in v.split(',') if x.strip()]


OTP_TEST_PHONE_NUMBERS = config(
    'OTP_TEST_PHONE_NUMBERS',
    default='[]',
    cast=_parse_phone_list,
)


# ═══════════════════════════════════════════════════════════════════
# RATE LIMITING OTP (TACHES.md) — anti force-brute et abus SMS
# L'autorité est le BACKEND : ces limites s'appliquent avant l'envoi
# du SMS et avant toute vérification de code.
# ═══════════════════════════════════════════════════════════════════
# Niveau 2 — cooldown entre deux OTP pour un même numéro
OTP_COOLDOWN_SECONDS = 60
# Niveau 1 — maximum d'OTP envoyés par numéro sur la fenêtre
OTP_MAX_SENDS_PER_PHONE = 3
OTP_PHONE_WINDOW_SECONDS = 600  # 10 minutes
# Niveau 3 — maximum de requêtes par IP sur la fenêtre
OTP_MAX_REQUESTS_PER_IP = 100
OTP_IP_WINDOW_SECONDS = 600  # 10 minutes
# Niveau 4 — limite globale de chaque endpoint OTP (par seconde)
OTP_GLOBAL_MAX_PER_SECOND = 5
# Vérification OTP — codes incorrects avant blocage temporaire
OTP_MAX_VERIFY_ATTEMPTS = 5
OTP_VERIFY_BLOCK_SECONDS = 600  # 10 minutes

# Compteurs du rate limiting : Redis (même instance que Celery), avec
# fallback LocMem si Redis est indisponible → le service ne casse jamais.
# socket_connect_timeout court : si Redis tombe, chaque accès échoue en
# ~0,5 s au lieu de plusieurs secondes (sinon chaque requête OTP deviendrait
# très lente : 7 accès cache × timeout par défaut).
# ── CACHE CATALOGUE (tâche 60, axe 3) ────────────────────────────────────────
CACHE_REDIS_URL = config(
    'CACHE_REDIS_URL', default='redis://127.0.0.1:6379/1'
)
ENABLE_CATALOG_CACHE = config(
    'ENABLE_CATALOG_CACHE', default=False, cast=bool
)

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": CELERY_BROKER_URL,
        "TIMEOUT": None,  # chaque clé porte son propre TTL
        "OPTIONS": {
            "CONNECTION_POOL_KWARGS": {
                "socket_connect_timeout": 0.5,
            },
        },
    },
    "fallback": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "rate-limiting-fallback",
    },
    "catalog": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": CACHE_REDIS_URL,
        "TIMEOUT": 600,
        "KEY_PREFIX": "muhtasari",
        "OPTIONS": {
            "CONNECTION_POOL_KWARGS": {
                "socket_connect_timeout": 0.5,
            },
        },
    },
}

# =============================================
# FIREBASE / FCM CONFIGURATION
# =============================================
