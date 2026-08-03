#!/usr/bin/env python3
"""
Test rapide du serveur sans configuration Django complexe
"""

import requests
import pymysql
import secrets
import string
from datetime import datetime

def generate_token():
    """Générer un token aléatoire"""
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(40))

def create_tokens_direct_mysql():
    """Créer des tokens directement via MySQL"""
    print("🔑 CRÉATION DE TOKENS VIA MYSQL DIRECT")
    print("=" * 50)
    
    try:
        # Connexion MySQL directe
        connection = pymysql.connect(
            host='localhost',
            user='jey_resume',
            password='1234',
            database='jey_resume',
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        # Récupérer les utilisateurs de test
        cursor.execute("""
            SELECT id, email, username, is_active 
            FROM auth_user 
            WHERE email IN ('cp@test.com', 'etudiant@test.com', 'admin@test.com')
        """)
        
        users = cursor.fetchall()
        print(f"👥 Utilisateurs trouvés: {len(users)}")
        
        created_tokens = []
        
        for user_id, email, username, is_active in users:
            if not is_active:
                print(f"  ⚠️ {email}: Utilisateur inactif")
                continue
            
            # Supprimer l'ancien token s'il existe
            cursor.execute("DELETE FROM authtoken_token WHERE user_id = %s", (user_id,))
            
            # Créer un nouveau token
            new_token = generate_token()
            cursor.execute("""
                INSERT INTO authtoken_token (key, created, user_id) 
                VALUES (%s, %s, %s)
            """, (new_token, datetime.now(), user_id))
            
            created_tokens.append({
                'email': email,
                'token': new_token,
                'user_id': user_id
            })
            
            print(f"  ✅ {email}: {new_token}")
        
        connection.commit()
        connection.close()
        
        return created_tokens
        
    except Exception as e:
        print(f"❌ Erreur MySQL: {e}")
        return []

def test_tokens_quickly(tokens):
    """Tester rapidement les tokens créés"""
    print(f"\n🧪 TEST RAPIDE DES TOKENS")
    print("=" * 50)
    
    base_url = "https://resumecours.gestionhospitaliare.site/api"
    
    for token_info in tokens:
        email = token_info['email']
        token = token_info['token']
        
        print(f"\n🔍 Test {email}:")
        
        headers = {
            'Authorization': f'Token {token}',
            'Content-Type': 'application/json'
        }
        
        try:
            # Test endpoint user
            response = requests.get(f"{base_url}/auth/user/", headers=headers, timeout=10)
            
            if response.status_code == 200:
                print(f"  ✅ Auth réussie: {response.status_code}")
                try:
                    data = response.json()
                    print(f"  👤 Email: {data.get('email', 'N/A')}")
                    print(f"  🆔 ID: {data.get('id', 'N/A')}")
                except:
                    print(f"  📄 Réponse non-JSON")
            elif response.status_code == 401:
                print(f"  ❌ Token rejeté: {response.status_code}")
                print(f"  📄 Réponse: {response.text[:100]}")
            else:
                print(f"  ❓ Status: {response.status_code}")
            
            # Test sessions audio si auth OK
            if response.status_code == 200:
                audio_response = requests.get(f"{base_url}/courses/sessions/audio/", headers=headers, timeout=10)
                if audio_response.status_code == 200:
                    audio_data = audio_response.json()
                    sessions_count = len(audio_data.get('sessions', []))
                    print(f"  🎵 Sessions audio: {sessions_count}")
                else:
                    print(f"  🎵 Sessions audio: {audio_response.status_code}")
                    
        except Exception as e:
            print(f"  ❌ Erreur: {e}")

def test_server_basic():
    """Test de base du serveur"""
    print(f"\n🌐 TEST DE BASE DU SERVEUR")
    print("=" * 50)
    
    base_url = "https://resumecours.gestionhospitaliare.site/api"
    
    endpoints = [
        "/courses/",
        "/auth/user/",
        "/courses/sessions/",
    ]
    
    for endpoint in endpoints:
        try:
            url = base_url + endpoint
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                print(f"  ✅ {endpoint}: OK ({response.status_code})")
            elif response.status_code == 401:
                print(f"  🔐 {endpoint}: Auth requise ({response.status_code})")
            else:
                print(f"  ❓ {endpoint}: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ {endpoint}: {e}")

def check_database_users():
    """Vérifier les utilisateurs en base"""
    print(f"\n👥 VÉRIFICATION DES UTILISATEURS EN BASE")
    print("=" * 50)
    
    try:
        connection = pymysql.connect(
            host='localhost',
            user='jey_resume',
            password='1234',
            database='jey_resume',
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        # Compter les utilisateurs
        cursor.execute("SELECT COUNT(*) FROM auth_user")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM auth_user WHERE is_active = 1")
        active_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM authtoken_token")
        total_tokens = cursor.fetchone()[0]
        
        print(f"📊 Statistiques:")
        print(f"  Utilisateurs total: {total_users}")
        print(f"  Utilisateurs actifs: {active_users}")
        print(f"  Tokens existants: {total_tokens}")
        
        # Lister les utilisateurs de test
        cursor.execute("""
            SELECT u.id, u.email, u.username, u.is_active, t.key
            FROM auth_user u
            LEFT JOIN authtoken_token t ON u.id = t.user_id
            WHERE u.email IN ('cp@test.com', 'etudiant@test.com', 'admin@test.com')
        """)
        
        test_users = cursor.fetchall()
        
        print(f"\n👤 Utilisateurs de test:")
        for user_id, email, username, is_active, token in test_users:
            status = "✅" if is_active else "❌"
            token_status = "🔑" if token else "❌"
            print(f"  {status} {email} ({username})")
            print(f"    Token: {token_status} {token[:10] + '...' if token else 'Aucun'}")
        
        connection.close()
        return len(test_users)
        
    except Exception as e:
        print(f"❌ Erreur base de données: {e}")
        return 0

def generate_curl_commands(tokens):
    """Générer des commandes curl pour tester"""
    print(f"\n📋 COMMANDES CURL POUR TESTER")
    print("=" * 50)
    
    if not tokens:
        print("❌ Aucun token disponible")
        return
    
    for token_info in tokens[:2]:  # Afficher 2 exemples
        email = token_info['email']
        token = token_info['token']
        
        print(f"\n# Test {email}:")
        print(f"curl -H 'Authorization: Token {token}' \\")
        print(f"     https://resumecours.gestionhospitaliare.site/api/auth/user/")
        
        print(f"\n# Test sessions audio {email}:")
        print(f"curl -H 'Authorization: Token {token}' \\")
        print(f"     https://resumecours.gestionhospitaliare.site/api/courses/sessions/audio/")

def main():
    """Fonction principale de test rapide"""
    print("🚀 TEST RAPIDE DU SERVEUR - SANS DJANGO")
    print("=" * 80)
    
    try:
        # 1. Test de base du serveur
        test_server_basic()
        
        # 2. Vérifier les utilisateurs en base
        users_count = check_database_users()
        
        if users_count == 0:
            print("\n❌ Aucun utilisateur de test trouvé")
            print("💡 Exécutez d'abord: python create_test_data.py")
            return
        
        # 3. Créer des tokens directement via MySQL
        tokens = create_tokens_direct_mysql()
        
        if not tokens:
            print("\n❌ Impossible de créer les tokens")
            return
        
        # 4. Tester les tokens
        test_tokens_quickly(tokens)
        
        # 5. Générer les commandes curl
        generate_curl_commands(tokens)
        
        # Résumé final
        print(f"\n" + "=" * 80)
        print("📊 RÉSUMÉ DU TEST RAPIDE")
        print("=" * 80)
        
        print(f"🔑 Tokens créés: {len(tokens)}")
        
        if tokens:
            print(f"\n🎯 TOKENS POUR FLUTTER:")
            for token_info in tokens:
                print(f"  {token_info['email']}: {token_info['token']}")
        
        print(f"\n💡 PROCHAINES ÉTAPES:")
        print(f"1. Copiez les tokens ci-dessus dans votre app Flutter")
        print(f"2. Testez avec les commandes curl affichées")
        print(f"3. Redémarrez le serveur si nécessaire:")
        print(f"   sudo systemctl restart gunicorn")
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()