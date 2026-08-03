#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')
django.setup()

from django.urls import reverse, resolve
from django.test import Client
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken

def test_url_routing():
    """Test URL routing for services and abonnements"""
    
    print("=== URL Routing Test ===")
    
    # Test URL reverse
    try:
        services_url = reverse('service-list-create')
        print(f"Services URL: {services_url}")
    except Exception as e:
        print(f"Services URL reverse error: {e}")
    
    try:
        abonnements_url = reverse('abonnement-list-create')
        print(f"Abonnements URL: {abonnements_url}")
    except Exception as e:
        print(f"Abonnements URL reverse error: {e}")
    
    # Test URL resolve
    try:
        resolver = resolve('/api/services/')
        print(f"Services resolver: {resolver.func.__name__}")
        print(f"Services view class: {resolver.func.cls}")
    except Exception as e:
        print(f"Services resolve error: {e}")
    
    try:
        resolver = resolve('/api/abonnements/')
        print(f"Abonnements resolver: {resolver.func.__name__}")
        print(f"Abonnements view class: {resolver.func.cls}")
    except Exception as e:
        print(f"Abonnements resolve error: {e}")
    
    # Test with Django test client
    print("\n=== Django Test Client ===")
    client = Client()
    
    # Get user and create token
    user = User.objects.get(username='jey')
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    
    # Test services endpoint
    response = client.get('/api/services/', HTTP_AUTHORIZATION=f'Bearer {access_token}')
    print(f"Services response status: {response.status_code}")
    print(f"Services response content: {response.content.decode()}")
    
    # Test abonnements endpoint
    response2 = client.get('/api/abonnements/', HTTP_AUTHORIZATION=f'Bearer {access_token}')
    print(f"Abonnements response status: {response2.status_code}")
    print(f"Abonnements response content: {response2.content.decode()}")

if __name__ == "__main__":
    test_url_routing()
