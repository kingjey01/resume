import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')
django.setup()

from django.contrib.auth.models import User

try:
    u = User.objects.get(username='cp_info')
    print(f'User: {u.username}')
    print(f'Has profile: {hasattr(u, "profile")}')
    if hasattr(u, 'profile'):
        print(f'Universite: {u.profile.universite}')
        print(f'Promotion: {u.profile.promotion}')
        print(f'Filiere: {u.profile.filiere}')
        print(f'Groupe: {u.profile.groupe}')
    else:
        print('No profile found!')
except User.DoesNotExist:
    print('User cp_info not found')
