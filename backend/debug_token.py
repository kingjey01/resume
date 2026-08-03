#!/usr/bin/env python3
"""
Debug des tokens directement sur le serveur
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from courses.views import SummaryListCreateView
from courses.permissions import CanAccessSummary

def test_token_authentication():
    """Test l'authentification par token directement"""
    print("🔍 Test d'authentification par token...")
    
    # Récupérer un token de test
    token = Token.objects.filter(user__username='test_admin').first()
    if not token:
        print("❌ Token admin non trouvé")
        return
    
    print(f"🔑 Token admin: {token.key[:20]}...")
    print(f"👤 Utilisateur: {token.user.username}")
    print(f"📋 Profil: {token.user.profile.groupe}")
    
    # Créer une requête simulée
    factory = RequestFactory()
    request = factory.get('/api/summaries/')
    request.META['HTTP_AUTHORIZATION'] = f'Token {token.key}'
    request.user = AnonymousUser()  # Initialement anonyme
    
    # Tester l'authentification
    auth = TokenAuthentication()
    try:
        user_auth_tuple = auth.authenticate(request)
        if user_auth_tuple:
            user, auth_token = user_auth_tuple
            request.user = user
            print(f"✅ Authentification réussie: {user.username}")
            print(f"📋 Profil utilisateur: {user.profile.groupe}")
        else:
            print("❌ Authentification échouée")
            return
    except Exception as e:
        print(f"❌ Erreur d'authentification: {e}")
        return
    
    # Tester les permissions
    permission = CanAccessSummary()
    view = SummaryListCreateView()
    
    try:
        has_perm = permission.has_permission(request, view)
        print(f"🔐 Permission has_permission: {has_perm}")
        
        if has_perm:
            print("✅ L'utilisateur devrait pouvoir accéder aux summaries!")
        else:
            print("❌ Permission refusée")
            
    except Exception as e:
        print(f"❌ Erreur de permission: {e}")
        import traceback
        traceback.print_exc()

def test_view_directly():
    """Test la vue directement"""
    print("\n🎯 Test de la vue SummaryListCreateView...")
    
    from django.test import Client
    from django.contrib.auth.models import User
    
    # Récupérer l'utilisateur admin
    user = User.objects.filter(username='test_admin').first()
    if not user:
        print("❌ Utilisateur admin non trouvé")
        return
    
    token = Token.objects.filter(user=user).first()
    if not token:
        print("❌ Token admin non trouvé")
        return
    
    # Test avec le client Django
    client = Client()
    response = client.get('/api/summaries/', HTTP_AUTHORIZATION=f'Token {token.key}')
    
    print(f"📡 Réponse directe: {response.status_code}")
    if response.status_code != 200:
        print(f"❌ Contenu: {response.content[:300]}")
    else:
        print("✅ Succès!")

def check_middleware():
    """Vérifier les middlewares"""
    print("\n🔧 Vérification des middlewares...")
    
    from django.conf import settings
    middlewares = settings.MIDDLEWARE
    
    print("📋 Middlewares configurés:")
    for i, middleware in enumerate(middlewares):
        print(f"  {i+1}. {middleware}")
        if 'Auth' in middleware:
            print(f"     ✅ Middleware d'authentification")

if __name__ == "__main__":
    print("🚀 DEBUG COMPLET DES TOKENS")
    print("="*50)
    
    test_token_authentication()
    test_view_directly()
    check_middleware()