#!/usr/bin/env python3
"""
Script pour trouver le bon endpoint pour récupérer les cours
"""
import requests
import json

def find_courses_endpoint():
    base_url = "http://localhost:8000/api"
    
    print("🔍 RECHERCHE DE L'ENDPOINT DES COURS")
    print("=" * 50)
    
    # 1. Connexion
    login_data = {"username": "ANNE", "password": "1234azer"}
    response = requests.post(f"{base_url}/auth/login/", json=login_data)
    token = response.json()['access']
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Tester différents endpoints possibles
    possible_endpoints = [
        "/cours/",
        "/course/", 
        "/courses/cours/",
        "/courses/list/",
        "/matiere/",
        "/matieres/",
        "/subjects/",
        "/classes/",
        "/modules/",
    ]
    
    print("\n🔍 Test des endpoints possibles...")
    
    for endpoint in possible_endpoints:
        print(f"\n📍 Test de {endpoint}...")
        try:
            response = requests.get(f"{base_url}{endpoint}", headers=headers)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    print(f"✅ {len(data)} éléments trouvés!")
                    print(f"Premier élément: {json.dumps(data[0], indent=2, ensure_ascii=False)}")
                    return endpoint
                elif isinstance(data, dict) and 'results' in data:
                    print(f"✅ {len(data['results'])} éléments trouvés (paginé)!")
                    if len(data['results']) > 0:
                        print(f"Premier élément: {json.dumps(data['results'][0], indent=2, ensure_ascii=False)}")
                    return endpoint
                else:
                    print(f"⚠️ Réponse vide ou structure inattendue")
            elif response.status_code == 404:
                print("❌ Endpoint non trouvé")
            else:
                print(f"❌ Erreur: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Erreur: {e}")
    
    # 3. Regarder dans les universités/filières pour voir s'il y a des cours
    print("\n🔍 Vérification dans les universités...")
    try:
        response = requests.get(f"{base_url}/universites/", headers=headers)
        if response.status_code == 200:
            universites = response.json()
            if len(universites) > 0:
                univ_id = universites[0]['id']
                print(f"Test avec université ID: {univ_id}")
                
                # Tester les cours d'une université
                test_endpoints = [
                    f"/universites/{univ_id}/cours/",
                    f"/universites/{univ_id}/courses/",
                    f"/universites/{univ_id}/matieres/",
                ]
                
                for endpoint in test_endpoints:
                    print(f"\n📍 Test de {endpoint}...")
                    try:
                        response = requests.get(f"{base_url}{endpoint}", headers=headers)
                        print(f"Status: {response.status_code}")
                        
                        if response.status_code == 200:
                            data = response.json()
                            if isinstance(data, list) and len(data) > 0:
                                print(f"✅ {len(data)} cours trouvés!")
                                print(f"Premier cours: {json.dumps(data[0], indent=2, ensure_ascii=False)}")
                                return endpoint
                    except Exception as e:
                        print(f"❌ Erreur: {e}")
    except Exception as e:
        print(f"❌ Erreur lors du test des universités: {e}")
    
    print("\n❌ Aucun endpoint de cours trouvé!")
    return None

if __name__ == "__main__":
    endpoint = find_courses_endpoint()
    if endpoint:
        print(f"\n🎉 Endpoint trouvé: {endpoint}")
    else:
        print("\n💡 Il faut peut-être créer des cours dans la base de données d'abord")