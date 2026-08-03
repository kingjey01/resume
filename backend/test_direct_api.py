#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')
django.setup()

from payments.models import Service, Abonnement
from payments.views import ServiceListCreateView, AbonnementListCreateView
from rest_framework.test import APIRequestFactory, force_authenticate
from django.contrib.auth.models import User
from rest_framework.response import Response

def test_direct_api():
    """Test API views directly without HTTP requests"""
    
    print("=== Direct API View Test ===")
    
    # Get user
    user = User.objects.get(username='jey')
    print(f"Testing with user: {user} (staff: {user.is_staff})")
    
    # Create request factory
    factory = APIRequestFactory()
    
    # Test ServiceListCreateView directly
    print("\n--- Testing ServiceListCreateView ---")
    request = factory.get('/api/services/')
    request.user = user  # Set user directly
    force_authenticate(request, user=user)
    
    view = ServiceListCreateView()
    view.setup(request)
    
    # Call the list method directly
    response = view.list(request)
    print(f"Response status: {response.status_code}")
    print(f"Response data: {response.data}")
    print(f"Response data type: {type(response.data)}")
    print(f"Response data length: {len(response.data)}")
    
    # Test AbonnementListCreateView directly
    print("\n--- Testing AbonnementListCreateView ---")
    request2 = factory.get('/api/abonnements/')
    request2.user = user  # Set user directly
    force_authenticate(request2, user=user)
    
    view2 = AbonnementListCreateView()
    view2.setup(request2)
    
    # Call the list method directly
    response2 = view2.list(request2)
    print(f"Response status: {response2.status_code}")
    print(f"Response data: {response2.data}")
    print(f"Response data type: {type(response2.data)}")
    print(f"Response data length: {len(response2.data)}")

if __name__ == "__main__":
    test_direct_api()
