"""
Configuration spécifique pour la production
"""
from .settings import *
import os

# SÉCURITÉ EN PRODUCTION
DEBUG = False
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-production-secret-key-here')

# Domaines autorisés en production
ALLOWED_HOSTS = [
    'resumecours.gestionhospitaliare.site',
    'www.resumecours.gestionhospitaliare.site',
    'api.resumecours.gestionhospitaliare.site',  # Si vous avez un sous-domaine API
]

# Base de données de production (PostgreSQL recommandé)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'resume_plus_db'),
        'USER': os.environ.get('DB_USER', 'resume_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'your_db_password'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# Configuration CORS pour la production
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "https://resumecours.gestionhospitaliare.site",
    "https://www.resumecours.gestionhospitaliare.site",
]

# Configuration des fichiers statiques pour la production
STATIC_URL = '/static/'
STATIC_ROOT = '/var/www/resume_plus/static/'

# Configuration des fichiers média
MEDIA_URL = '/media/'
MEDIA_ROOT = '/var/www/resume_plus/media/'

# Configuration de sécurité renforcée
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 an
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Si vous utilisez HTTPS (recommandé)
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Configuration des logs pour la production
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/resume_plus/django.log',
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/resume_plus/django_error.log',
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'error_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'users': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'courses': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Configuration email pour la production (optionnel)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@resumecours.gestionhospitaliare.site')