"""
Configuration Celery pour Resume+
Permet l'exécution de tâches asynchrones (transcription + résumé IA)
"""
import os
from celery import Celery

# Définir le module de settings Django par défaut
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')

app = Celery('resume_backend')

# Charger la configuration depuis les settings Django (préfixe CELERY_)
app.config_from_object('django.conf:settings', namespace='CELERY')

# Découvrir automatiquement les tâches dans les apps Django
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
