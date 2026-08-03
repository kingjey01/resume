#!/usr/bin/env python3
"""
Test rapide de l'authentification en production
"""

import requests
import json
import time

# Configuration production
BASE_URL = "https://resumecours.gestionhospitaliare.site/api"

def test_auth_endpoints_quick():
    """Test rapide des endpoints d'authentification"""
    print("🔐 TEST RAPIDE DE L'AUTHENTIFICATION EN PRODUCTION")
    print("=" * 60)
    print(f"🌐 Serveur: {BASE_URL}")
    print()
    
    # Endpoints à tester
    endpoints = [
        {
            'url': '/auth/user/',
            'name': 'User Info',
            'requires_auth': True
        },
        {
            'url': '/users/profile/',
            'name': 'User Profile',
            'requires_auth': True
        },
        {
            'url': '/courses/',
            'name': 'Courses List',
            'requires_auth': False
        },
        {
            'url': '/courses/sessions/audio/',
            'name': 'Audio Sessions',
            'requires_auth': True
        }
    ]
    
    # Test sans authentification
    print("🔓 Test sans authentification:")
    for endpoint in endpoints:
        try:
            url = BASE_URL + endpoint['url']
            response = requests.get(url, timeout=10)
            
            status_icon = "✅" if response.status_code == 200 else "🔐" if response.status_code == 401 else "❌"
            print(f"  {status_icon} {endpoint['name']}: {response.status_code}")
            
            if response.status_code == 401 and endpoint['requires_auth']:
                print(f"    ✅ Authentification requise (normal)")
            elif response.status_code == 200 and not endpoint['requires_auth']:
                print(f"    ✅ Accessible publiquement (normal)")
            elif response.status_code == 200 and endpoint['requires_auth']:
                print(f"    ⚠️ Accessible sans auth (vérifier permissions)")
            
        except Exception as e:
            print(f"  ❌ {endpoint['name']}: Erreur - {e}")
    
    return True

def test_with_hardcoded_tokens():
    """Tester avec des tokens codés en dur (pour debug)"""
    print(f"\n🔑 TEST AVEC TOKENS DE DEBUG")
    print("=" * 60)
    
    # Tokens de test (à remplacer par les vrais tokens)
    test_tokens = [
        "your_cp_token_here",
        "your_etudiant_token_here", 
        "your_admin_token_here"
    ]
    
    # Remplacer par de vrais tokens si disponibles
    print("⚠️ Remplacez les tokens de test dans le script")
    print("   Utilisez les tokens générés par fix_auth_issues.py")
    
    for i, token in enumerate(test_tokens):
        if token.startswith("your_"):
            print(f"  ❌ Token {i+1}: Token de test non configuré")
            continue
        
        print(f"\n🔑 Test avec token {i+1}: {token[:10]}...")
        
        headers = {
            'Authorization': f'Token {token}',
            'Content-Type': 'application/json'
        }
        
        # Tester l'endpoint user
        try:
            response = requests.get(f"{BASE_URL}/auth/user/", headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ Authentification réussie")
                print(f"  👤 Utilisateur: {data.get('email', 'N/A')}")
                print(f"  🏷️ ID: {data.get('id', 'N/A')}")
                
                # Tester les sessions audio
                audio_response = requests.get(f"{BASE_URL}/courses/sessions/audio/", headers=headers, timeout=10)
                if audio_response.status_code == 200:
                    audio_data = audio_response.json()
                    sessions_count = len(audio_data.get('sessions', []))
                    print(f"  🎵 Sessions audio: {sessions_count}")
                else:
                    print(f"  ❌ Sessions audio: {audio_response.status_code}")
                
            elif response.status_code == 401:
                print(f"  ❌ Token invalide ou expiré")
                print(f"  📄 Réponse: {response.text[:100]}")
            else:
                print(f"  ❓ Status inattendu: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Erreur: {e}")

def test_cors_headers():
    """Tester les headers CORS"""
    print(f"\n🌐 TEST DES HEADERS CORS")
    print("=" * 60)
    
    # Test OPTIONS request (preflight CORS)
    try:
        response = requests.options(
            f"{BASE_URL}/auth/user/",
            headers={
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'Authorization, Content-Type'
            },
            timeout=10
        )
        
        print(f"OPTIONS request: {response.status_code}")
        
        # Vérifier les headers CORS
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
            'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')
        }
        
        print(f"Headers CORS:")
        for header, value in cors_headers.items():
            status = "✅" if value else "❌"
            print(f"  {status} {header}: {value}")
        
        return any(cors_headers.values())
        
    except Exception as e:
        print(f"❌ Erreur test CORS: {e}")
        return False

def generate_curl_commands():
    """Générer des commandes curl pour tester"""
    print(f"\n📋 COMMANDES CURL POUR TESTER")
    print("=" * 60)
    
    print("# Test sans authentification:")
    print(f"curl -I {BASE_URL}/courses/")
    print()
    
    print("# Test avec authentification (remplacez YOUR_TOKEN):")
    print(f"curl -H 'Authorization: Token YOUR_TOKEN' \\")
    print(f"     {BASE_URL}/auth/user/")
    print()
    
    print("# Test sessions audio:")
    print(f"curl -H 'Authorization: Token YOUR_TOKEN' \\")
    print(f"     {BASE_URL}/courses/sessions/audio/")
    print()
    
    print("# Test CORS:")
    print(f"curl -X OPTIONS \\")
    print(f"     -H 'Origin: http://localhost:3000' \\")
    print(f"     -H 'Access-Control-Request-Method: GET' \\")
    print(f"     -H 'Access-Control-Request-Headers: Authorization' \\")
    print(f"     {BASE_URL}/auth/user/")

def check_server_status():
    """Vérifier le statut général du serveur"""
    print(f"\n🏥 VÉRIFICATION DU STATUT SERVEUR")
    print("=" * 60)
    
    try:
        # Test de connectivité de base
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/courses/", timeout=15)
        response_time = (time.time() - start_time) * 1000
        
        print(f"🌐 Connectivité: ✅")
        print(f"⏱️ Temps de réponse: {response_time:.0f}ms")
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ Serveur Django opérationnel")
            
            # Vérifier le contenu
            try:
                data = response.json()
                if isinstance(data, list):
                    print(f"📚 Cours disponibles: {len(data)}")
                elif isinstance(data, dict) and 'count' in data:
                    print(f"📚 Cours disponibles: {data['count']}")
            except:
                print(f"📄 Réponse non-JSON")
        else:
            print(f"❌ Problème serveur: {response.status_code}")
            print(f"📄 Réponse: {response.text[:200]}")
        
        return response.status_code == 200
        
    except requests.exceptions.Timeout:
        print(f"⏰ Timeout - Serveur lent ou inaccessible")
        return False
    except requests.exceptions.ConnectionError:
        print(f"🔌 Erreur de connexion - Serveur down?")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def main():
    """Fonction principale de test rapide"""
    print("🚀 TEST RAPIDE D'AUTHENTIFICATION - PRODUCTION")
    print("=" * 80)
    
    try:
        # 1. Vérifier le statut du serveur
        server_ok = check_server_status()
        
        if not server_ok:
            print("\n❌ Serveur inaccessible - Arrêt des tests")
            return
        
        # 2. Tester les endpoints
        test_auth_endpoints_quick()
        
        # 3. Tester CORS
        cors_ok = test_cors_headers()
        
        # 4. Tester avec tokens (si configurés)
        test_with_hardcoded_tokens()
        
        # 5. Générer les commandes curl
        generate_curl_commands()
        
        # Résumé
        print(f"\n" + "=" * 80)
        print("📊 RÉSUMÉ DU TEST RAPIDE")
        print("=" * 80)
        
        print(f"🌐 Serveur accessible: {'✅' if server_ok else '❌'}")
        print(f"🌐 CORS configuré: {'✅' if cors_ok else '❌'}")
        
        print(f"\n💡 PROCHAINES ÉTAPES:")
        print(f"1. Exécutez: python fix_auth_issues.py")
        print(f"2. Récupérez les tokens générés")
        print(f"3. Testez avec les commandes curl affichées")
        print(f"4. Configurez les tokens dans votre app Flutter")
        
        if not cors_ok:
            print(f"\n⚠️ PROBLÈME CORS DÉTECTÉ:")
            print(f"   Vérifiez la configuration CORS dans settings.py")
            print(f"   Redémarrez le serveur après modification")
        
    except KeyboardInterrupt:
        print(f"\n⏹️ Test interrompu")
    except Exception as e:
        print(f"\n❌ Erreur générale: {e}")

if __name__ == '__main__':
    main()