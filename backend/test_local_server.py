#!/usr/bin/env python3
"""
Test rapide après redémarrage du serveur
"""
import requests

BASE_URL = "https://resumecours.gestionhospitaliare.site"

# Tokens du diagnostic
TOKENS = {
    'ETUDIANT': '3580d7190850a9294c56cb1c3158adfc35be86bd',
    'CP': 'f54d458ba830c31c8dd31eaedcb73479f9ac2f7b', 
    'ADMIN': '9743c81fdd50b11c38a55fb9de24c56d8d4857dd'
}

def quick_test():
    print("🚀 TEST RAPIDE APRÈS REDÉMARRAGE")
    print("="*50)
    
    # Test 1: Sans authentification
    print("\n1️⃣ Test sans auth:")
    try:
        response = requests.get(f"{BASE_URL}/api/courses/", timeout=10)
        print(f"  /api/courses/ → {response.status_code}")
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
    
    # Test 2: Avec token étudiant
    print("\n2️⃣ Test avec token ÉTUDIANT:")
    headers = {'Authorization': f'Token {TOKENS["ETUDIANT"]}'}
    
    endpoints = [
        "/api/courses/",
        "/api/summaries/",
        "/api/summaries/gratuits/"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=10)
            print(f"  {endpoint:<25} → {response.status_code}")
            if response.status_code == 401:
                print(f"    ❌ {response.json().get('detail', 'Erreur auth')}")
            elif response.status_code == 200:
                print(f"    ✅ Succès!")
        except Exception as e:
            print(f"  {endpoint:<25} → ERROR: {e}")
    
    # Test 3: Avec token ADMIN
    print("\n3️⃣ Test avec token ADMIN:")
    headers = {'Authorization': f'Token {TOKENS["ADMIN"]}'}
    
    try:
        response = requests.get(f"{BASE_URL}/api/summaries/", headers=headers, timeout=10)
        print(f"  /api/summaries/ → {response.status_code}")
        if response.status_code == 200:
            print(f"    ✅ ADMIN peut accéder aux summaries!")
        else:
            print(f"    ❌ Problème: {response.text[:100]}")
    except Exception as e:
        print(f"  ❌ Erreur: {e}")

if __name__ == "__main__":
    quick_test()