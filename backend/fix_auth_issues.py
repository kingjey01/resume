#!/usr/bin/env python3
"""
Script pour corriger les problèmes d'authentification en production
"""

import os
import sys
import pymysql
from pathlib import Path

# Installer PyMySQL comme MySQLdb (comme dans votre config)
pymysql.install_as_MySQLdb()

# Ajouter le répertoire du projet au path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Configuration Django avec votre configuration MySQL existante
import django.conf

try:
    from decouple import config
except ImportError:
    print("⚠️ python-decouple non installé, utilisation des valeurs par défaut")
    def config(key, default=None):
        return os.environ.get(key, default)

# Configuration directe avec vos paramètres
django.conf.settings.configure(
    DEBUG=True,
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': config('DB_NAME', default='jey_resume'),
            'USER': config('DB_USER', default='jey_resume'),
            'PASSWORD': config('DB_PASSWORD', default='1234'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='3306'),
            'OPTIONS': {
                'charset': 'utf8mb4',
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            }
        }
    },
    INSTALLED_APPS=[
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'rest_framework',
        'rest_framework.authtoken',
        'courses',
        'users',
    ],
    USE_TZ=True,
    SECRET_KEY='temp-key-for-auth-fix',
    DEFAULT_AUTO_FIELD='django.db.models.BigAutoField'
)

import django
django.setup()

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from users.models import UserProfile

def create_missing_tokens():
    """Créer des tokens pour tous les utilisateurs qui n'en ont pas"""
    print("🔑 Création des tokens manquants")
    print("=" * 50)
    
    try:
        # Récupérer tous les utilisateurs actifs sans token
        users_without_token = User.objects.filter(
            is_active=True,
            auth_token__isnull=True
        )
        
        print(f"👥 Utilisateurs sans token: {users_without_token.count()}")
        
        created_count = 0
        for user in users_without_token:
            try:
                token = Token.objects.create(user=user)
                print(f"  ✅ Token créé pour {user.email}: {token.key}")
                created_count += 1
            except Exception as e:
                print(f"  ❌ Erreur pour {user.email}: {e}")
        
        print(f"\n🎯 {created_count} tokens créés")
        return created_count
        
    except Exception as e:
        print(f"❌ Erreur création tokens: {e}")
        return 0

def fix_test_users():
    """Corriger et créer les utilisateurs de test avec leurs tokens"""
    print("\n👤 Correction des utilisateurs de test")
    print("=" * 50)
    
    test_users_data = [
        {
            'email': 'cp@test.com',
            'username': 'cp_test',
            'first_name': 'CP',
            'last_name': 'Test',
            'password': 'TestCP123!',
            'groupe': 'CP'
        },
        {
            'email': 'etudiant@test.com',
            'username': 'etudiant_test',
            'first_name': 'Étudiant',
            'last_name': 'Test',
            'password': 'TestEtudiant123!',
            'groupe': 'ETUDIANT'
        },
        {
            'email': 'admin@test.com',
            'username': 'admin_test',
            'first_name': 'Admin',
            'last_name': 'Test',
            'password': 'AdminTest123!',
            'is_staff': True,
            'is_superuser': True,
            'groupe': 'ADMIN'
        }
    ]
    
    created_users = []
    
    for user_data in test_users_data:
        try:
            # Créer ou récupérer l'utilisateur
            user, created = User.objects.get_or_create(
                email=user_data['email'],
                defaults={
                    'username': user_data['username'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'is_staff': user_data.get('is_staff', False),
                    'is_superuser': user_data.get('is_superuser', False),
                    'is_active': True
                }
            )
            
            if created:
                user.set_password(user_data['password'])
                user.save()
                print(f"  ✅ Utilisateur créé: {user.email}")
            else:
                print(f"  ℹ️ Utilisateur existe: {user.email}")
            
            # Créer ou récupérer le token
            token, token_created = Token.objects.get_or_create(user=user)
            if token_created:
                print(f"    🔑 Token créé: {token.key}")
            else:
                print(f"    🔑 Token existe: {token.key}")
            
            # Créer ou mettre à jour le profil
            try:
                from courses.models import Universite, Filiere, Promotion
                
                profile, profile_created = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'groupe': user_data['groupe'],
                        'universite': Universite.objects.first(),
                        'filiere': Filiere.objects.first(),
                        'promotion': Promotion.objects.first()
                    }
                )
                
                if profile_created:
                    print(f"    👤 Profil créé: {user_data['groupe']}")
                else:
                    print(f"    👤 Profil existe: {profile.groupe}")
                    
            except Exception as e:
                print(f"    ⚠️ Erreur profil: {e}")
            
            created_users.append({
                'user': user,
                'token': token.key,
                'email': user.email,
                'groupe': user_data['groupe']
            })
            
        except Exception as e:
            print(f"  ❌ Erreur utilisateur {user_data['email']}: {e}")
    
    return created_users

def test_tokens_validity():
    """Tester la validité des tokens créés"""
    print("\n🧪 Test de validité des tokens")
    print("=" * 50)
    
    try:
        import requests
        
        base_url = "https://resumecours.gestionhospitaliare.site"
        test_endpoint = "/api/auth/user/"
        
        # Récupérer quelques tokens de test
        test_users = User.objects.filter(
            email__in=['cp@test.com', 'etudiant@test.com', 'admin@test.com']
        )
        
        valid_tokens = []
        
        for user in test_users:
            try:
                token = Token.objects.get(user=user)
                
                # Tester le token
                headers = {
                    'Authorization': f'Token {token.key}',
                    'Content-Type': 'application/json'
                }
                
                response = requests.get(
                    base_url + test_endpoint,
                    headers=headers,
                    timeout=10
                )
                
                print(f"  🔑 {user.email}: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"    ✅ Token valide")
                    try:
                        data = response.json()
                        print(f"    👤 Utilisateur: {data.get('email', 'N/A')}")
                    except:
                        pass
                    valid_tokens.append(token.key)
                    
                elif response.status_code == 401:
                    print(f"    ❌ Token invalide")
                    print(f"    📄 Réponse: {response.text[:100]}")
                else:
                    print(f"    ❓ Status inattendu: {response.status_code}")
                    
            except Token.DoesNotExist:
                print(f"  ❌ {user.email}: Pas de token")
            except Exception as e:
                print(f"  ❌ {user.email}: Erreur - {e}")
        
        return valid_tokens
        
    except Exception as e:
        print(f"❌ Erreur test tokens: {e}")
        return []

def check_cors_configuration():
    """Vérifier et afficher la configuration CORS"""
    print("\n🌐 Vérification de la configuration CORS")
    print("=" * 50)
    
    try:
        from django.conf import settings
        
        # CORS settings
        cors_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', [])
        cors_credentials = getattr(settings, 'CORS_ALLOW_CREDENTIALS', False)
        cors_headers = getattr(settings, 'CORS_ALLOW_HEADERS', [])
        
        print(f"📋 Configuration CORS actuelle:")
        print(f"  Origins autorisées: {cors_origins}")
        print(f"  Credentials autorisés: {cors_credentials}")
        print(f"  Headers autorisés: {len(cors_headers)} headers")
        
        # Vérifications
        flutter_origins = [
            'http://localhost:3000',
            'http://127.0.0.1:3000',
            'https://resumecours.gestionhospitaliare.site'
        ]
        
        missing_origins = []
        for origin in flutter_origins:
            if origin not in cors_origins:
                missing_origins.append(origin)
        
        if missing_origins:
            print(f"\n⚠️ Origins manquantes pour Flutter:")
            for origin in missing_origins:
                print(f"  - {origin}")
        else:
            print(f"\n✅ Toutes les origins Flutter sont configurées")
        
        if not cors_credentials:
            print(f"\n⚠️ CORS_ALLOW_CREDENTIALS devrait être True pour l'auth")
        
        return len(missing_origins) == 0 and cors_credentials
        
    except Exception as e:
        print(f"❌ Erreur CORS: {e}")
        return False

def generate_flutter_auth_config():
    """Générer la configuration d'authentification pour Flutter"""
    print("\n📱 Génération de la config Flutter")
    print("=" * 50)
    
    try:
        # Récupérer les tokens de test
        test_users = User.objects.filter(
            email__in=['cp@test.com', 'etudiant@test.com', 'admin@test.com']
        )
        
        flutter_config = {
            'base_url': 'https://resumecours.gestionhospitaliare.site/api',
            'auth_endpoint': '/auth/user/',
            'test_tokens': {}
        }
        
        for user in test_users:
            try:
                token = Token.objects.get(user=user)
                flutter_config['test_tokens'][user.email] = {
                    'token': token.key,
                    'user_id': user.id,
                    'username': user.username,
                    'groupe': getattr(user.userprofile, 'groupe', 'N/A') if hasattr(user, 'userprofile') else 'N/A'
                }
            except Token.DoesNotExist:
                pass
        
        # Sauvegarder la config
        import json
        config_file = BASE_DIR / "flutter_auth_config.json"
        with open(config_file, 'w') as f:
            json.dump(flutter_config, f, indent=2)
        
        print(f"  ✅ Configuration sauvegardée: {config_file}")
        
        # Afficher les tokens pour Flutter
        print(f"\n🔑 Tokens pour Flutter:")
        for email, config in flutter_config['test_tokens'].items():
            print(f"  {email}:")
            print(f"    Token: {config['token']}")
            print(f"    Groupe: {config['groupe']}")
        
        return flutter_config
        
    except Exception as e:
        print(f"❌ Erreur config Flutter: {e}")
        return None

def main():
    """Fonction principale de correction"""
    print("🔧 CORRECTION DES PROBLÈMES D'AUTHENTIFICATION")
    print("=" * 80)
    
    try:
        # 1. Créer les tokens manquants
        tokens_created = create_missing_tokens()
        
        # 2. Corriger les utilisateurs de test
        test_users = fix_test_users()
        
        # 3. Tester la validité des tokens
        valid_tokens = test_tokens_validity()
        
        # 4. Vérifier CORS
        cors_ok = check_cors_configuration()
        
        # 5. Générer la config Flutter
        flutter_config = generate_flutter_auth_config()
        
        # Résumé final
        print("\n" + "=" * 80)
        print("📊 RÉSUMÉ DE LA CORRECTION")
        print("=" * 80)
        
        print(f"🔑 Tokens créés: {tokens_created}")
        print(f"👤 Utilisateurs de test: {len(test_users)}")
        print(f"✅ Tokens valides: {len(valid_tokens)}")
        print(f"🌐 CORS configuré: {'Oui' if cors_ok else 'Non'}")
        
        if test_users:
            print(f"\n🔑 TOKENS DE TEST POUR FLUTTER:")
            for user_info in test_users:
                print(f"  {user_info['email']} ({user_info['groupe']}): {user_info['token']}")
        
        print(f"\n🧪 COMMANDES DE TEST:")
        if valid_tokens:
            token = valid_tokens[0]
            print(f"  # Test avec curl:")
            print(f"  curl -H 'Authorization: Token {token}' \\")
            print(f"       https://resumecours.gestionhospitaliare.site/api/auth/user/")
            
            print(f"\n  # Test sessions audio:")
            print(f"  curl -H 'Authorization: Token {token}' \\")
            print(f"       https://resumecours.gestionhospitaliare.site/api/courses/sessions/audio/")
        
        print(f"\n💡 PROCHAINES ÉTAPES:")
        print(f"1. Redémarrez le serveur: sudo systemctl restart gunicorn")
        print(f"2. Testez avec: python debug_auth_headers.py")
        print(f"3. Utilisez les tokens dans votre app Flutter")
        print(f"4. Vérifiez la config CORS si nécessaire")
        
        if not cors_ok:
            print(f"\n⚠️ ATTENTION: Configuration CORS à corriger")
            print(f"   Ajoutez dans settings.py:")
            print(f"   CORS_ALLOW_CREDENTIALS = True")
            print(f"   CORS_ALLOWED_ORIGINS = [")
            print(f"       'http://localhost:3000',")
            print(f"       'https://resumecours.gestionhospitaliare.site'")
            print(f"   ]")
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()