#!/usr/bin/env python
import os
import sys
import django
import requests

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')
django.setup()

from django.contrib.auth.models import User
from payments.models import Service, Abonnement

def test_subscription_creation():
    """Test creating a new subscription via API"""
    
    print("=== Test Subscription Creation ===")
    
    # Login first
    login_data = {
        'email': 'jey@example.com',
        'password': 'password123'
    }
    
    login_response = requests.post('http://127.0.0.1:8000/api/auth/login/', json=login_data)
    if login_response.status_code != 200:
        print(f"Login failed: {login_response.status_code}")
        return
    
    tokens = login_response.json()
    access_token = tokens.get('access')
    print(f"Login successful, token obtained")
    
    # Get available services
    services_response = requests.get(
        'http://127.0.0.1:8000/api/services/',
        headers={'Authorization': f'Bearer {access_token}'}
    )
    
    if services_response.status_code != 200:
        print(f"Failed to get services: {services_response.status_code}")
        return
    
    services = services_response.json()
    print(f"Available services: {len(services)}")
    
    if not services:
        print("No services available for testing")
        return
    
    # Test with Premium service (ID 4)
    premium_service = next((s for s in services if s['id'] == 4), None)
    if not premium_service:
        print("Premium service not found")
        return
    
    print(f"Testing subscription to: {premium_service['nom']} (ID: {premium_service['id']})")
    
    # Create subscription data
    subscription_data = {
        'service': premium_service['id'],
        'date_debut': '2025-08-30T20:00:00+02:00',
        'date_fin': '2025-09-30T20:00:00+02:00',
    }
    
    print(f"Subscription data: {subscription_data}")
    
    # Create subscription
    create_response = requests.post(
        'http://127.0.0.1:8000/api/abonnements/',
        json=subscription_data,
        headers={'Authorization': f'Bearer {access_token}'}
    )
    
    print(f"Create subscription status: {create_response.status_code}")
    print(f"Create response: {create_response.text}")
    
    if create_response.status_code == 201:
        subscription = create_response.json()
        print(f"Subscription created successfully!")
        print(f"Subscription ID: {subscription.get('id')}")
        print(f"Service: {subscription.get('service_name')}")
        print(f"Status: {subscription.get('status')}")
        
        # Verify it appears in user's subscriptions
        print("\n=== Verifying subscription appears in list ===")
        list_response = requests.get(
            'http://127.0.0.1:8000/api/abonnements/',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        
        if list_response.status_code == 200:
            user_subscriptions = list_response.json()
            print(f"User now has {len(user_subscriptions)} subscription(s)")
            for sub in user_subscriptions:
                print(f"- {sub.get('service_name')} (Status: {sub.get('status')})")
        else:
            print(f"Failed to get user subscriptions: {list_response.status_code}")
    
    else:
        print(f"Failed to create subscription")
        try:
            error_data = create_response.json()
            print(f"Error details: {error_data}")
        except:
            print(f"Raw error: {create_response.text}")

if __name__ == "__main__":
    test_subscription_creation()
