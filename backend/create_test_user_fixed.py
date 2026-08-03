#!/usr/bin/env python3
"""
Créer un utilisateur de test avec token pour les tests API - VERSION CORRIGÉE
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

def create_test_user():
    """Créer un utilisateur de test avec profil et token"""
    
    print("🔧 Création d'un utilisateur de test...")
    
    # Créer ou récupérer l'utilisateur
    username = "test_student"
    email = "test@example.com"
    password = "testpass123"
    
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': email,
            'first_name': 'Test',
            'last_name': 'Student'
        }
    )
    
    if created:
        user.set_password(password)
        user.save()
        print(f"✅ Utilisateur créé: {username}")
    else:
        print(f"✅ Utilisateur existant: {username}")
    
    # Créer ou récupérer le profil avec les bons champs
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            'groupe': 'ETUDIANT',  # Utiliser 'groupe' au lieu de 'role'
            'phone': '+33123456789',
            'points': 0
        }
    )
    
    if created:
        print(f"✅ Profil créé: {profile.groupe}")
    else:
        print(f"✅ Profil existant: {profile.groupe}")
    
    # Créer ou récupérer le token
    token, created = Token.objects.get_or_create(user=user)
    
    if created:
        print(f"✅ Token créé: {token.key}")
    else:
        print(f"✅ Token existant: {token.key}")
    
    print("\n" + "="*50)
    print("🎯 INFORMATIONS DE TEST - ÉTUDIANT")
    print("="*50)
    print(f"Username: {user.username}")
    print(f"Email: {user.email}")
    print(f"Password: {password}")
    print(f"Groupe: {profile.groupe}")
    print(f"Token: {token.key}")
    print("="*50)
    
    return {
        'user': user,
        'profile': profile,
        'token': token.key,
        'username': username,
        'password': password
    }

def create_admin_user():
    """Créer un utilisateur admin pour les tests avancés"""
    
    print("\n🔧 Création d'un utilisateur admin...")
    
    username = "test_admin"
    email = "admin@example.com"
    password = "adminpass123"
    
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': email,
            'first_name': 'Test',
            'last_name': 'Admin',
            'is_staff': True,
            'is_superuser': True
        }
    )
    
    if created:
        user.set_password(password)
        user.save()
        print(f"✅ Admin créé: {username}")
    else:
        print(f"✅ Admin existant: {username}")
    
    # Créer le profil admin avec les bons champs
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            'groupe': 'ADMIN',  # Utiliser 'ADMIN' au lieu de 'admin'
            'phone': '+33987654321',
            'points': 1000
        }
    )
    
    if created:
        print(f"✅ Profil admin créé: {profile.groupe}")
    else:
        print(f"✅ Profil admin existant: {profile.groupe}")
    
    # Créer le token
    token, created = Token.objects.get_or_create(user=user)
    
    print(f"✅ Token Admin: {token.key}")
    
    print("\n" + "="*50)
    print("🎯 INFORMATIONS DE TEST - ADMIN")
    print("="*50)
    print(f"Username: {user.username}")
    print(f"Email: {user.email}")
    print(f"Password: {password}")
    print(f"Groupe: {profile.groupe}")
    print(f"Token: {token.key}")
    print("="*50)
    
    return {
        'user': user,
        'profile': profile,
        'token': token.key,
        'username': username,
        'password': password
    }

def create_cp_user():
    """Créer un utilisateur CP (Chef de Promotion)"""
    
    print("\n🔧 Création d'un utilisateur CP...")
    
    username = "test_cp"
    email = "cp@example.com"
    password = "cppass123"
    
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': email,
            'first_name': 'Test',
            'last_name': 'CP'
        }
    )
    
    if created:
        user.set_password(password)
        user.save()
        print(f"✅ CP créé: {username}")
    else:
        print(f"✅ CP existant: {username}")
    
    # Créer le profil CP
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            'groupe': 'CP',
            'phone': '+33555666777',
            'points': 500
        }
    )
    
    # Créer le token
    token, created = Token.objects.get_or_create(user=user)
    
    print(f"✅ Token CP: {token.key}")
    
    print("\n" + "="*50)
    print("🎯 INFORMATIONS DE TEST - CP")
    print("="*50)
    print(f"Username: {user.username}")
    print(f"Email: {user.email}")
    print(f"Password: {password}")
    print(f"Groupe: {profile.groupe}")
    print(f"Token: {token.key}")
    print("="*50)
    
    return {
        'user': user,
        'profile': profile,
        'token': token.key,
        'username': username,
        'password': password
    }

if __name__ == "__main__":
    print("🚀 Création des utilisateurs de test avec les bons champs...")
    
    try:
        # Créer utilisateur étudiant
        student_info = create_test_user()
        
        # Créer utilisateur CP
        cp_info = create_cp_user()
        
        # Créer utilisateur admin
        admin_info = create_admin_user()
        
        print("\n🎉 SUCCÈS ! Tous les utilisateurs créés.")
        print("\n📝 TOKENS À UTILISER POUR LES TESTS:")
        print("="*60)
        print(f"ÉTUDIANT Token: {student_info['token']}")
        print(f"CP Token:       {cp_info['token']}")
        print(f"ADMIN Token:    {admin_info['token']}")
        print("="*60)
        
        print("\n🔍 PERMISSIONS ATTENDUES:")
        print("- ÉTUDIANT: Peut voir summaries gratuits seulement")
        print("- CP: Peut créer et voir tous les summaries")
        print("- ADMIN: Accès complet à tout")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()