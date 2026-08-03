import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')
django.setup()

from django.contrib.auth.models import User
from courses.models import Universite

try:
    u = User.objects.get(username='cp_info')
    profile = u.profile
    
    print(f'User: {u.username}')
    print(f'Current universite: {profile.universite} (ID: {profile.universite.id})')
    
    # Trouver l'universite UNIKIN (ID 14)
    unikin = Universite.objects.get(id=14)
    print(f'Target universite: {unikin} (ID: {unikin.id})')
    
    # Mettre a jour
    profile.universite = unikin
    profile.save()
    
    print(f'\n[OK] Universite updated successfully!')
    print(f'New universite: {profile.universite} (ID: {profile.universite.id})')
    
except User.DoesNotExist:
    print('User cp_info not found')
except Universite.DoesNotExist:
    print('Universite ID 14 not found')
