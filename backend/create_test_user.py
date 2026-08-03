#!/usr/bin/env python3
"""
Créer un utilisateur de test avec token pour les tests API
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
    
    # Créer ou récupérer le profil
    profile, created = Profile.objects.get_or_create(
        user=user,
        defaults={
            'role': 'student',  # Rôle étudiant
            'phone': '+33123456789',
            'address': 'Test Address'
        }
    )
    
    if created:
        print(f"✅ Profil créé: {profile.role}")
    else:
        print(f"✅ Profil existant: {profile.role}")
    
    # Créer ou récupérer le token
    token, created = Token.objects.get_or_create(user=user)
    
    if created:
        print(f"✅ Token créé: {token.key}")
    else:
        print(f"✅ Token existant: {token.key}")
    
    print("\n" + "="*50)
    print("🎯 INFORMATIONS DE TEST")
    print("="*50)
    print(f"Username: {user.username}")
    print(f"Email: {user.email}")
    print(f"Password: {password}")
    print(f"Role: {profile.role}")
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
    
    # Créer le profil admin
    profile, created = Profile.objects.get_or_create(
        user=user,
        defaults={
            'role': 'admin',
            'phone': '+33987654321',
            'address': 'Admin Address'
        }
    )
    
    # Créer le token
    token, created = Token.objects.get_or_create(user=user)
    
    print(f"✅ Token Admin: {token.key}")
    
    return {
        'user': user,
        'profile': profile,
        'token': token.key,
        'username': username,
        'password': password
    }

if __name__ == "__main__":
    print("🚀 Création des utilisateurs de test...")
    
    try:
        # Créer utilisateur étudiant
        student_info = create_test_user()
        
        # Créer utilisateur admin
        admin_info = create_admin_user()
        
        print("\n🎉 SUCCÈS ! Utilisateurs créés.")
        print("\n📝 Tokens à utiliser pour les tests:")
        print(f"Student Token: {student_info['token']}")
        print(f"Admin Token: {admin_info['token']}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()