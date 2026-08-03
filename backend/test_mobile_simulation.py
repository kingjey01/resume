#!/usr/bin/env python3
"""
📱 SIMULATION DE L'APP MOBILE POUR TESTER L'AUTHENTIFICATION
===========================================================

Ce script simule le comportement de l'app mobile Flutter.
"""

import requests
import json
import time

# Configuration
BASE_URL = "https://resumecours.gestionhospitaliare.site/api"

def print_header(title):
    print("\n" + "=" * 50)
    print(f"📱 {title}")
    print("=" * 50)

def print_step(step, description):
    print(f"\n🔸 Étape {step}: {description}")
    print("-" * 30)

def login_user(username, password):
    """Simule la connexion de l'utilisateur"""
    print_step(1, "Connexion utilisateur")
    
    login_data = {
        "username": username,
        "password": password
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login/",
            json=login_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Connexion réussie!")
            print(f"👤 Utilisateur: {data['user']['username']}")
            print(f"📧 Email: {data['user']['email']}")
            print(f"🎓 Groupe: {data['user']['profile']['groupe']}")
            print(f"🔑 Token: {data['access'][:30]}...")
            return data['access']
        else:
            print(f"❌ Échec de connexion: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return None

def test_user_info(token):
    """Teste l'endpoint /api/auth/user/"""
    print_step(2, "Test des informations utilisateur")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            f"{BASE_URL}/auth/user/",
            headers=headers,
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Informations utilisateur récupérées!")
            print(f"👤 ID: {data['id']}")
            print(f"👤 Username: {data['username']}")
            print(f"📧 Email: {data['email']}")
            return True
        else:
            print(f"❌ Échec: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_summaries(token):
    """Teste l'endpoint /api/summaries/"""
    print_step(3, "Test des résumés")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            f"{BASE_URL}/summaries/",
            headers=headers,
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Résumés récupérés: {len(data)} éléments")
            
            if data:
                print("📚 Premier résumé:")
                first_summary = data[0]
                print(f"   Titre: {first_summary.get('titre', 'N/A')}")
                print(f"   Cours: {first_summary.get('course', 'N/A')}")
                print(f"   Prix: {first_summary.get('prix', 'N/A')}")
            else:
                print("📚 Aucun résumé disponible")
            return True
        else:
            print(f"❌ Échec: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def main():
    """Fonction principale - Simule le parcours complet de l'app mobile"""
    print_header("SIMULATION APP MOBILE RESUME+")
    
    # Données de test
    username = "ANNE"
    password = "1234azer"
    
    print(f"🎯 Test avec l'utilisateur: {username}")
    
    # 1. Connexion
    token = login_user(username, password)
    
    if not token:
        print("\n❌ Impossible de continuer sans token")
        return
    
    # Attendre un peu (comme le ferait l'app)
    time.sleep(1)
    
    # 2. Test des endpoints
    results = {
        'user_info': test_user_info(token),
        'summaries': test_summaries(token)
    }
    
    # 3. Résumé des résultats
    print_header("RÉSUMÉ DES TESTS")
    
    success_count = sum(results.values())
    total_tests = len(results)
    
    print(f"\n📊 Résultats: {success_count}/{total_tests} tests réussis")
    
    for endpoint, success in results.items():
        status = "✅" if success else "❌"
        print(f"   {status} {endpoint}")
    
    if success_count == total_tests:
        print("\n🎉 Tous les tests sont réussis!")
        print("✅ Votre API fonctionne parfaitement")
        print("📱 L'app mobile devrait maintenant fonctionner")
    else:
        print(f"\n⚠️  {total_tests - success_count} test(s) ont échoué")
        print("🔧 Vérifiez les logs Django pour plus de détails")

if __name__ == "__main__":
    main()