#!/usr/bin/env python3
"""
Test simple d'authentification sans connexion base de données
"""

import requests
import json

def test_server_basic():
    """Test de base du serveur"""
    print("🌐 TEST DE BASE DU SERVEUR")
    print("=" * 50)
    
    try:
        # Test endpoint public
        response = requests.get("https://resumecours.gestionhospitaliare.site/api/courses/", timeout=15)
        print(f"📚 /courses/ (sans auth): {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Serveur Django fonctionne")
            return True
        else:
            print(f"   ❌ Problème serveur: {response.text[:100]}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur connexion serveur: {e}")
        return False

def test_auth_endpoint_without_token():
    """Test de l'endpoint auth sans token"""
    print(f"\n🔐 TEST ENDPOINT AUTH SANS TOKEN")
    print("=" * 50)
    
    try:
        response = requests.get("https://resumecours.gestionhospitaliare.site/api/auth/user/", timeout=10)
        print(f"📊 Status: {response.status_code}")
        print(f"📄 Réponse: {response.text}")
        
        if response.status_code == 401:
            print("✅ Authentification requise (normal)")
            return True
        else:
            print("❓ Status inattendu")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_token_with_different_methods():
    """Tester le token avec différentes méthodes"""
    print(f"\n🔑 TEST DU TOKEN AVEC DIFFÉRENTES MÉTHODES")
    print("=" * 50)
    
    token = "65VjgtKRTHIiH39fnp5WOL7GLGohjT8L3yD5SqXb"
    url = "https://resumecours.gestionhospitaliare.site/api/auth/user/"
    
    # Méthode 1: requests.get avec headers
    print("🔍 Méthode 1: requests.get avec headers")
    try:
        headers = {
            'Authorization': f'Token {token}',
            'Content-Type': 'application/json'
        }
        response = requests.get(url, headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Réponse: {response.text[:200]}")
        
        if response.status_code == 200:
            print("   ✅ Méthode 1 fonctionne!")
            return True
    except Exception as e:
        print(f"   ❌ Erreur méthode 1: {e}")
    
    # Méthode 2: requests.get avec auth différent
    print(f"\n🔍 Méthode 2: Format Bearer")
    try:
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        response = requests.get(url, headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Réponse: {response.text[:200]}")
        
        if response.status_code == 200:
            print("   ✅ Méthode 2 fonctionne!")
            return True
    except Exception as e:
        print(f"   ❌ Erreur méthode 2: {e}")
    
    # Méthode 3: Sans Content-Type
    print(f"\n🔍 Méthode 3: Sans Content-Type")
    try:
        headers = {
            'Authorization': f'Token {token}'
        }
        response = requests.get(url, headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Réponse: {response.text[:200]}")
        
        if response.status_code == 200:
            print("   ✅ Méthode 3 fonctionne!")
            return True
    except Exception as e:
        print(f"   ❌ Erreur méthode 3: {e}")
    
    return False

def analyze_error_response():
    """Analyser la réponse d'erreur en détail"""
    print(f"\n🔍 ANALYSE DÉTAILLÉE DE L'ERREUR")
    print("=" * 50)
    
    token = "65VjgtKRTHIiH39fnp5WOL7GLGohjT8L3yD5SqXb"
    url = "https://resumecours.gestionhospitaliare.site/api/auth/user/"
    
    try:
        headers = {
            'Authorization': f'Token {token}',
            'Content-Type': 'application/json'
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📄 Response Text: {response.text}")
        print(f"🔧 Response Headers:")
        for key, value in response.headers.items():
            print(f"   {key}: {value}")
        
        # Analyser le JSON de réponse
        try:
            error_data = response.json()
            print(f"\n📋 Erreur JSON:")
            print(json.dumps(error_data, indent=2))
            
            # Analyser le type d'erreur
            if "detail" in error_data:
                detail = error_data["detail"]
                if "Authentication credentials were not provided" in detail:
                    print(f"\n🎯 DIAGNOSTIC:")
                    print(f"   Le serveur ne voit pas le token d'authentification")
                    print(f"   Causes possibles:")
                    print(f"   1. Le middleware d'authentification n'est pas configuré")
                    print(f"   2. rest_framework.authtoken n'est pas installé")
                    print(f"   3. Le token n'est pas dans la bonne table")
                    print(f"   4. Le serveur cache les headers")
                
        except:
            print(f"📄 Réponse non-JSON")
        
    except Exception as e:
        print(f"❌ Erreur analyse: {e}")

def suggest_solutions():
    """Suggérer des solutions"""
    print(f"\n💡 SOLUTIONS SUGGÉRÉES")
    print("=" * 50)
    
    print("Sur le serveur de production, vérifiez:")
    print()
    print("1. 📋 Configuration Django REST Framework:")
    print("   - INSTALLED_APPS contient 'rest_framework.authtoken'")
    print("   - REST_FRAMEWORK contient 'rest_framework.authentication.TokenAuthentication'")
    print()
    print("2. 🔄 Redémarrage des services:")
    print("   sudo systemctl restart gunicorn")
    print("   sudo systemctl restart httpd")
    print()
    print("3. 📊 Vérification des logs:")
    print("   sudo journalctl -u gunicorn --no-pager -n 20")
    print("   tail -f /var/log/httpd/error_log")
    print()
    print("4. 🔧 Test direct sur le serveur:")
    print("   curl -H 'Authorization: Token 65VjgtKRTHIiH39fnp5WOL7GLGohjT8L3yD5SqXb' \\")
    print("        http://localhost:8000/api/auth/user/")

def main():
    """Fonction principale"""
    print("🔍 DIAGNOSTIC SIMPLE DU PROBLÈME D'AUTHENTIFICATION")
    print("=" * 80)
    
    # 1. Test de base du serveur
    server_ok = test_server_basic()
    
    if not server_ok:
        print("\n❌ Le serveur Django ne répond pas correctement")
        return
    
    # 2. Test de l'endpoint auth sans token
    auth_endpoint_ok = test_auth_endpoint_without_token()
    
    # 3. Test du token avec différentes méthodes
    token_works = test_token_with_different_methods()
    
    if token_works:
        print(f"\n✅ Un token fonctionne!")
    else:
        print(f"\n❌ Aucun token ne fonctionne")
        
        # 4. Analyser l'erreur en détail
        analyze_error_response()
        
        # 5. Suggérer des solutions
        suggest_solutions()
    
    # Conclusion
    print(f"\n" + "=" * 80)
    print("🎯 CONCLUSION")
    print("=" * 80)
    
    if token_works:
        print("✅ Les tokens fonctionnent - Problème résolu!")
    else:
        print("❌ PROBLÈME CONFIRMÉ:")
        print("   Les tokens existent mais Django REST Framework ne les reconnaît pas")
        print()
        print("🔧 ACTION REQUISE SUR LE SERVEUR:")
        print("   1. Vérifiez la configuration REST_FRAMEWORK dans settings.py")
        print("   2. Redémarrez Gunicorn")
        print("   3. Vérifiez les logs pour plus de détails")

if __name__ == '__main__':
    main()