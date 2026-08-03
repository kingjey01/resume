#!/usr/bin/env python3
"""
Vérifier l'état de la base de données et des services d'authentification
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from users.models import UserProfile
from django.db import connection

def check_database_tables():
    """Vérifier que toutes les tables nécessaires existent"""
    print("🔍 Vérification des tables de base de données...")
    
    with connection.cursor() as cursor:
        # Lister toutes les tables
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = [
            'authtoken_token',  # Table des tokens
            'users_userprofile',  # Table des profils
            'auth_user',  # Table des utilisateurs
        ]
        
        print(f"\n📊 Tables trouvées ({len(tables)} total):")
        for table in sorted(tables):
            if any(req in table for req in required_tables):
                print(f"  ✅ {table}")
            else:
                print(f"  📄 {table}")
        
        print(f"\n🔍 Vérification des tables critiques:")
        for req_table in required_tables:
            if any(req_table in table for table in tables):
                print(f"  ✅ {req_table} - Trouvée")
            else:
                print(f"  ❌ {req_table} - MANQUANTE!")
        
        return tables

def check_tokens():
    """Vérifier les tokens en base"""
    print(f"\n🔑 Vérification des tokens...")
    
    try:
        tokens = Token.objects.all()
        print(f"📊 {tokens.count()} tokens trouvés en base:")
        
        for token in tokens:
            user = token.user
            profile = getattr(user, 'profile', None)
            print(f"  🔑 {token.key[:20]}... → {user.username} ({profile.groupe if profile else 'Pas de profil'})")
        
        return tokens.count() > 0
    except Exception as e:
        print(f"❌ Erreur lors de la vérification des tokens: {e}")
        return False

def check_users():
    """Vérifier les utilisateurs et profils"""
    print(f"\n👥 Vérification des utilisateurs...")
    
    try:
        users = User.objects.all()
        print(f"📊 {users.count()} utilisateurs trouvés:")
        
        for user in users:
            profile = getattr(user, 'profile', None)
            has_token = hasattr(user, 'auth_token')
            print(f"  👤 {user.username} - Profil: {profile.groupe if profile else 'AUCUN'} - Token: {'✅' if has_token else '❌'}")
        
        return users.count() > 0
    except Exception as e:
        print(f"❌ Erreur lors de la vérification des utilisateurs: {e}")
        return False

def test_token_authentication():
    """Tester l'authentification par token directement"""
    print(f"\n🧪 Test d'authentification par token...")
    
    try:
        # Récupérer un token de test
        token = Token.objects.first()
        if not token:
            print("❌ Aucun token trouvé pour le test")
            return False
        
        print(f"🔑 Test avec token: {token.key[:20]}...")
        
        # Simuler une requête avec token
        from rest_framework.test import APIClient
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        
        # Test sur un endpoint simple
        response = client.get('/api/courses/')
        print(f"📡 Réponse /api/courses/ avec token: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ L'authentification par token fonctionne!")
            return True
        else:
            print(f"❌ Échec de l'authentification: {response.status_code}")
            print(f"Contenu: {response.content[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test d'authentification: {e}")
        return False

def check_django_settings():
    """Vérifier la configuration Django"""
    print(f"\n⚙️  Vérification de la configuration Django...")
    
    from django.conf import settings
    
    # Vérifier REST_FRAMEWORK
    rest_config = getattr(settings, 'REST_FRAMEWORK', {})
    auth_classes = rest_config.get('DEFAULT_AUTHENTICATION_CLASSES', [])
    
    print(f"🔧 Classes d'authentification configurées:")
    for auth_class in auth_classes:
        print(f"  📋 {auth_class}")
        if 'TokenAuthentication' in auth_class:
            print(f"    ✅ TokenAuthentication trouvée!")
    
    # Vérifier INSTALLED_APPS
    installed_apps = getattr(settings, 'INSTALLED_APPS', [])
    required_apps = ['rest_framework', 'rest_framework.authtoken']
    
    print(f"\n📦 Applications installées (critiques):")
    for app in required_apps:
        if app in installed_apps:
            print(f"  ✅ {app}")
        else:
            print(f"  ❌ {app} - MANQUANTE!")

def main():
    print("🚀 DIAGNOSTIC COMPLET DE L'AUTHENTIFICATION")
    print("="*60)
    
    # Vérifications
    tables_ok = check_database_tables()
    tokens_ok = check_tokens()
    users_ok = check_users()
    auth_ok = test_token_authentication()
    
    check_django_settings()
    
    print(f"\n{'='*60}")
    print("📋 RÉSUMÉ DU DIAGNOSTIC")
    print('='*60)
    print(f"Tables DB:        {'✅' if tables_ok else '❌'}")
    print(f"Tokens en base:   {'✅' if tokens_ok else '❌'}")
    print(f"Utilisateurs:     {'✅' if users_ok else '❌'}")
    print(f"Auth par token:   {'✅' if auth_ok else '❌'}")
    
    if not auth_ok:
        print(f"\n🔧 ACTIONS RECOMMANDÉES:")
        print("1. Vérifier que 'rest_framework.authtoken' est dans INSTALLED_APPS")
        print("2. Exécuter: python manage.py migrate")
        print("3. Redémarrer gunicorn: sudo systemctl restart gunicorn")

if __name__ == "__main__":
    main()