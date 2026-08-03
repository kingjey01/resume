#!/usr/bin/env python3
"""
Test avec les VRAIS endpoints selon la configuration URLs
"""
import requests
import json

# Configuration
BASE_URL = "https://resumecours.gestionhospitaliare.site"
TOKENS_TO_TEST = [
    "a1b2c3d4e5f6789012345678901234567890abcd",
    "b2c3d4e5f6789012345678901234567890abcde1",
    "c3d4e5f6789012345678901234567890abcdef12"
]

def test_endpoint(url, headers=None, method='GET'):
    """Test un endpoint avec gestion d'erreur"""
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, timeout=10)
        else:
            response = requests.post(url, headers=headers, timeout=10)
        
        return {
            'status_code': response.status_code,
            'content': response.text[:500],
            'headers': dict(response.headers)
        }
    except Exception as e:
        return {
            'error': str(e),
            'status_code': None
        }

def main():
    print("=" * 60)
    print("🔍 TEST AVEC LES VRAIS ENDPOINTS /api/")
    print("=" * 60)
    
    # Test 1: Endpoints corrects selon urls.py
    print("\n1️⃣ Test endpoints publics")
    print("-" * 40)
    
    endpoints_public = [
        "/api/courses/",
        "/api/",
        "/swagger/",
        "/admin/"
    ]
    
    for endpoint in endpoints_public:
        result = test_endpoint(f"{BASE_URL}{endpoint}")
        status = result.get('status_code', 'ERROR')
        print(f"  {endpoint:<20} → {status}")
        if status == 401:
            print(f"    ❌ Auth requise: {result['content'][:100]}...")
        elif status == 200:
            print(f"    ✅ OK!")
        elif result.get('error'):
            print(f"    ❌ Erreur: {result['error']}")
    
    # Test 2: Endpoints avec authentification
    print("\n2️⃣ Test avec tokens d'authentification")
    print("-" * 40)
    
    auth_endpoints = [
        "/api/courses/",
        "/api/summaries/",
        "/api/auth/",
    ]
    
    for i, token in enumerate(TOKENS_TO_TEST, 1):
        print(f"\n🔑 Token {i}: {token[:20]}...")
        headers = {
            'Authorization': f'Token {token}',
            'Content-Type': 'application/json'
        }
        
        for endpoint in auth_endpoints:
            result = test_endpoint(f"{BASE_URL}{endpoint}", headers)
            status = result.get('status_code', 'ERROR')
            print(f"  {endpoint:<20} → {status}")
            
            if status == 200:
                print(f"    ✅ Succès!")
                # Afficher un peu de contenu si c'est du JSON
                try:
                    content = json.loads(result['content'])
                    if isinstance(content, list):
                        print(f"    📊 {len(content)} éléments trouvés")
                    elif isinstance(content, dict):
                        print(f"    📊 Clés: {list(content.keys())[:3]}")
                except:
                    pass
            elif status == 401:
                print(f"    ❌ Token invalide: {result['content'][:100]}...")
            elif status == 403:
                print(f"    ⚠️  Accès refusé: {result['content'][:100]}...")
            elif result.get('error'):
                print(f"    ❌ Erreur: {result['error']}")
    
    # Test 3: Vérification structure API
    print("\n3️⃣ Structure de l'API")
    print("-" * 40)
    
    # Test sans auth d'abord
    result = test_endpoint(f"{BASE_URL}/api/courses/")
    print(f"Sans auth /api/courses/ → {result.get('status_code')}")
    
    # Test avec le premier token
    headers = {'Authorization': f'Token {TOKENS_TO_TEST[0]}'}
    result = test_endpoint(f"{BASE_URL}/api/courses/", headers)
    print(f"Avec auth /api/courses/ → {result.get('status_code')}")
    
    if result.get('status_code') == 200:
        print("✅ L'authentification fonctionne!")
    elif result.get('status_code') == 401:
        print("❌ Token invalide ou configuration auth cassée")
        print(f"Détail: {result['content'][:200]}")

if __name__ == "__main__":
    main()