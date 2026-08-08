"""
Django settings for resume_backend project.
"""

from pathlib import Path
from datetime import timedelta
from decouple import config
import os
from celery.schedules import crontab

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-your-secret-key-here')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

# ALLOWED_HOSTS - Domaines autorisés
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    'resumecours.gestionhospitaliare.site',  # Domaine de production
    'www.resumecours.gestionhospitaliare.site',  # Avec www si applicable
    'ftp.clavierplus.com',  # Domaine alternatif
    '180.149.197.29',  # IP serveur de production
]

if DEBUG:
    ALLOWED_HOSTS.append('*')  # Permet tous les hôtes en développement

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
    'courses',
    'payments',
    'security',
    'notifications',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Doit être le premier
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # 'users.middleware.JWTAuthenticationMiddleware',  # Notre middleware personnalisé JWT - TEMPORAIREMENT DÉSACTIVÉ
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'resume_backend.urls'

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

WSGI_APPLICATION = 'resume_backend.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
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
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Kinshasa'
USE_I18N = True
USE_TZ = True 

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    # 'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    # 'PAGE_SIZE': 20,
    # Temporarily disable default filter backends
    # 'DEFAULT_FILTER_BACKENDS': [
    #     'django_filters.rest_framework.DjangoFilterBackend',
    #     'rest_framework.filters.SearchFilter',
    #     'rest_framework.filters.OrderingFilter',
    # ],
}

# Simple JWT Configuration
SIMPLE_JWT = {
    # Durées de vie des tokens
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),  # Durée de vie du token d'accès (1 jour)
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),  # Durée de vie du refresh token (30 jours)
    'SLIDING_TOKEN_LIFETIME': timedelta(days=1),  # Durée de vie du token glissant
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=30),  # Durée de vie du rafraîchissement du token glissant
    
    # Configuration du rafraîchissement
    'ROTATE_REFRESH_TOKENS': True,  # Génère un nouveau refresh token à chaque rafraîchissement
    'BLACKLIST_AFTER_ROTATION': True,  # Met à la liste noire les anciens tokens après rotation
    'UPDATE_LAST_LOGIN': True,  # Met à jour le last_login de l'utilisateur
    
    # Période de grâce pour le rafraîchissement (1 heure)
    'SLIDING_TOKEN_REFRESH_LIFETIME_GRACE_PERIOD': timedelta(hours=1),
    
    # Configuration de sécurité
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer', 'JWT'),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    
    # Configuration des revendications (claims)
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'TOKEN_TYPE_CLAIM': 'token_type',
    'JTI_CLAIM': 'jti',
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    
    # Configuration des classes
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',
}

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:57585",  # Flutter web dev port
    "http://127.0.0.1:57585",
    "https://resumecours.gestionhospitaliare.site",  # Domaine de production
]

# En développement, on autorise toutes les origines pour faciliter les tests
CORS_ALLOW_ALL_ORIGINS = DEBUG

# En production, on restreint aux origines autorisées mais on permet les tests
if not DEBUG:
    CORS_ALLOWED_ORIGINS = [
        "https://resumecours.gestionhospitaliare.site",
        "https://www.resumecours.gestionhospitaliare.site",
        "http://localhost:8000",  # Pour les tests
        "http://127.0.0.1:8000",  # Pour les tests
        "http://localhost:8080",  # Flutter web
        "http://127.0.0.1:8080",  # Flutter web
    ]

# En-têtes autorisés
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-requested-with',
    'x-new-access-token',
    'x-new-refresh-token',
]

# En-têtes exposés au client
CORS_EXPOSE_HEADERS = [
    'x-new-access-token',
    'x-new-refresh-token',
]

# Méthodes HTTP autorisées
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# Autoriser les cookies d'authentification
CORS_ALLOW_CREDENTIALS = True

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
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# Custom user roles
USER_ROLES = (
    ('student', 'Étudiant'),
    ('cp', 'Chef de Promo'),
    ('admin', 'Administrateur'),
)

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'users': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'users.middleware': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# Configuration CORS
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = True  # En développement seulement, à restreindre en production
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost",
    "https://resumecours.gestionhospitaliare.site",
    "https://www.resumecours.gestionhospitaliare.site",
]

# En-têtes autorisés
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
    'access-control-allow-origin',
]

# Méthodes autorisées
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# Configuration des en-têtes exposés
CORS_EXPOSE_HEADERS = [
    'content-type',
    'x-content-type-options',
    'authorization',
]

# ========================================
# CONFIGURATION DES APIS EXTERNES
# ========================================

# Deepgram API - Transcription audio → texte (Étape 1)
DEEPGRAM_API_KEY = config('DEEPGRAM_API_KEY', default='')

# DeepSeek API - Génération de résumés intelligents (Étape 2)
DEEPSEEK_API_KEY = config('DEEPSEEK_API_KEY', default='')

# Keccel SMS API - Envoi d'OTP par SMS
KECCEL_SMS_TOKEN = config('KECCEL_SMS_TOKEN', default='')
SMS_URL = config('SMS_URL', default='https://sms.keccel.com/api/v2/sms')

# ═══════════════════════════════════════════════════════════════════
# MODE DE TEST GOOGLE PLAY (OTP fixe sans SMS)
# ═══════════════════════════════════════════════════════════════════
# OTP_TEST_MODE = True → les numéros listés dans OTP_TEST_PHONE_NUMBERS :
#   • ne reçoivent PAS de SMS (le code est affiché dans les logs/console)
#   • peuvent se connecter avec le code OTP fixe "1234"
# Le flux API et frontend reste IDENTIQUE à un utilisateur normal.
# Désactiver : OTP_TEST_MODE=False (ou liste vide) → tous les numéros
# utilisent le système OTP réel. Aucun impact sur les utilisateurs réels.
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

# ========================================
# CONFIGURATION EMAIL (Gmail SMTP)
# ========================================
# En production, utiliser SMTP backend pour envoyer les emails réellement
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
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

# Pour le développement local, afficher les emails dans la console
if DEBUG and not config('FORCE_EMAIL_SMTP', default=False, cast=bool):
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    print('[EMAIL] Backend: Console - Les emails seront affichés dans la console')

# URL du frontend pour les liens de réinitialisation
FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:3000')

# ========================================
# CONFIGURATION PAYMENT CALLBACKS
# ========================================

# URL de callback pour FlexPay (paiements mobiles)
URL_CALLBACK = config('URL_CALLBACK', default=[
    'https://calls-declined-sector-relevance.trycloudflare.com', # Cloudflare Tunnel
    'https://resumecours.gestionhospitaliare.site',  # Production
    'http://localhost:8080',                         # Développement
    'http://127.0.0.1:8080',                         # Développement alternatif
])

# URL de base pour les callbacks (utilisée si URL_CALLBACK n'est pas défini)
if not hasattr(URL_CALLBACK, '__iter__') or len(URL_CALLBACK) == 0:
    URL_CALLBACK = ['https://calls-declined-sector-relevance.trycloudflare.com']
    #URL_CALLBACK = ['http://localhost:8080']

# =============================================
# CELERY CONFIGURATION
# =============================================
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://127.0.0.1:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 3600  # 60 minutes max par tâche (audio longue durée)
CELERY_TASK_SOFT_TIME_LIMIT = 3300  # Alerte à 55 minutes

# =============================================
# FIREBASE / FCM CONFIGURATION
# =============================================
FIREBASE_CREDENTIALS_PATH = config('FIREBASE_CREDENTIALS_PATH', default='')
