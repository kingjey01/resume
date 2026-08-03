import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')
django.setup()

from django.contrib.auth.models import User
from courses.models import Course

try:
    u = User.objects.get(username='cp_info')
    profile = u.profile
    
    print('USER PROFILE:')
    print(f'  Universite: {profile.universite} (ID: {profile.universite.id if profile.universite else None})')
    print(f'  Promotion: {profile.promotion} (ID: {profile.promotion.id if profile.promotion else None})')
    print(f'  Filiere: {profile.filiere} (ID: {profile.filiere.id if profile.filiere else None})')
    print()
    
    print('FIRST 3 COURSES:')
    for c in Course.objects.all()[:3]:
        print(f'\nCourse: {c.nom}')
        print(f'  universite_fk: {c.universite_fk} (ID: {c.universite_fk.id if c.universite_fk else None})')
        print(f'  promotion_fk: {c.promotion_fk} (ID: {c.promotion_fk.id if c.promotion_fk else None})')
        print(f'  filiere_fk: {c.filiere_fk} (ID: {c.filiere_fk.id if c.filiere_fk else None})')
        
        # Check matches
        univ_match = c.universite_fk == profile.universite if c.universite_fk and profile.universite else False
        promo_match = c.promotion_fk == profile.promotion if c.promotion_fk and profile.promotion else False
        fil_match = c.filiere_fk == profile.filiere if c.filiere_fk and profile.filiere else False
        
        print(f'  Matches: Univ={univ_match}, Promo={promo_match}, Fil={fil_match}')
            
except User.DoesNotExist:
    print('User cp_info not found')
