#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')
django.setup()

from payments.models import Service, Abonnement
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

def create_test_services():
    """Créer des services de test"""
    
    # Service Premium
    service_premium, created = Service.objects.get_or_create(
        nom="Premium",
        defaults={
            'description': "Accès illimité à tous les résumés, téléchargement PDF, support prioritaire",
            'type': 'premium',
            'price': 2500.00,
            'currency': 'CDF',
            'duree_mois': 1,
            'features': [
                "Accès illimité aux résumés",
                "Téléchargement PDF",
                "Support prioritaire",
                "Pas de publicité"
            ],
            'is_active': True
        }
    )
    
    # Service VIP
    service_vip, created = Service.objects.get_or_create(
        nom="VIP",
        defaults={
            'description': "Tous les avantages Premium + accès anticipé aux nouveaux contenus",
            'type': 'vip',
            'price': 5000.00,
            'currency': 'CDF',
            'duree_mois': 1,
            'features': [
                "Tous les avantages Premium",
                "Accès anticipé aux nouveaux résumés",
                "Consultation hors ligne",
                "Badge VIP",
                "Support 24/7"
            ],
            'is_active': True
        }
    )
    
    # Service Basic
    service_basic, created = Service.objects.get_or_create(
        nom="Basic",
        defaults={
            'description': "Accès limité aux résumés gratuits avec publicités",
            'type': 'basic',
            'price': 0.00,
            'currency': 'CDF',
            'duree_mois': 12,
            'features': [
                "Accès aux résumés gratuits",
                "3 téléchargements par mois",
                "Support communautaire"
            ],
            'is_active': True
        }
    )
    
    print(f"Services crees:")
    print(f"   - {service_premium.nom}: {service_premium.price} {service_premium.currency}")
    print(f"   - {service_vip.nom}: {service_vip.price} {service_vip.currency}")
    print(f"   - {service_basic.nom}: {service_basic.price} {service_basic.currency}")
    
    # Créer un abonnement de test si un utilisateur existe
    try:
        user = User.objects.first()
        if user:
            abonnement, created = Abonnement.objects.get_or_create(
                user=user,
                service=service_basic,
                defaults={
                    'date_debut': timezone.now(),
                    'date_fin': timezone.now() + timedelta(days=365),
                    'status': 'active',
                    'progress': 25
                }
            )
            if created:
                print(f"Abonnement de test cree pour {user.username}")
    except Exception as e:
        print(f"Pas d'utilisateur trouve pour creer un abonnement de test")

if __name__ == '__main__':
    create_test_services()
    print("Donnees de test creees avec succes!")
