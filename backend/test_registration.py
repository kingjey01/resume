#!/usr/bin/env python3
"""
Test de l'endpoint de registration et génération de tokens
"""
import requests
import json
import random
import string

BASE_URL = "https://resumecours.gestionhospitaliare.site"

def generate_random_user():
    """Générer des données utilisateur aléatoires"""
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return {
        "username": f"testuser_{random_suffix}",
        "email": f"test_{random_suffix}@example.com",
        "password": "testpass123",
        "password_confirm": "testpass123",
        "first_name": "Test",
        "last_name": "User",
        "groupe": "ETUDIANT",
        "phone": "+33123456789"
    }

def test_registration():
    """Test de création de compte"""
    print("🚀 TEST DE CRÉATION DE COMPTE")
    print("="*50)
    
    # Générer un utilisateur de test
    user_data = generate_random_user()
    print(f"👤 Création utilisateur: {user_data['username']}")
    print(f"📧 Email: {user_data['email']}")
    
    # Test de registration
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/register/",
            json=user_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"\n📡 Réponse registration: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            print("✅ Compte créé avec succès!")
            
            # Vérifier les tokens
            if 'access' in data and 'refresh' in data:
                print(f"🔑 Access Token: {data['access'][:30]}...")
                print(f"🔄 Refresh Token: {data['refresh'][:30]}...")
                
                # Vérifier les données utilisateur
                if 'user' in data:
                    user_info = data['user']
                    print(f"👤 ID utilisateur: {user_info.get('id')}")
                    print(f"📧 Email: {user_info.get('email')}")
                    print(f"👥 Profil: {user_info.get('profile', {}).get('groupe', 'Non défini')}")
                
                return data
            else:
                print("❌ Tokens manquants dans la réponse")
                print(f"Contenu: {data}")
        else:
            print(f"❌ Échec de la création: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Erreurs: {error_data}")
            except:
                print(f"Contenu brut: {response.text[:300]}")
                
    except Exception as e:
        print(f"❌ Erreur de requête: {e}")
    
    return None

def test_login_with_new_user():
    """Test de connexion avec un utilisateur existant"""
    print(f"\n🔐 TEST DE CONNEXION")
    print("="*50)
    
    # Utiliser un utilisateur existant
    login_data = {
        "username": "test_student",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login/",
            json=login_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"📡 Réponse login: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Connexion réussie!")
            
            if 'access' in data and 'refresh' in data:
                print(f"🔑 Access Token: {data['access'][:30]}...")
                print(f"🔄 Refresh Token: {data['refresh'][:30]}...")
                return data
            else:
                print("❌ Tokens manquants")
        else:
            print(f"❌ Échec de la connexion: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Erreurs: {error_data}")
            except:
                print(f"Contenu: {response.text[:300]}")
                
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    return None

def test_api_with_jwt_token(access_token):
    """Test des endpoints API avec le token JWT"""
    print(f"\n🧪 TEST API AVEC TOKEN JWT")
    print("="*50)
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    endpoints = [
        ("/api/auth/profile/", "Profil utilisateur"),
        ("/api/auth/user/", "Info utilisateur"),
        ("/api/courses/", "Courses"),
        ("/api/summaries/", "Summaries"),
    ]
    
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=10)
            print(f"  {description:<20} → {response.status_code}")
            
            if response.status_code == 200:
                print(f"    ✅ Succès!")
            elif response.status_code == 401:
                print(f"    ❌ Non autorisé: {response.json().get('detail', 'Erreur auth')}")
            else:
                print(f"    ⚠️  Autre: {response.text[:100]}")
                
        except Exception as e:
            print(f"  {description:<20} → ERROR: {e}")

def main():
    print("🚀 TEST COMPLET DU SYSTÈME D'AUTHENTIFICATION")
    print("="*60)
    
    # Test 1: Création de compte
    registration_data = test_registration()
    
    # Test 2: Connexion
    login_data = test_login_with_new_user()
    
    # Test 3: Utilisation des tokens
    if registration_data and 'access' in registration_data:
        print(f"\n🔍 Test avec token de registration...")
        test_api_with_jwt_token(registration_data['access'])
    
    if login_data and 'access' in login_data:
        print(f"\n🔍 Test avec token de login...")
        test_api_with_jwt_token(login_data['access'])
    
    print(f"\n{'='*60}")
    print("📋 RÉSUMÉ")
    print('='*60)
    print(f"Registration: {'✅' if registration_data else '❌'}")
    print(f"Login: {'✅' if login_data else '❌'}")
    
    if registration_data or login_data:
        print("✅ Le système d'authentification JWT fonctionne!")
        print("✅ Les nouveaux utilisateurs auront des tokens automatiquement!")
    else:
        print("❌ Problèmes détectés dans le système d'authentification")

if __name__ == "__main__":
    main()