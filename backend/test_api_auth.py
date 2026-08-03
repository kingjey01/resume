#!/usr/bin/env python3
"""
🔧 SCRIPT DE TEST DE L'API ET AUTHENTIFICATION
==============================================

Ce script teste les endpoints de l'API pour diagnostiquer les problèmes d'authentification.

Usage:
    cd backend
    python test_api_auth.py
"""

import requests
import json
import os
import sys

# Configuration
BASE_URL = "http://127.0.0.1:8000"  # Changez selon votre configuration
API_BASE = f"{BASE_URL}/api"

def print_header(title):
    """Affiche un en-tête formaté"""
    print("\n" + "=" * 60)
    print(f"🔧 {title}")
    print("=" * 60)

def print_section(title):
    """Affiche une section formatée"""
    print(f"\n📋 {title}")
    print("-" * 40)

def test_server_status():
    """Teste si le serveur Django est accessible"""
    print_section("Test de connectivité du serveur")
    
    try:
        response = requests.get(f"{BASE_URL}/admin/", timeout=5)
        if response.status_code in [200, 302]:
            print("✅ Serveur Django accessible")
            return True
        else:
            print(f"⚠️  Serveur répond avec le code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter au serveur Django")
        print(f"   Vérifiez que le serveur tourne sur {BASE_URL}")
        return False
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False

def test_login():
    """Teste la connexion avec les comptes de test"""
    print_section("Test de connexion")
    
    # Comptes de test à essayer
    test_accounts = [
        {"email": "admin@resumeplus.cd", "password": "AdminResume2024!"},
        {"email": "cp.info@unikin.cd", "password": "CPInfo2024!"},
        {"email": "etudiant1@gmail.com", "password": "Etudiant2024!"},
    ]
    
    for account in test_accounts:
        print(f"\n🔐 Test de connexion: {account['email']}")
        
        try:
            response = requests.post(
                f"{API_BASE}/auth/login/",
                json=account,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if 'access' in data:
                    print("   ✅ Connexion réussie")
                    print(f"   Token: {data['access'][:20]}...")
                    return data['access']  # Retourner le token pour les tests suivants
                else:
                    print("   ⚠️  Connexion réussie mais pas de token")
            else:
                print(f"   ❌ Échec de connexion: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Erreur lors de la connexion: {e}")
    
    return None

def test_authenticated_endpoints(token):
    """Teste les endpoints qui nécessitent une authentification"""
    print_section("Test des endpoints authentifiés")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Endpoints à tester
    endpoints = [
        {"url": "/auth/user/", "method": "GET", "name": "Infos utilisateur"},
        {"url": "/auth/profile/", "method": "GET", "name": "Profil utilisateur"},
        {"url": "/summaries/", "method": "GET", "name": "Liste des résumés"},
        {"url": "/purchases/", "method": "GET", "name": "Liste des achats"},
        {"url": "/services/", "method": "GET", "name": "Liste des services"},
    ]
    
    for endpoint in endpoints:
        print(f"\n📡 Test: {endpoint['name']} ({endpoint['method']} {endpoint['url']})")
        
        try:
            if endpoint['method'] == 'GET':
                response = requests.get(
                    f"{API_BASE}{endpoint['url']}",
                    headers=headers,
                    timeout=10
                )
            else:
                response = requests.post(
                    f"{API_BASE}{endpoint['url']}",
                    headers=headers,
                    timeout=10
                )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ Succès")
                try:
                    data = response.json()
                    if isinstance(data, list):
                        print(f"   📊 {len(data)} éléments retournés")
                    elif isinstance(data, dict):
                        print(f"   📊 Objet retourné avec {len(data)} champs")
                except:
                    print("   📊 Réponse non-JSON")
            elif response.status_code == 401:
                print("   ❌ Non autorisé (problème d'authentification)")
            elif response.status_code == 403:
                print("   ❌ Interdit (problème de permissions)")
            elif response.status_code == 404:
                print("   ❌ Endpoint non trouvé")
            else:
                print(f"   ⚠️  Code inattendu: {response.text[:100]}")
                
        except Exception as e:
            print(f"   ❌ Erreur: {e}")

def test_cors():
    """Teste la configuration CORS"""
    print_section("Test de la configuration CORS")
    
    try:
        # Test d'une requête OPTIONS (preflight CORS)
        response = requests.options(
            f"{API_BASE}/auth/login/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type, Authorization"
            },
            timeout=5
        )
        
        print(f"Status OPTIONS: {response.status_code}")
        
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
        }
        
        print("En-têtes CORS:")
        for header, value in cors_headers.items():
            if value:
                print(f"   ✅ {header}: {value}")
            else:
                print(f"   ❌ {header}: Non défini")
                
    except Exception as e:
        print(f"❌ Erreur lors du test CORS: {e}")

def main():
    """Fonction principale"""
    print_header("TEST DE L'API RESUME+")
    
    # 1. Test de connectivité
    if not test_server_status():
        print("\n❌ Impossible de continuer sans serveur accessible")
        return
    
    # 2. Test CORS
    test_cors()
    
    # 3. Test de connexion
    token = test_login()
    
    if not token:
        print("\n❌ Impossible de continuer sans token d'authentification")
        print("\n💡 Suggestions:")
        print("   • Vérifiez que la base de données contient des utilisateurs de test")
        print("   • Exécutez le script seed: python run_seed.py")
        print("   • Vérifiez les logs Django pour plus de détails")
        return
    
    # 4. Test des endpoints authentifiés
    test_authenticated_endpoints(token)
    
    print_header("RÉSUMÉ DES TESTS")
    print("\n✅ Tests terminés!")
    print("\n💡 Si des erreurs persistent:")
    print("   • Vérifiez les logs Django (python manage.py runserver)")
    print("   • Vérifiez la configuration CORS dans settings.py")
    print("   • Assurez-vous que les migrations sont appliquées")
    print("   • Vérifiez que les données de test existent")

if __name__ == "__main__":
    main()