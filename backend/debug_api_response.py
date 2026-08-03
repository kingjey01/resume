#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')
django.setup()

from payments.models import Service, Abonnement
from payments.serializers import ServiceSerializer, AbonnementSerializer
from django.contrib.auth.models import User

def test_api_responses():
    """Test API responses to debug the format issue"""
    
    print("=== Testing Services Serialization ===")
    
    services = Service.objects.all()
    serializer = ServiceSerializer(services, many=True)
    data = serializer.data
    
    print(f"Services Data Type: {type(data)}")
    print(f"Services Data: {data}")
    print(f"Services Data Length: {len(data)}")
    
    # Convert to list
    list_data = list(data)
    print(f"List Data Type: {type(list_data)}")
    print(f"List Data: {list_data}")
    
    print("\n=== Testing Abonnements Serialization ===")
    
    abonnements = Abonnement.objects.all()
    serializer = AbonnementSerializer(abonnements, many=True)
    data = serializer.data
    
    print(f"Abonnements Data Type: {type(data)}")
    print(f"Abonnements Data: {data}")
    print(f"Abonnements Data Length: {len(data)}")
    
    # Convert to list
    list_data = list(data)
    print(f"List Data Type: {type(list_data)}")
    print(f"List Data: {list_data}")

if __name__ == "__main__":
    test_api_responses()
