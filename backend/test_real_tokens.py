#!/usr/bin/env python3
"""
Test avec les vrais tokens créés avec des profils utilisateurs
"""
import requests
import json

# Configuration
BASE_URL = "https://resumecours.gestionhospitaliare.site"

# Vrais tokens avec profils
TOKENS = {
    'ETUDIANT': '3580d7190850a9294c56cb1c3158adfc35be86bd',
    'CP': 'f54d458ba830c31c8dd31eaedcb73479f9ac2f7b',
    'ADMIN': '9743c81fdd50b11c38a55fb9de24c56d8d4857dd'
}

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

def test_user_permissions(role, token):
    """Test les permissions pour un rôle donné"""
    print(f"\n{'='*60}")
    print(f"🔍 TEST PERMISSIONS - {role}")
    print(f"Token: {token[:20]}...")
    print('='*60)
    
    headers = {
        'Authorization': f'Token {token}',
        'Content-Type': 'application/json'
    }
    
    # Endpoints à tester
    endpoints = [
        ("/api/summaries/", "Summaries (Liste)"),
        ("/api/summaries/achetes/", "Summaries Achetés"),
        ("/api/summaries/gratuits/", "Summaries Gratuits"),
        ("/api/courses/", "Courses"),
        ("/api/sessions/", "Sessions"),
        ("/api/universite-filieres/", "Université-Filières"),
        ("/api/filiere-promotions/", "Filière-Promotions"),
    ]
    
    results = {}
    
    for endpoint, description in endpoints:
        result = test_endpoint(f"{BASE_URL}{endpoint}", headers)
        status = result.get('status_code', 'ERROR')
        results[endpoint] = status
        
        # Affichage avec couleurs
        if status == 200:
            print(f"  ✅ {description:<25} → {status}")
            # Essayer d'analyser le JSON
            try:
                content = json.loads(result['content'])
                if isinstance(content, list):
                    print(f"      📊 {len(content)} éléments trouvés")
                elif isinstance(content, dict):
                    keys = list(content.keys())[:3]
                    print(f"      📊 Clés: {keys}")
            except:
                print(f"      📄 Réponse non-JSON")
        elif status == 401:
            print(f"  ❌ {description:<25} → {status} (Non autorisé)")
        elif status == 403:
            print(f"  ⚠️  {description:<25} → {status} (Accès refusé)")
        elif status == 404:
            print(f"  🔍 {description:<25} → {status} (Non trouvé)")
        else:
            print(f"  ❓ {description:<25} → {status}")
    
    return results

def main():
    print("🚀 TEST COMPLET DES PERMISSIONS AVEC VRAIS TOKENS")
    print("="*70)
    
    all_results = {}
    
    # Tester chaque rôle
    for role, token in TOKENS.items():
        results = test_user_permissions(role, token)
        all_results[role] = results
    
    # Résumé comparatif
    print(f"\n{'='*70}")
    print("📊 RÉSUMÉ COMPARATIF DES PERMISSIONS")
    print('='*70)
    
    endpoints = [
        "/api/summaries/",
        "/api/summaries/gratuits/", 
        "/api/summaries/achetes/",
        "/api/universite-filieres/",
        "/api/filiere-promotions/"
    ]
    
    print(f"{'Endpoint':<30} {'ÉTUDIANT':<10} {'CP':<10} {'ADMIN':<10}")
    print("-" * 70)
    
    for endpoint in endpoints:
        etudiant_status = all_results.get('ETUDIANT', {}).get(endpoint, 'N/A')
        cp_status = all_results.get('CP', {}).get(endpoint, 'N/A')
        admin_status = all_results.get('ADMIN', {}).get(endpoint, 'N/A')
        
        print(f"{endpoint:<30} {etudiant_status:<10} {cp_status:<10} {admin_status:<10}")
    
    # Analyse des résultats
    print(f"\n{'='*70}")
    print("🎯 ANALYSE DES RÉSULTATS")
    print('='*70)
    
    # Vérifier si les permissions fonctionnent comme attendu
    summaries_etudiant = all_results.get('ETUDIANT', {}).get('/api/summaries/', 0)
    summaries_cp = all_results.get('CP', {}).get('/api/summaries/', 0)
    summaries_admin = all_results.get('ADMIN', {}).get('/api/summaries/', 0)
    
    if summaries_etudiant == 200:
        print("✅ ÉTUDIANT peut accéder aux summaries")
    else:
        print("❌ ÉTUDIANT ne peut pas accéder aux summaries")
    
    if summaries_cp == 200:
        print("✅ CP peut accéder aux summaries")
    else:
        print("❌ CP ne peut pas accéder aux summaries")
    
    if summaries_admin == 200:
        print("✅ ADMIN peut accéder aux summaries")
    else:
        print("❌ ADMIN ne peut pas accéder aux summaries")

if __name__ == "__main__":
    main()