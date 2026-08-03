#!/usr/bin/env python3
"""
📚 TEST RÉPONSE SUMMARIES
========================

Vérifier ce que renvoie l'endpoint /summaries/
"""

import requests
import json

def test_summaries_endpoint():
    print("📚 TEST ENDPOINT SUMMARIES")
    print("=" * 30)
    
    BASE_URL = "http://localhost:8000/api"
    
    # 1. Connexion
    login_data = {"username": "ANNE", "password": "1234azer"}
    
    try:
        # Login
        login_response = requests.post(
            f"{BASE_URL}/auth/login/",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login échoué: {login_response.text}")
            return
        
        token = login_response.json()['access']
        print(f"✅ Token obtenu: {token[:30]}...")
        
        # 2. Test summaries
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        summaries_response = requests.get(
            f"{BASE_URL}/summaries/",
            headers=headers
        )
        
        print(f"\n📊 RÉSULTAT /summaries/:")
        print(f"Status: {summaries_response.status_code}")
        print(f"Headers: {dict(summaries_response.headers)}")
        
        if summaries_response.status_code == 200:
            try:
                data = summaries_response.json()
                print(f"✅ Données JSON reçues:")
                print(f"Type: {type(data)}")
                print(f"Nombre d'éléments: {len(data) if isinstance(data, list) else 'N/A'}")
                
                if isinstance(data, list) and len(data) > 0:
                    print(f"Premier élément: {json.dumps(data[0], indent=2)}")
                elif isinstance(data, list) and len(data) == 0:
                    print("📝 Liste vide - Pas de résumés dans la base")
                else:
                    print(f"Données: {json.dumps(data, indent=2)}")
                    
            except json.JSONDecodeError:
                print(f"❌ Réponse n'est pas du JSON valide:")
                print(f"Contenu: {summaries_response.text}")
        else:
            print(f"❌ Erreur: {summaries_response.text}")
        
        # 3. Test autres endpoints
        other_endpoints = ["/auth/user/", "/services/", "/purchases/"]
        
        for endpoint in other_endpoints:
            print(f"\n🧪 Test {endpoint}:")
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, list):
                        print(f"   ✅ {len(data)} éléments")
                    else:
                        print(f"   ✅ Données reçues")
                except:
                    print(f"   ⚠️  Réponse non-JSON")
            else:
                print(f"   ❌ Erreur: {response.text[:50]}...")
                
    except Exception as e:
        print(f"❌ Erreur générale: {e}")

if __name__ == "__main__":
    test_summaries_endpoint()