"""
Settings pour les tests — exécute les tâches Celery en mode EAGER
(synchrones, sans broker Redis) pour que les tests fonctionnent
sur n'importe quelle machine.

Usage : python manage.py test --settings=resume_backend.settings_test
"""
from .settings import *  # noqa: F401,F403

# Exécuter les tâches Celery immédiatement (synchrones) pendant les tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Tâche 71 : les tests utilisent toujours l'environnement Sandbox, quel que
# soit APPLE_ENVIRONMENT défini dans le .env local/production.
APPLE_ENVIRONMENT = 'Sandbox'
APPLE_ALLOWED_ENVIRONMENTS = 'Sandbox'
