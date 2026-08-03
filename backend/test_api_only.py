#!/usr/bin/env python3
"""
Test d'API uniquement - sans connexion base de données
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
            'content': response.text[:500],  # Limiter la sortie
            'headers': dict(response.headers)
        }
    except Exception as e:
        return {
            'error': str(e),
            'status_code': None
        }

def main():
    print("=" * 60)
    print("🔍 TEST API UNIQUEMENT - SANS BASE DE DONNÉES")
    print("=" * 60)
    
    # Test 1: Endpoint public (courses)
    print("\n1️⃣ Test endpoint public /courses/")
    print("-" * 40)
    result = test_endpoint(f"{BASE_URL}/courses/")
    print(f"Status: {result.get('status_code', 'ERROR')}")
    if result.get('error'):
        print(f"❌ Erreur: {result['error']}")
    else:
        print(f"Réponse: {result['content'][:200]}...")
    
    # Test 2: Endpoint avec token
    print("\n2️⃣ Test avec tokens d'authentification")
    print("-" * 40)
    
    for i, token in enumerate(TOKENS_TO_TEST, 1):
        print(f"\nToken {i}: {token[:20]}...")
        headers = {
            'Authorization': f'Token {token}',
            'Content-Type': 'application/json'
        }
        
        # Test summaries
        result = test_endpoint(f"{BASE_URL}/summaries/", headers)
        print(f"  /summaries/ → Status: {result.get('status_code', 'ERROR')}")
        if result.get('error'):
            print(f"  ❌ Erreur: {result['error']}")
        elif result.get('status_code') == 200:
            print(f"  ✅ Succès!")
        else:
            print(f"  ⚠️  Réponse: {result['content'][:100]}...")
    
    # Test 3: Vérification CORS
    print("\n3️⃣ Test CORS")
    print("-" * 40)
    headers = {
        'Origin': 'https://resumecours.gestionhospitaliare.site',
        'Access-Control-Request-Method': 'GET',
        'Access-Control-Request-Headers': 'Authorization'
    }
    result = test_endpoint(f"{BASE_URL}/courses/", headers, 'OPTIONS')
    print(f"OPTIONS request → Status: {result.get('status_code', 'ERROR')}")
    
    # Test 4: Endpoints disponibles
    print("\n4️⃣ Test endpoints disponibles")
    print("-" * 40)
    endpoints = [
        "/",
        "/admin/",
        "/api/",
        "/courses/",
        "/summaries/",
        "/users/",
    ]
    
    for endpoint in endpoints:
        result = test_endpoint(f"{BASE_URL}{endpoint}")
        status = result.get('status_code', 'ERROR')
        print(f"  {endpoint:<15} → {status}")

if __name__ == "__main__":
    main()