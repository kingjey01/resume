#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import django
import requests
import json
from datetime import datetime, timedelta

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth.models import User
from payments.models import Service, Abonnement
from django.utils import timezone

# Configuration API
BASE_URL = 'http://127.0.0.1:8000/api'
LOGIN_URL = f'{BASE_URL}/auth/login/'
SERVICES_URL = f'{BASE_URL}/services/'
ABONNEMENTS_URL = f'{BASE_URL}/abonnements/'

def test_consecutive_subscriptions():
    """Test de l'algorithme d'abonnements consécutifs"""
    
    print("=== TEST ALGORITHME ABONNEMENTS CONSECUTIFS ===\n")
    
    # 1. Login pour obtenir le token
    print("1. Connexion utilisateur...")
    login_data = {
        'email': 'jey@example.com',
        'password': 'password123'
    }
    
    response = requests.post(LOGIN_URL, json=login_data)
    if response.status_code != 200:
        print(f"ERREUR Erreur de connexion: {response.status_code}")
        print(response.text)
        return
    
    token = response.json()['access']
    headers = {'Authorization': f'Bearer {token}'}
    print("OK Connexion reussie")
    
    # 2. Récupérer les services disponibles
    print("\n2. Récupération des services...")
    response = requests.get(SERVICES_URL, headers=headers)
    if response.status_code != 200:
        print(f"ERREUR recuperation services: {response.status_code}")
        return
    
    services = response.json()
    print(f"OK {len(services)} services trouves")
    
    # Choisir le service Premium pour le test
    premium_service = None
    for service in services:
        if service['nom'] == 'Premium':
            premium_service = service
            break
    
    if not premium_service:
        print("ERREUR Service Premium non trouve")
        return
    
    print(f"INFO Service selectionne: {premium_service['nom']} - {premium_service['price']} CDF")
    
    # 3. Vérifier les abonnements actuels
    print("\n3. Vérification des abonnements actuels...")
    response = requests.get(ABONNEMENTS_URL, headers=headers)
    if response.status_code == 200:
        current_subs = response.json()
        print(f"INFO Abonnements actuels: {len(current_subs)}")
        
        # Afficher les abonnements actifs pour le service Premium
        active_premium_subs = [
            sub for sub in current_subs 
            if sub['service'] == premium_service['id'] and sub['status'] == 'active'
        ]
        
        if active_premium_subs:
            for sub in active_premium_subs:
                print(f"INFO Abonnement actif trouve:")
                print(f"   - Début: {sub['date_debut']}")
                print(f"   - Fin: {sub['date_fin']}")
                print(f"   - Status: {sub['status']}")
    
    # 4. Créer un premier abonnement
    print("\n4. Création du premier abonnement Premium...")
    subscription_data = {
        'service': premium_service['id'],
        'date_debut': timezone.now().isoformat()
    }
    
    response = requests.post(ABONNEMENTS_URL, json=subscription_data, headers=headers)
    if response.status_code != 201:
        print(f"ERREUR creation abonnement: {response.status_code}")
        print(response.text)
        return
    
    first_sub = response.json()
    print("OK Premier abonnement cree:")
    print(f"   - ID: {first_sub['id']}")
    print(f"   - Début: {first_sub['date_debut']}")
    print(f"   - Fin: {first_sub['date_fin']}")
    print(f"   - Status: {first_sub['status']}")
    
    # 5. Créer un deuxième abonnement (devrait être consécutif)
    print("\n5. Création du deuxième abonnement Premium (test consécutif)...")
    
    response = requests.post(ABONNEMENTS_URL, json=subscription_data, headers=headers)
    if response.status_code != 201:
        print(f"ERREUR creation deuxieme abonnement: {response.status_code}")
        print(response.text)
        return
    
    second_sub = response.json()
    print("OK Deuxieme abonnement cree:")
    print(f"   - ID: {second_sub['id']}")
    print(f"   - Début: {second_sub['date_debut']}")
    print(f"   - Fin: {second_sub['date_fin']}")
    print(f"   - Status: {second_sub['status']}")
    
    # 6. Vérification de l'algorithme
    print("\n6. Vérification de l'algorithme consécutif...")
    
    # Convertir les dates pour comparaison
    first_end = datetime.fromisoformat(first_sub['date_fin'].replace('Z', '+00:00'))
    second_start = datetime.fromisoformat(second_sub['date_debut'].replace('Z', '+00:00'))
    
    if abs((second_start - first_end).total_seconds()) < 60:  # Tolérance de 1 minute
        print("OK ALGORITHME CORRECT: Le deuxieme abonnement commence a la fin du premier")
        print(f"   - Fin du 1er: {first_sub['date_fin']}")
        print(f"   - Début du 2e: {second_sub['date_debut']}")
        
        if second_sub['status'] == 'pending':
            print("OK Status correct: 'pending' car commence dans le futur")
        else:
            print("WARN Status inattendu: devrait etre 'pending'")
    else:
        print("ERREUR ALGORITHME INCORRECT: Les dates ne sont pas consecutives")
        print(f"   - Écart: {(second_start - first_end).total_seconds()} secondes")
    
    # 7. Afficher tous les abonnements finaux
    print("\n7. État final des abonnements...")
    response = requests.get(ABONNEMENTS_URL, headers=headers)
    if response.status_code == 200:
        final_subs = response.json()
        premium_subs = [sub for sub in final_subs if sub['service'] == premium_service['id']]
        
        print(f"INFO Total abonnements Premium: {len(premium_subs)}")
        for i, sub in enumerate(premium_subs, 1):
            print(f"   {i}. ID {sub['id']} - {sub['status']} - {sub['date_debut']} -> {sub['date_fin']}")
    
    print("\n=== FIN DU TEST ===")

if __name__ == '__main__':
    test_consecutive_subscriptions()
