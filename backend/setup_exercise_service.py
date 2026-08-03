#!/usr/bin/env python
"""
Script pour configurer le service d'exercices et suspendre les autres services
"""
import os
import sys
import django

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')
django.setup()

from courses.models import Service
from django.db import transaction

def setup_exercise_service():
    """Configure le service d'exercices et suspend les autres"""
    try:
        with transaction.atomic():
            # Suspendre tous les services existants
            Service.objects.all().update(is_active=False)
            print("[OK] Tous les services existants ont été suspendus")
            
            # Créer ou mettre à jour le service d'exercices
            exercise_service, created = Service.objects.get_or_create(
                nom="Exercices",
                defaults={
                    'description': "Accès aux exercices QCM générés par IA basés sur les résumés de cours",
                    'prix': 5.00,  # Prix en USD
                    'is_active': True
                }
            )
            
            if created:
                print("[OK] Service 'Exercices' créé avec succès")
            else:
                # Réactiver le service d'exercices s'il existait déjà
                exercise_service.is_active = True
                exercise_service.save()
                print("[OK] Service 'Exercices' réactivé")
            
            print(f"[INFO] Service d'exercices configuré:")
            print(f"   - Nom: {exercise_service.nom}")
            print(f"   - Prix: {exercise_service.prix} USD")
            print(f"   - Description: {exercise_service.description}")
            print(f"   - Actif: {exercise_service.is_active}")
            
            # Afficher les services suspendus
            suspended_services = Service.objects.filter(is_active=False)
            if suspended_services.exists():
                print(f"\n[PAUSE] Services suspendus ({suspended_services.count()}):")
                for service in suspended_services:
                    print(f"   - {service.nom}")
            
            return exercise_service
            
    except Exception as e:
        print(f"[ERROR] Erreur lors de la configuration: {str(e)}")
        return None

if __name__ == "__main__":
    print("[START] Configuration du service d'exercices...")
    service = setup_exercise_service()
    if service:
        print("\n[SUCCESS] Configuration terminée avec succès!")
    else:
        print("\n[FAILED] Échec de la configuration")
