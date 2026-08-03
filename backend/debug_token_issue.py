#!/usr/bin/env python3
"""
Debug du problème de tokens
"""

import requests
import pymysql

def check_tokens_in_database():
    """Vérifier les tokens directement en base"""
    print("🔍 VÉRIFICATION DES TOKENS EN BASE DE DONNÉES")
    print("=" * 60)
    
    try:
        connection = pymysql.connect(
            host='resumecours.gestionhospitaliare.site',
            user='jey_resume',
            password='1234',
            database='jey_resume',
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        # Vérifier les tokens en base
        cursor.execute("""
            SELECT t.`key`, u.`email`, u.`is_active`, t.`created`
            FROM `authtoken_token` t
            JOIN `auth_user` u ON t.`user_id` = u.`id`
            ORDER BY t.`created` DESC
        """)
        
        tokens = cursor.fetchall()
        
        print(f"📊 Tokens trouvés en base: {len(tokens)}")
        
        for key, email, is_active, created in tokens:
            print(f"  🔑 {email}: {key[:20]}...")
            print(f"     Actif: {'Oui' if is_active else 'Non'}")
            print(f"     Créé: {created}")
        
        connection.close()
        return tokens
        
    except Exception as e:
        print(f"❌ Erreur base de données: {e}")
        return []

def test_token_formats():
    """Tester différents formats de tokens"""
    print(f"\n🧪 TEST DE DIFFÉRENTS FORMATS DE TOKENS")
    print("=" * 60)
    
    token = "65VjgtKRTHIiH39fnp5WOL7GLGohjT8L3yD5SqXb"
    base_url = "https://resumecours.gestionhospitaliare.site/api/auth/user/"
    
    formats = [
        f'Token {token}',
        f'Bearer {token}',
        f'JWT {token}',
        token,  # Sans préfixe
    ]
    
    for auth_format in formats:
        print(f"\n🔍 Test format: '{auth_format[:30]}...'")
        
        headers = {
            'Authorization': auth_format,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        try:
            response = requests.get(base_url, headers=headers, timeout=10)
            
            print(f"   📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ Format accepté!")
                data = response.json()
                print(f"   👤 Email: {data.get('email', 'N/A')}")
                return auth_format
            elif response.status_code == 401:
                print(f"   ❌ Format rejeté")
                print(f"   📄 Réponse: {response.text[:100]}")
            else:
                print(f"   ❓ Status inattendu: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
    
    return None

def check_django_auth_config():
    """Vérifier la configuration d'authentification Django"""
    print(f"\n🔧 VÉRIFICATION DE LA CONFIGURATION DJANGO")
    print("=" * 60)
    
    # Tester l'endpoint sans authentification
    try:
        response = requests.get("https://resumecours.gestionhospitaliare.site/api/courses/", timeout=10)
        print(f"📚 Endpoint /courses/ (sans auth): {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✅ Serveur Django fonctionne")
        else:
            print(f"   ❌ Problème serveur Django")
            
    except Exception as e:
        print(f"❌ Erreur serveur: {e}")
    
    # Tester l'endpoint auth sans token
    try:
        response = requests.get("https://resumecours.gestionhospitaliare.site/api/auth/user/", timeout=10)
        print(f"🔐 Endpoint /auth/user/ (sans token): {response.status_code}")
        
        if response.status_code == 401:
            print(f"   ✅ Authentification requise (normal)")
            print(f"   📄 Message: {response.text}")
        else:
            print(f"   ❓ Status inattendu: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur auth endpoint: {e}")

def test_middleware_issue():
    """Tester si le problème vient du middleware"""
    print(f"\n🔧 TEST DU MIDDLEWARE D'AUTHENTIFICATION")
    print("=" * 60)
    
    token = "65VjgtKRTHIiH39fnp5WOL7GLGohjT8L3yD5SqXb"
    
    # Test avec différents headers
    test_cases = [
        {
            'name': 'Headers standard',
            'headers': {
                'Authorization': f'Token {token}',
                'Content-Type': 'application/json'
            }
        },
        {
            'name': 'Headers avec User-Agent',
            'headers': {
                'Authorization': f'Token {token}',
                'Content-Type': 'application/json',
                'User-Agent': 'Resume+ Test Client'
            }
        },
        {
            'name': 'Headers avec Accept',
            'headers': {
                'Authorization': f'Token {token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        },
        {
            'name': 'Headers minimaux',
            'headers': {
                'Authorization': f'Token {token}'
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🔍 {test_case['name']}:")
        
        try:
            response = requests.get(
                "https://resumecours.gestionhospitaliare.site/api/auth/user/",
                headers=test_case['headers'],
                timeout=10
            )
            
            print(f"   📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ Succès!")
                return test_case['headers']
            else:
                print(f"   📄 Réponse: {response.text[:100]}")
                
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
    
    return None

def check_server_logs():
    """Suggestions pour vérifier les logs serveur"""
    print(f"\n📋 VÉRIFICATION DES LOGS SERVEUR")
    print("=" * 60)
    
    print("Pour diagnostiquer le problème, vérifiez ces logs sur le serveur:")
    print()
    print("1. Logs Django:")
    print("   tail -f /home/jey/resumecours.gestionhospitaliare.site/backend/django.log")
    print()
    print("2. Logs Gunicorn:")
    print("   sudo journalctl -u gunicorn -f")
    print()
    print("3. Logs Apache:")
    print("   sudo tail -f /var/log/httpd/error_log")
    print()
    print("4. Redémarrer les services:")
    print("   sudo systemctl restart gunicorn")
    print("   sudo systemctl restart httpd")

def main():
    """Fonction principale de debug"""
    print("🔍 DEBUG COMPLET DU PROBLÈME DE TOKENS")
    print("=" * 80)
    
    # 1. Vérifier les tokens en base
    tokens = check_tokens_in_database()
    
    if not tokens:
        print("\n❌ Aucun token trouvé en base - Le problème est là!")
        return
    
    # 2. Tester différents formats
    working_format = test_token_formats()
    
    if working_format:
        print(f"\n✅ Format fonctionnel trouvé: {working_format}")
    else:
        print(f"\n❌ Aucun format de token ne fonctionne")
    
    # 3. Vérifier la config Django
    check_django_auth_config()
    
    # 4. Tester le middleware
    working_headers = test_middleware_issue()
    
    if working_headers:
        print(f"\n✅ Headers fonctionnels trouvés!")
    else:
        print(f"\n❌ Aucun header ne fonctionne")
    
    # 5. Suggestions pour les logs
    check_server_logs()
    
    # Conclusion
    print(f"\n" + "=" * 80)
    print("🎯 DIAGNOSTIC")
    print("=" * 80)
    
    if tokens and not working_format:
        print("❌ PROBLÈME IDENTIFIÉ:")
        print("   - Les tokens existent en base de données")
        print("   - Mais Django REST Framework ne les reconnaît pas")
        print("   - Problème probable: Configuration d'authentification")
        print()
        print("💡 SOLUTIONS À ESSAYER:")
        print("1. Vérifiez que 'rest_framework.authtoken' est dans INSTALLED_APPS")
        print("2. Vérifiez que TokenAuthentication est dans REST_FRAMEWORK settings")
        print("3. Redémarrez Gunicorn: sudo systemctl restart gunicorn")
        print("4. Vérifiez les logs serveur pour plus de détails")
    elif not tokens:
        print("❌ PROBLÈME: Aucun token en base de données")
        print("💡 SOLUTION: Recréez les tokens avec create_token_table.py")
    else:
        print("✅ Les tokens semblent fonctionner")

if __name__ == '__main__':
    main()