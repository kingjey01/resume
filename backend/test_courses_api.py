#!/usr/bin/env python3
"""
Test complet de l'API courses avec les vrais endpoints
"""
import requests
import json

# Configuration
BASE_URL = "https://resumecours.gestionhospitaliare.site"
TOKEN = "a1b2c3d4e5f6789012345678901234567890abcd"

def test_endpoint(url, headers=None, method='GET'):
    """Test un endpoint avec gestion d'erreur"""
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, timeout=10)
        else:
            response = requests.post(url, headers=headers, timeout=10)
        
        return {
            'status_code': response.status_code,
            'content': response.text[:800],
            'headers': dict(response.headers)
        }
    except Exception as e:
        return {
            'error': str(e),
            'status_code': None
        }

def main():
    print("=" * 60)
    print("🔍 TEST COMPLET API COURSES")
    print("=" * 60)
    
    # Headers avec token
    headers = {
        'Authorization': f'Token {TOKEN}',
        'Content-Type': 'application/json'
    }
    
    # Endpoints à tester selon courses/urls.py
    endpoints = [
        # Endpoints principaux
        ("/api/courses/", "Courses - Liste"),
        ("/api/", "API Root"),
        
        # Endpoints du routeur
        ("/api/universites/", "Universités"),
        ("/api/filieres/", "Filières"),
        ("/api/promotions/", "Promotions"),
        ("/api/universite-filieres/", "Université-Filières"),
        ("/api/filiere-promotions/", "Filière-Promotions"),
        
        # Sessions
        ("/api/sessions/", "Sessions"),
        ("/api/sessions/audio/", "Sessions Audio"),
        
        # Summaries
        ("/api/summaries/", "Summaries"),
        ("/api/summaries/achetes/", "Summaries Achetés"),
        ("/api/summaries/gratuits/", "Summaries Gratuits"),
    ]
    
    print("\n1️⃣ Test sans authentification")
    print("-" * 50)
    for endpoint, description in endpoints[:5]:  # Premiers endpoints seulement
        result = test_endpoint(f"{BASE_URL}{endpoint}")
        status = result.get('status_code', 'ERROR')
        print(f"  {description:<25} → {status}")
        if status == 200:
            try:
                content = json.loads(result['content'])
                if isinstance(content, list):
                    print(f"    📊 {len(content)} éléments")
                elif isinstance(content, dict):
                    print(f"    📊 Clés: {list(content.keys())[:3]}")
            except:
                pass
    
    print("\n2️⃣ Test avec authentification")
    print("-" * 50)
    for endpoint, description in endpoints:
        result = test_endpoint(f"{BASE_URL}{endpoint}", headers)
        status = result.get('status_code', 'ERROR')
        print(f"  {description:<25} → {status}")
        
        if status == 200:
            try:
                content = json.loads(result['content'])
                if isinstance(content, list):
                    print(f"    ✅ {len(content)} éléments trouvés")
                elif isinstance(content, dict):
                    keys = list(content.keys())[:3]
                    print(f"    ✅ Clés: {keys}")
            except:
                print(f"    ✅ Réponse OK (non-JSON)")
        elif status == 401:
            print(f"    ❌ Non autorisé")
        elif status == 403:
            print(f"    ⚠️  Accès refusé")
        elif status == 404:
            print(f"    ❌ Non trouvé")
        elif result.get('error'):
            print(f"    ❌ Erreur: {result['error']}")
    
    print("\n3️⃣ Test spécifique summaries")
    print("-" * 50)
    
    # Test détaillé pour summaries
    summaries_endpoints = [
        "/api/summaries/",
        "/api/summaries/achetes/",
        "/api/summaries/gratuits/",
    ]
    
    for endpoint in summaries_endpoints:
        print(f"\n🔍 Test détaillé: {endpoint}")
        result = test_endpoint(f"{BASE_URL}{endpoint}", headers)
        print(f"Status: {result.get('status_code')}")
        if result.get('content'):
            print(f"Contenu: {result['content'][:300]}...")

if __name__ == "__main__":
    main()