"""
Script de seed pour le déploiement avec les nouveaux modèles FlexPay
À exécuter après les migrations : python manage.py seed_production
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from decimal import Decimal
from django.contrib.auth.models import User
from courses.models import Promotion, Filiere, Universite, UniversiteFiliere
from payments.models import Service


def seed_promotions():
    """Créer les promotions académiques"""
    promotions_data = [
        {'nom': 'L1', 'annee': 1},
        {'nom': 'L2', 'annee': 2},
        {'nom': 'L3', 'annee': 3},
        {'nom': 'M1', 'annee': 4},
        {'nom': 'M2', 'annee': 5},
    ]
    
    for data in promotions_data:
        Promotion.objects.get_or_create(nom=data['nom'], defaults={'annee': data['annee']})
    
    print(f"✅ {len(promotions_data)} promotions créées")


def seed_filieres():
    """Créer les filières académiques courantes"""
    filieres_data = [
        {'nom': 'Médecine', 'description': 'Faculté de Médecine'},
        {'nom': 'Pharmacie', 'description': 'Faculté de Pharmacie'},
        {'nom': 'Droit', 'description': 'Faculté de Droit'},
        {'nom': 'Sciences Économiques', 'description': 'Faculté des Sciences Économiques'},
        {'nom': 'Informatique', 'description': 'Département d\'Informatique'},
        {'nom': 'Génie Civil', 'description': 'Département de Génie Civil'},
        {'nom': 'Biologie', 'description': 'Département de Biologie'},
        {'nom': 'Chimie', 'description': 'Département de Chimie'},
    ]
    
    for data in filieres_data:
        Filiere.objects.get_or_create(nom=data['nom'], defaults={'description': data['description']})
    
    print(f"✅ {len(filieres_data)} filières créées")


def seed_universites():
    """Créer les universités"""
    universites_data = [
        {'nom': 'Université de Kinshasa', 'adresse': 'Kinshasa, RDC'},
        {'nom': 'Université de Lubumbashi', 'adresse': 'Lubumbashi, RDC'},
        {'nom': 'Université de Kisangani', 'adresse': 'Kisangani, RDC'},
        {'nom': 'Université Protestante au Congo', 'adresse': 'Kinshasa, RDC'},
    ]
    
    for data in universites_data:
        Universite.objects.get_or_create(nom=data['nom'], defaults={'adresse': data['adresse']})
    
    print(f"✅ {len(universites_data)} universités créées")


def seed_services_abonnement():
    """Créer les services d'abonnement pour FlexPay"""
    services_data = [
        {
            'nom': 'Abonnement Basic',
            'description': 'Accès à 5 résumés par mois',
            'type': 'basic',
            'price': Decimal('5000.00'),
            'currency': 'CDF',
            'duree_mois': 1,
            'features': [
                '5 résumés par mois',
                'Support email',
                'Accès aux résumés gratuits'
            ]
        },
        {
            'nom': 'Abonnement Premium',
            'description': 'Accès illimité à tous les résumés',
            'type': 'premium',
            'price': Decimal('15000.00'),
            'currency': 'CDF',
            'duree_mois': 1,
            'features': [
                'Résumés illimités',
                'Support prioritaire',
                'Accès aux PDF',
                'Lecture audio'
            ]
        },
        {
            'nom': 'Abonnement VIP',
            'description': 'Accès illimité + fonctionnalités premium',
            'type': 'vip',
            'price': Decimal('35000.00'),
            'currency': 'CDF',
            'duree_mois': 3,
            'features': [
                'Résumés illimités',
                'Support 24/7',
                'Accès aux PDF',
                'Lecture audio',
                'Téléchargement hors ligne',
                'Partage avec amis'
            ]
        },
    ]
    
    for data in services_data:
        Service.objects.get_or_create(
            nom=data['nom'],
            defaults={
                'description': data['description'],
                'type': data['type'],
                'price': data['price'],
                'currency': data['currency'],
                'duree_mois': data['duree_mois'],
                'features': data['features'],
                'is_active': True
            }
        )
    
    print(f"✅ {len(services_data)} services d'abonnement créés")


def create_admin_user():
    """Créer l'utilisateur admin si inexistant"""
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@resumecours.cd',
            password='admin123'  # À changer en production !
        )
        print("✅ Utilisateur admin créé (login: admin / password: admin123)")
    else:
        print("ℹ️ Utilisateur admin existe déjà")


def main():
    """Fonction principale de seeding"""
    print("🌱 Démarrage du seed pour la production...\n")
    
    try:
        seed_promotions()
        seed_filieres()
        seed_universites()
        seed_services_abonnement()
        create_admin_user()
        
        print("\n✅ Seed terminé avec succès !")
        print("\n📋 Récapitulatif des données créées:")
        print(f"   - {Promotion.objects.count()} promotions")
        print(f"   - {Filiere.objects.count()} filières")
        print(f"   - {Universite.objects.count()} universités")
        print(f"   - {Service.objects.count()} services d'abonnement")
        
    except Exception as e:
        print(f"\n❌ Erreur lors du seed : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
