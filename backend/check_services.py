#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')
django.setup()

from payments.models import Service, Abonnement
from django.contrib.auth.models import User

def check_services():
    print("=== Vérification des Services ===")
    services = Service.objects.all()
    print(f"Nombre de services: {services.count()}")
    
    for service in services:
        print(f"  - {service.nom}: {service.price} {service.currency} ({service.type})")
    
    print("\n=== Vérification des Abonnements ===")
    abonnements = Abonnement.objects.all()
    print(f"Nombre d'abonnements: {abonnements.count()}")
    
    for abonnement in abonnements:
        print(f"  - {abonnement.user.username} -> {abonnement.service.nom} ({abonnement.status})")
    
    print("\n=== Test API Response Format ===")
    from payments.serializers import ServiceSerializer, AbonnementSerializer
    
    # Test services serialization
    services_data = ServiceSerializer(services, many=True).data
    print(f"Services data type: {type(services_data)}")
    print(f"Services data: {services_data}")
    
    # Test abonnements serialization
    abonnements_data = AbonnementSerializer(abonnements, many=True).data
    print(f"Abonnements data type: {type(abonnements_data)}")
    print(f"Abonnements data: {abonnements_data}")

if __name__ == "__main__":
    check_services()
