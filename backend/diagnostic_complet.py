#!/usr/bin/env python3
"""
🏥 DIAGNOSTIC COMPLET DE L'API
=============================

Script de diagnostic complet pour identifier le problème d'authentification
"""

import requests
import json
import jwt
from datetime import datetime

BASE_URL = "https://resumecours.gestionhospitaliare.site/api"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print('='*60)

def test_1_server_status():
    """Test 1: Vérifier que le serveur répond"""
    print_section("TEST 1: STATUT DU SERVEUR")
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"✅ Serveur accessible - Status: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Serveur inaccessible: {e}")
        return False

def test_2_login():
    """Test 2: Connexion et génération de token"""
    print_section("TEST 2: CONNEXION ET TOKEN")
    
    login_data = {
        "username": "ANNE",
        "password": "1234azer"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login/",
            json=login_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Status de connexion: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data['access']
            print(f"✅ Token généré: {token[:30]}...")
            
            # Décoder le token
            try:
                decoded = jwt.decode(token, options={"verify_signature": False})
                exp_date = datetime.fromtimestamp(decoded['exp'])
                print(f"✅ Token valide jusqu'à: {exp_date}")
                print(f"✅ User ID: {decoded.get('user_id')}")
                return token
            except Exception as e:
                print(f"❌ Erreur décodage token: {e}")
                return None
        else:
            print(f"❌ Échec connexion: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Erreur connexion: {e}")
        return None

def test_3_endpoints_without_auth():
    """Test 3: Endpoints sans authentification"""
    print_section("TEST 3: ENDPOINTS PUBLICS")
    
    public_endpoints = [
        "/auth/login/",
        "/auth/register/",
    ]
    
    results = {}
    for endpoint in public_endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            status = "✅" if response.status_code in [200, 405] else "❌"
            print(f"{status} {endpoint} - Status: {response.status_code}")
            results[endpoint] = response.status_code
        except Exception as e:
            print(f"❌ {endpoint} - Erreur: {e}")
            results[endpoint] = "ERROR"
    
    return results

def test_4_auth_endpoints(token):
    """Test 4: Endpoints avec authentification"""
    print_section("TEST 4: ENDPOINTS AUTHENTIFIÉS")
    
    if not token:
        print("❌ Pas de token disponible")
        return {}
    
    auth_endpoints = [
        "/auth/user/",
        "/summaries/",
        "/services/",
        "/purchases/"
    ]
    
    results = {}
    
    for endpoint in auth_endpoints:
        print(f"\n🧪 Test {endpoint}:")
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(
                f"{BASE_URL}{endpoint}",
                headers=headers,
                timeout=10
            )
            
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:100]}...")
            
            if response.status_code == 200:
                print("   ✅ SUCCÈS")
                results[endpoint] = "SUCCESS"
            elif response.status_code == 401:
                print("   ❌ NON AUTORISÉ")
                results[endpoint] = "UNAUTHORIZED"
            else:
                print(f"   ⚠️  AUTRE ERREUR: {response.status_code}")
                results[endpoint] = f"ERROR_{response.status_code}"
                
        except Exception as e:
            print(f"   ❌ EXCEPTION: {e}")
            results[endpoint] = "EXCEPTION"
    
    return results

def test_5_cors_headers():
    """Test 5: Vérifier les headers CORS"""
    print_section("TEST 5: HEADERS CORS")
    
    try:
        response = requests.options(
            f"{BASE_URL}/auth/user/",
            headers={
                "Origin": "http://localhost:8080",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization"
            }
        )
        
        print(f"Status OPTIONS: {response.status_code}")
        
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
        }
        
        print("Headers CORS:")
        for header, value in cors_headers.items():
            status = "✅" if value else "❌"
            print(f"   {status} {header}: {value}")
        
        return cors_headers
        
    except Exception as e:
        print(f"❌ Erreur test CORS: {e}")
        return {}

def generate_report(server_ok, token, public_results, auth_results, cors_headers):
    """Générer un rapport de diagnostic"""
    print_section("📊 RAPPORT DE DIAGNOSTIC")
    
    print(f"🖥️  Serveur accessible: {'✅' if server_ok else '❌'}")
    print(f"🔑 Token généré: {'✅' if token else '❌'}")
    
    print(f"\n📋 Endpoints publics:")
    for endpoint, status in public_results.items():
        icon = "✅" if status in [200, 405] else "❌"
        print(f"   {icon} {endpoint}: {status}")
    
    print(f"\n🔒 Endpoints authentifiés:")
    success_count = 0
    for endpoint, status in auth_results.items():
        icon = "✅" if status == "SUCCESS" else "❌"
        if status == "SUCCESS":
            success_count += 1
        print(f"   {icon} {endpoint}: {status}")
    
    print(f"\n🌐 CORS configuré: {'✅' if any(cors_headers.values()) else '❌'}")
    
    # Diagnostic final
    print(f"\n🎯 DIAGNOSTIC FINAL:")
    if success_count == len(auth_results):
        print("✅ TOUT FONCTIONNE PARFAITEMENT!")
        print("📱 Votre app mobile devrait fonctionner")
    elif token and success_count == 0:
        print("❌ PROBLÈME D'AUTHENTIFICATION JWT")
        print("🔧 Le token est généré mais pas reconnu")
        print("💡 Vérifiez la configuration Django REST Framework")
    elif not token:
        print("❌ PROBLÈME DE GÉNÉRATION DE TOKEN")
        print("🔧 Vérifiez la configuration JWT")
    else:
        print(f"⚠️  PROBLÈME PARTIEL: {success_count}/{len(auth_results)} endpoints fonctionnent")

def main():
    print("🏥 DIAGNOSTIC COMPLET DE L'API RESUME+")
    print("Cela va tester tous les aspects de votre API...")
    
    # Tests séquentiels
    server_ok = test_1_server_status()
    token = test_2_login()
    public_results = test_3_endpoints_without_auth()
    auth_results = test_4_auth_endpoints(token)
    cors_headers = test_5_cors_headers()
    
    # Rapport final
    generate_report(server_ok, token, public_results, auth_results, cors_headers)
    
    print(f"\n💡 PROCHAINES ÉTAPES:")
    if token and not any(status == "SUCCESS" for status in auth_results.values()):
        print("1. Le problème est dans l'authentification JWT côté serveur")
        print("2. Vérifiez les logs Django sur le serveur")
        print("3. Testez l'authentification en local avec manage.py shell")
    else:
        print("1. Testez avec votre app Flutter")
        print("2. Utilisez les mêmes credentials: ANNE / 1234azer")

if __name__ == "__main__":
    main()