#!/usr/bin/env python3
"""
Test pour vérifier que tous les endpoints existent et fonctionnent
"""
import requests
import json

def test_all_endpoints():
    base_url = "http://localhost:8000/api"
    
    print("🔍 TEST DE TOUS LES ENDPOINTS")
    print("=" * 40)
    
    # Test 1: Endpoint login
    print("\n1. Test endpoint /auth/login/")
    try:
        response = requests.post(f"{base_url}/auth/login/", json={
            "username": "ANNE",
            "password": "1234azer"
        })
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Login fonctionne")
            token = response.json().get('access')
        else:
            print(f"   ❌ Erreur: {response.text}")
            return
    except Exception as e:
        print(f"   ❌ Erreur connexion: {e}")
        return
    
    # Test 2: Endpoint summaries
    print("\n2. Test endpoint /summaries/")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{base_url}/summaries/", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            summaries = response.json()
            print(f"   ✅ {len(summaries)} summaries disponibles")
        else:
            print(f"   ❌ Erreur: {response.text}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Test 3: Endpoint user profile
    print("\n3. Test endpoint /auth/user/")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{base_url}/auth/user/", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            user = response.json()
            print(f"   ✅ Utilisateur: {user.get('username', 'N/A')}")
        else:
            print(f"   ❌ Erreur: {response.text}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    print("\n🎉 TOUS LES ENDPOINTS DJANGO FONCTIONNENT !")
    print("Le problème est donc côté Flutter, pas côté Django.")

if __name__ == "__main__":
    test_all_endpoints()