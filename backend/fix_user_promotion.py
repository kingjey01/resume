import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')
django.setup()

from django.contrib.auth.models import User
from courses.models import Promotion

try:
    u = User.objects.get(username='cp_info')
    profile = u.profile
    
    print(f'User: {u.username}')
    print(f'Current promotion: {profile.promotion}')
    
    # Trouver la promotion L1
    l1_promo = Promotion.objects.get(nom='L1')
    print(f'Target promotion: {l1_promo}')
    
    # Mettre à jour
    profile.promotion = l1_promo
    profile.save()
    
    print(f'\n[OK] Promotion updated successfully!')
    print(f'New promotion: {profile.promotion}')
    
except User.DoesNotExist:
    print('User cp_info not found')
except Promotion.DoesNotExist:
    print('Promotion L1 not found')
