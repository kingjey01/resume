#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')
django.setup()

from payments.models import Service, Abonnement
from payments.views import ServiceListCreateView, AbonnementListCreateView
from rest_framework.test import APIRequestFactory
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken

def debug_services_issue():
    """Debug why services are not showing in API"""
    
    print("=== Database Check ===")
    services = Service.objects.all()
    print(f"Total services in DB: {services.count()}")
    
    for service in services:
        print(f"- {service.nom} (ID: {service.id}, Active: {service.is_active})")
    
    print("\n=== Active Services Check ===")
    active_services = Service.objects.filter(is_active=True)
    print(f"Active services: {active_services.count()}")
    
    for service in active_services:
        print(f"- {service.nom} (ID: {service.id})")
    
    print("\n=== API View Test ===")
    # Create test request
    factory = APIRequestFactory()
    user = User.objects.first()
    
    # Generate JWT token
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    
    request = factory.get('/api/services/', HTTP_AUTHORIZATION=f'Bearer {access_token}')
    request.user = user
    
    # Test ServiceListCreateView
    view = ServiceListCreateView()
    view.setup(request)
    
    # Test get_queryset method
    queryset = view.get_queryset()
    print(f"View queryset count: {queryset.count()}")
    
    for service in queryset:
        print(f"- Queryset service: {service.nom}")
    
    # Test serialization
    from payments.serializers import ServiceSerializer
    serializer = ServiceSerializer(queryset, many=True)
    data = serializer.data
    print(f"Serialized data count: {len(data)}")
    print(f"Serialized data: {list(data)}")
    
    print("\n=== Abonnements Check ===")
    abonnements = Abonnement.objects.filter(user=user)
    print(f"User abonnements: {abonnements.count()}")
    
    for abonnement in abonnements:
        print(f"- {abonnement.service.nom} ({abonnement.status})")

if __name__ == "__main__":
    debug_services_issue()
