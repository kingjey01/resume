#!/usr/bin/env python3
"""
Debug des headers d'authentification
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.test import RequestFactory
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication

def test_different_auth_headers():
    """Test différents formats de headers d'authentification"""
    print("🔍 Test des headers d'authentification...")
    
    # Récupérer un token
    token = Token.objects.filter(user__username='test_admin').first()
    if not token:
        print("❌ Token non trouvé")
        return
    
    print(f"🔑 Token: {token.key[:20]}...")
    
    factory = RequestFactory()
    auth = TokenAuthentication()
    
    # Test 1: Header standard
    print("\n1️⃣ Test header standard:")
    request1 = factory.get('/api/summaries/')
    request1.META['HTTP_AUTHORIZATION'] = f'Token {token.key}'
    
    try:
        result1 = auth.authenticate(request1)
        print(f"   HTTP_AUTHORIZATION: {'✅' if result1 else '❌'}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Test 2: Header en minuscules (comme Nginx peut le faire)
    print("\n2️⃣ Test header minuscules:")
    request2 = factory.get('/api/summaries/')
    request2.META['http_authorization'] = f'Token {token.key}'
    
    try:
        result2 = auth.authenticate(request2)
        print(f"   http_authorization: {'✅' if result2 else '❌'}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Test 3: Header Authorization direct
    print("\n3️⃣ Test Authorization direct:")
    request3 = factory.get('/api/summaries/')
    request3.META['Authorization'] = f'Token {token.key}'
    
    try:
        result3 = auth.authenticate(request3)
        print(f"   Authorization: {'✅' if result3 else '❌'}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Afficher tous les headers disponibles
    print(f"\n📋 Headers disponibles dans request1.META:")
    for key, value in request1.META.items():
        if 'auth' in key.lower() or 'token' in key.lower():
            print(f"   {key}: {value[:50]}...")

def test_wsgi_headers():
    """Test comment les headers arrivent via WSGI"""
    print(f"\n🌐 Test des headers WSGI...")
    
    # Simuler ce que fait un serveur web
    environ = {
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': '/api/summaries/',
        'HTTP_AUTHORIZATION': f'Token {Token.objects.first().key}',
        'HTTP_HOST': 'resumecours.gestionhospitaliare.site',
        'SERVER_NAME': 'resumecours.gestionhospitaliare.site',
        'SERVER_PORT': '443',
        'wsgi.url_scheme': 'https',
    }
    
    factory = RequestFactory()
    request = factory.get('/api/summaries/', **{
        'HTTP_AUTHORIZATION': environ['HTTP_AUTHORIZATION'],
        'HTTP_HOST': environ['HTTP_HOST']
    })
    
    auth = TokenAuthentication()
    try:
        result = auth.authenticate(request)
        print(f"   WSGI simulation: {'✅' if result else '❌'}")
        if result:
            user, token = result
            print(f"   Utilisateur: {user.username}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

if __name__ == "__main__":
    print("🚀 DEBUG DES HEADERS D'AUTHENTIFICATION")
    print("="*50)
    
    test_different_auth_headers()
    test_wsgi_headers()