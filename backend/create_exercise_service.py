"""Script pour créer le service Exercices QCM"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')
django.setup()

from payments.models import Service

svc, created = Service.objects.get_or_create(
    nom='Exercices QCM',
    defaults={
        'description': 'Acces illimite aux exercices QCM generes par IA',
        'type': 'premium',
        'price': 2500,
        'currency': 'CDF',
        'duree_mois': 1,
        'features': ['QCM generes par IA', 'Acces illimite', 'Suivi de performance', 'Explications detaillees'],
        'is_active': True,
    }
)

status = 'cree' if created else 'existant'
print(f'Service {status}: {svc.id} - {svc.nom} ({svc.price} {svc.currency})')
