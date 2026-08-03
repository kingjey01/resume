# Charger Celery au démarrage de Django (optionnel - ne bloque pas si Celery non installé)
from .celery import app as celery_app

__all__ = ('celery_app',)
