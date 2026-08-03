#!/usr/bin/env python
"""
Script pour corriger les données avant migration
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')
django.setup()

from courses.models import Universite, Promotion, Filiere
from users.models import UserProfile

def create_initial_data():
    """Créer des données initiales pour les nouvelles tables"""
    
    # Créer quelques universités
    universites = [
        {'nom': 'Université de Yaoundé I', 'adresse': 'Yaoundé, Cameroun'},
        {'nom': 'Université de Douala', 'adresse': 'Douala, Cameroun'},
        {'nom': 'Université de Dschang', 'adresse': 'Dschang, Cameroun'},
    ]
    
    for univ_data in universites:
        Universite.objects.get_or_create(nom=univ_data['nom'], defaults=univ_data)
    
    # Créer les promotions
    promotions = [
        {'nom': 'L1', 'annee': 2024},
        {'nom': 'L2', 'annee': 2024},
        {'nom': 'L3', 'annee': 2024},
        {'nom': 'M1', 'annee': 2024},
        {'nom': 'M2', 'annee': 2024},
    ]
    
    for promo_data in promotions:
        Promotion.objects.get_or_create(nom=promo_data['nom'], defaults=promo_data)
    
    # Créer les filières
    filieres = [
        {'nom': 'Informatique', 'description': 'Sciences informatiques et technologies'},
        {'nom': 'Mathématiques', 'description': 'Mathématiques appliquées'},
        {'nom': 'Physique', 'description': 'Sciences physiques'},
        {'nom': 'Chimie', 'description': 'Sciences chimiques'},
        {'nom': 'Biologie', 'description': 'Sciences biologiques'},
    ]
    
    for filiere_data in filieres:
        Filiere.objects.get_or_create(nom=filiere_data['nom'], defaults=filiere_data)
    
    print("Données initiales créées avec succès!")

def clear_user_profiles():
    """Vider les champs problématiques des UserProfile"""
    profiles = UserProfile.objects.all()
    for profile in profiles:
        profile.filiere = None
        profile.save()
    print(f"Nettoyé {profiles.count()} profils utilisateur")

if __name__ == '__main__':
    print("Création des données initiales...")
    create_initial_data()
    print("Nettoyage des profils utilisateur...")
    clear_user_profiles()
    print("Terminé!")
