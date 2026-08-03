#!/usr/bin/env python3
"""
Script pour tester le bon endpoint des cours
"""
import requests
import json

def test_correct_courses_endpoint():
    base_url = "http://localhost:8000/api"
    
    print("🔍 TEST DU BON ENDPOINT DES COURS")
    print("=" * 50)
    
    # 1. Connexion
    login_data = {"username": "ANNE", "password": "1234azer"}
    response = requests.post(f"{base_url}/auth/login/", json=login_data)
    token = response.json()['access']
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Tester l'endpoint correct
    endpoints_to_test = [
        "/courses/courses/",  # Le plus probable
        "/courses/",          # Déjà testé mais on refait
        "/api/courses/",      # Au cas où
    ]
    
    for endpoint in endpoints_to_test:
        print(f"\n📍 Test de {endpoint}...")
        try:
            response = requests.get(f"{base_url}{endpoint}", headers=headers)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Réponse reçue!")
                print(f"Type: {type(data)}")
                
                if isinstance(data, list):
                    print(f"📊 {len(data)} cours trouvés")
                    if len(data) > 0:
                        print(f"\n📋 Premier cours:")
                        print(json.dumps(data[0], indent=2, ensure_ascii=False))
                        
                        print(f"\n🔍 Clés du modèle Course:")
                        for key, value in data[0].items():
                            print(f"  - {key}: {type(value)} = {value}")
                        
                        return endpoint, data
                elif isinstance(data, dict) and 'results' in data:
                    print(f"📊 {len(data['results'])} cours trouvés (paginé)")
                    if len(data['results']) > 0:
                        print(f"\n📋 Premier cours:")
                        print(json.dumps(data['results'][0], indent=2, ensure_ascii=False))
                        return endpoint, data['results']
                else:
                    print(f"⚠️ Structure inattendue: {data}")
            else:
                print(f"❌ Erreur: {response.status_code}")
                if response.text:
                    print(f"Message: {response.text}")
                    
        except Exception as e:
            print(f"❌ Exception: {e}")
    
    return None, None

if __name__ == "__main__":
    endpoint, courses = test_correct_courses_endpoint()
    if endpoint and courses:
        print(f"\n🎉 ENDPOINT TROUVÉ: {endpoint}")
        print(f"📊 {len(courses)} cours disponibles")
        print("\n📝 Structure attendue par Flutter:")
        if courses:
            course = courses[0]
            flutter_expected = {
                'id': course.get('id'),
                'nom': course.get('nom'),
                'filiere': course.get('filiere'),
                'description': course.get('description'),
                'university': course.get('university'),
                'created_at': course.get('created_at')
            }
            print(json.dumps(flutter_expected, indent=2, ensure_ascii=False))
    else:
        print("\n❌ Aucun endpoint de cours fonctionnel trouvé")