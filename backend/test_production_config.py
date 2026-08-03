#!/usr/bin/env python3
"""
🔍 TEST SPÉCIFIQUE CONFIGURATION PRODUCTION
==========================================

Test pour diagnostiquer les problèmes de configuration JWT en production
"""

import requests
import json
import jwt
from datetime import datetime

BASE_URL = "https://resumecours.gestionhospitaliare.site/api"

def test_cors_preflight():
    """Test CORS preflight pour voir si le serveur répond correctement"""
    print("🌐 Test CORS Preflight...")
    
    try:
        response = requests.options(
            f"{BASE_URL}/auth/user/",
            headers={
                "Origin": "http://localhost:8080",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization,content-type"
            },
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        print("Headers de réponse:")
        for header, value in response.headers.items():
            if 'cors' in header.lower() or 'access-control' in header.lower():
                print(f"  {header}: {value}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Erreur CORS: {e}")
        return False

def test_jwt_validation():
    """Test de validation JWT côté serveur"""
    print("\n🔑 Test validation JWT...")
    
    # 1. Obtenir un token
    login_data = {"username": "ANNE", "password": "1234azer"}
    
    try:
        login_response = requests.post(
            f"{BASE_URL}/auth/login/",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if login_response.status_code != 200:
            print(f"❌ Échec connexion: {login_response.text}")
            return False
        
        token = login_response.json()['access']
        print(f"✅ Token obtenu: {token[:30]}...")
        
        # 2. Décoder le token pour vérifier sa structure
        try:
            decoded = jwt.decode(token, options={"verify_signature": False})
            print(f"✅ Token structure: {json.dumps(decoded, indent=2)}")
            
            # Vérifier les champs requis
            required_fields = ['token_type', 'exp', 'user_id']
            missing_fields = [field for field in required_fields if field not in decoded]
            
            if missing_fields:
                print(f"❌ Champs manquants dans le token: {missing_fields}")
                return False
            
            print("✅ Structure du token correcte")
            
        except Exception as e:
            print(f"❌ Erreur décodage token: {e}")
            return False
        
        # 3. Tester différents formats d'Authorization header
        test_formats = [
            ("Bearer standard", f"Bearer {token}"),
            ("JWT format", f"JWT {token}"),
        ]
        
        for format_name, auth_header in test_formats:
            print(f"\n🧪 Test format: {format_name}")
            
            try:
                response = requests.get(
                    f"{BASE_URL}/auth/user/",
                    headers={
                        "Authorization": auth_header,
                        "Content-Type": "application/json"
                    },
                    timeout=10
                )
                
                print(f"  Status: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"  ✅ {format_name} fonctionne!")
                    return True
                else:
                    print(f"  ❌ {format_name} échoue: {response.text[:100]}")
                    
            except Exception as e:
                print(f"  ❌ Erreur {format_name}: {e}")
        
        return False
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        return False

def test_server_logs_simulation():
    """Simuler ce qui se passe côté serveur"""
    print("\n📋 Simulation côté serveur...")
    
    print("Ce qui devrait se passer côté Django:")
    print("1. Requête reçue avec header Authorization")
    print("2. JWTAuthentication.authenticate() appelé")
    print("3. Token extrait et validé")
    print("4. User attaché à request.user")
    print("5. Vue exécutée avec user authentifié")
    
    print("\nCe qui se passe probablement:")
    print("❌ JWTAuthentication ne reconnaît pas le token")
    print("❌ request.user reste AnonymousUser")
    print("❌ IsAuthenticated permission échoue")

def main():
    print("🔍 DIAGNOSTIC CONFIGURATION PRODUCTION")
    print("=" * 50)
    
    # Tests
    cors_ok = test_cors_preflight()
    jwt_ok = test_jwt_validation()
    test_server_logs_simulation()
    
    # Résumé
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DIAGNOSTIC")
    print("=" * 50)
    
    print(f"🌐 CORS Preflight: {'✅' if cors_ok else '❌'}")
    print(f"🔑 JWT Validation: {'✅' if jwt_ok else '❌'}")
    
    if not cors_ok and not jwt_ok:
        print("\n🚨 PROBLÈMES MULTIPLES DÉTECTÉS:")
        print("1. ❌ Configuration CORS incorrecte")
        print("2. ❌ Authentification JWT ne fonctionne pas")
        print("\n🔧 ACTIONS REQUISES:")
        print("1. Corriger CORS_ALLOWED_ORIGINS dans settings.py")
        print("2. Vérifier configuration SIMPLE_JWT")
        print("3. Redémarrer le serveur Django")
    elif not cors_ok:
        print("\n🚨 PROBLÈME CORS UNIQUEMENT:")
        print("🔧 Ajoutez localhost:8080 à CORS_ALLOWED_ORIGINS")
    elif not jwt_ok:
        print("\n🚨 PROBLÈME JWT UNIQUEMENT:")
        print("🔧 Vérifiez la configuration SIMPLE_JWT et REST_FRAMEWORK")
    else:
        print("\n🎉 TOUT FONCTIONNE!")

if __name__ == "__main__":
    main()