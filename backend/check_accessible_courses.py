import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')
django.setup()

from django.contrib.auth.models import User
from courses.models import Course

try:
    u = User.objects.get(username='cp_info')
    profile = u.profile
    
    print(f'User: {u.username}')
    print(f'Universite: {profile.universite}')
    print(f'Promotion: {profile.promotion}')
    print(f'Filiere: {profile.filiere}')
    print()
    
    # Tous les cours
    all_courses = Course.objects.all()
    print(f'Total courses in DB: {all_courses.count()}')
    
    # Cours avec relations M2M remplies
    courses_with_rel = Course.objects.exclude(universites=None).exclude(filieres=None).exclude(promotions=None)
    print(f'Courses with M2M filled: {courses_with_rel.count()}')

    # Cours accessibles par cet utilisateur
    accessible_courses = Course.objects.filter(
        universites=profile.universite,
        promotions=profile.promotion,
        filieres=profile.filiere
    )
    print(f'Accessible courses for {u.username}: {accessible_courses.count()}')

    if accessible_courses.exists():
        print('\nAccessible courses:')
        for c in accessible_courses[:5]:
            uni = c.universites.first()
            fil = c.filieres.first()
            print(f'  - {c.nom} ({uni.nom if uni else "?"} / {fil.nom if fil else "?"})')
    else:
        print('\nNo accessible courses found!')
        print('\nChecking promotion match:')
        print(f'User promotion: {profile.promotion} (ID: {profile.promotion.id})')
        print('\nAll courses promotions:')
        for c in courses_with_rel[:5]:
            promo = c.promotions.first()
            print(f'  - {c.nom}: promotion={promo} (ID: {promo.id if promo else None})')
            
except User.DoesNotExist:
    print('User cp_info not found')
