#!/usr/bin/env python
"""
Script SEED pour remplir la base de données avec des données de test
Usage: python manage.py runscript seed_data
Ou: python manage.py shell < seed_data.py
"""

import os
import sys
import django

# Configuration Django - ajouter le chemin parent
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')

django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from courses.models import (
    Universite, Filiere, Promotion,
    Course, Session, Summary, Service
)
from users.models import UserProfile


def clear_data():
    """Supprime toutes les données existantes"""
    print("[DELETE] Suppression des donnees existantes...")
    Summary.objects.all().delete()
    Session.objects.all().delete()
    Course.objects.all().delete()
    Service.objects.all().delete()
    Promotion.objects.all().delete()
    Filiere.objects.all().delete()
    Universite.objects.all().delete()
    UserProfile.objects.all().delete()
    User.objects.filter(is_superuser=False).delete()
    print("[OK] Donnees supprimees")


def create_promotions():
    """Cree les promotions (L1, L2, L3, M1, M2)"""
    print("[PROMO] Creation des promotions...")
    promotions_data = [
        {'nom': 'L1', 'annee': 2024},
        {'nom': 'L2', 'annee': 2024},
        {'nom': 'L3', 'annee': 2024},
        {'nom': 'M1', 'annee': 2024},
        {'nom': 'M2', 'annee': 2024},
    ]
    promotions = []
    for data in promotions_data:
        promo, created = Promotion.objects.get_or_create(**data)
        promotions.append(promo)
        print(f"  + {promo}")
    return promotions


def create_filieres():
    """Cree les filieres"""
    print("[FILIERE] Creation des filieres...")
    filieres_data = [
        {'nom': 'Informatique', 'description': 'Sciences informatiques et programmation'},
        {'nom': 'Médecine', 'description': 'Sciences médicales et santé'},
        {'nom': 'Droit', 'description': 'Sciences juridiques'},
        {'nom': 'Économie', 'description': 'Sciences économiques et gestion'},
        {'nom': 'Génie Civil', 'description': 'Construction et infrastructures'},
        {'nom': 'Pharmacie', 'description': 'Sciences pharmaceutiques'},
        {'nom': 'Agronomie', 'description': 'Sciences agricoles'},
        {'nom': 'Sciences Politiques', 'description': 'Relations internationales et politique'},
    ]
    filieres = []
    for data in filieres_data:
        filiere, created = Filiere.objects.get_or_create(**data)
        filieres.append(filiere)
        print(f"  + {filiere}")
    return filieres


def create_universites():
    """Cree les universites"""
    print("[UNIV] Creation des universites...")
    universites_data = [
        {'nom': 'Université de Kinshasa (UNIKIN)', 'adresse': 'Kinshasa, RDC'},
        {'nom': 'Université de Lubumbashi (UNILU)', 'adresse': 'Lubumbashi, RDC'},
        {'nom': 'Université Catholique du Congo (UCC)', 'adresse': 'Kinshasa, RDC'},
        {'nom': 'Université Protestante au Congo (UPC)', 'adresse': 'Kinshasa, RDC'},
        {'nom': 'Institut Supérieur de Commerce (ISC)', 'adresse': 'Kinshasa, RDC'},
    ]
    universites = []
    for data in universites_data:
        univ, created = Universite.objects.get_or_create(**data)
        universites.append(univ)
        print(f"  + {univ}")
    return universites


def link_universites_filieres(universites, filieres):
    """Lie les universites aux filieres"""
    print("[LINK] Liaison universites-filieres...")
    # UNIKIN a toutes les filières
    universites[0].filieres.add(*filieres)

    # UNILU a Informatique, Médecine, Droit, Génie Civil
    universites[1].filieres.add(*[filieres[0], filieres[1], filieres[2], filieres[4]])

    # UCC a Droit, Économie, Sciences Politiques
    universites[2].filieres.add(*[filieres[2], filieres[3], filieres[7]])

    # UPC a Médecine, Pharmacie
    universites[3].filieres.add(*[filieres[1], filieres[5]])

    # ISC a Économie
    universites[4].filieres.add(filieres[3])

    print("  + Liaisons creees")


def link_filieres_promotions(filieres, promotions):
    """Lie les filieres aux promotions"""
    print("[LINK] Liaison filieres-promotions...")
    for filiere in filieres:
        filiere.promotions.add(*promotions)
    print("  + Liaisons creees")


def create_users(universites, filieres, promotions):
    """Cree les utilisateurs de test"""
    print("[USER] Creation des utilisateurs...")
    users_data = [
        {
            'username': 'admin',
            'email': 'admin@test.com',
            'password': 'admin123',
            'first_name': 'Admin',
            'last_name': 'System',
            'is_superuser': True,
            'is_staff': True,
            'profile': {'groupe': 'ADMIN', 'phone': '+243999000001'}
        },
        {
            'username': 'cp_info',
            'email': 'cp.info@test.com',
            'password': 'cp123456',
            'first_name': 'Jean',
            'last_name': 'Mukendi',
            'profile': {
                'groupe': 'CP',
                'phone': '+243999000002',
                'universite': universites[0],  # UNIKIN
                'filiere': filieres[0],  # Informatique
                'promotion': promotions[2],  # L3
            }
        },
        {
            'username': 'cp_medecine',
            'email': 'cp.med@test.com',
            'password': 'cp123456',
            'first_name': 'Marie',
            'last_name': 'Kabongo',
            'profile': {
                'groupe': 'CP',
                'phone': '+243999000003',
                'universite': universites[0],  # UNIKIN
                'filiere': filieres[1],  # Médecine
                'promotion': promotions[3],  # M1
            }
        },
        {
            'username': 'etudiant1',
            'email': 'etudiant1@test.com',
            'password': 'etud123456',
            'first_name': 'Patrick',
            'last_name': 'Mwamba',
            'profile': {
                'groupe': 'ETUDIANT',
                'phone': '+243999000004',
                'universite': universites[0],
                'filiere': filieres[0],
                'promotion': promotions[2],
            }
        },
        {
            'username': 'etudiant2',
            'email': 'etudiant2@test.com',
            'password': 'etud123456',
            'first_name': 'Grace',
            'last_name': 'Mutombo',
            'profile': {
                'groupe': 'ETUDIANT',
                'phone': '+243999000005',
                'universite': universites[1],
                'filiere': filieres[2],
                'promotion': promotions[1],
            }
        },
    ]
    
    created_users = []
    for data in users_data:
        profile_data = data.pop('profile')
        user, created = User.objects.get_or_create(
            username=data['username'],
            defaults={
                'email': data['email'],
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'is_superuser': data.get('is_superuser', False),
                'is_staff': data.get('is_staff', False),
            }
        )
        if created:
            user.set_password(data['password'])
            user.save()
        
        # Créer ou mettre à jour le profil
        profile, _ = UserProfile.objects.get_or_create(user=user, defaults=profile_data)
        if not _:
            for key, value in profile_data.items():
                setattr(profile, key, value)
            profile.save()
        
        created_users.append(user)
        print(f"  + {user.username} ({profile_data['groupe']})")
    
    return created_users


def create_courses(universites, filieres):
    """Cree les cours"""
    print("[COURSE] Creation des cours...")
    courses_data = [
        # Informatique
        {'nom': 'Algorithmique et Structures de Données', 'filiere': 'Informatique', 'university': 'UNIKIN', 'description': 'Fondamentaux des algorithmes'},
        {'nom': 'Programmation Python', 'filiere': 'Informatique', 'university': 'UNIKIN', 'description': 'Introduction à Python'},
        {'nom': 'Base de Données', 'filiere': 'Informatique', 'university': 'UNIKIN', 'description': 'SQL et modélisation'},
        {'nom': 'Réseaux Informatiques', 'filiere': 'Informatique', 'university': 'UNIKIN', 'description': 'TCP/IP et protocoles'},
        {'nom': 'Intelligence Artificielle', 'filiere': 'Informatique', 'university': 'UNIKIN', 'description': 'Machine Learning basics'},
        
        # Médecine
        {'nom': 'Anatomie Humaine', 'filiere': 'Médecine', 'university': 'UNIKIN', 'description': 'Structure du corps humain'},
        {'nom': 'Physiologie', 'filiere': 'Médecine', 'university': 'UNIKIN', 'description': 'Fonctionnement des organes'},
        {'nom': 'Biochimie Médicale', 'filiere': 'Médecine', 'university': 'UNIKIN', 'description': 'Chimie du vivant'},
        {'nom': 'Pathologie Générale', 'filiere': 'Médecine', 'university': 'UNIKIN', 'description': 'Étude des maladies'},
        
        # Droit
        {'nom': 'Droit Constitutionnel', 'filiere': 'Droit', 'university': 'UNIKIN', 'description': 'Constitution et institutions'},
        {'nom': 'Droit Civil', 'filiere': 'Droit', 'university': 'UNIKIN', 'description': 'Droit des personnes'},
        {'nom': 'Droit Pénal', 'filiere': 'Droit', 'university': 'UNIKIN', 'description': 'Infractions et sanctions'},
        
        # Économie
        {'nom': 'Microéconomie', 'filiere': 'Économie', 'university': 'UNIKIN', 'description': 'Comportement des agents'},
        {'nom': 'Macroéconomie', 'filiere': 'Économie', 'university': 'UNIKIN', 'description': 'Économie nationale'},
        {'nom': 'Comptabilité Générale', 'filiere': 'Économie', 'university': 'ISC', 'description': 'Principes comptables'},
    ]
    
    courses = []
    for data in courses_data:
        course, created = Course.objects.get_or_create(**data)
        courses.append(course)
        print(f"  + {course.nom}")
    return courses


def create_sessions(courses, users):
    """Cree les sessions de cours"""
    print("[SESSION] Creation des sessions...")
    now = timezone.now()
    sessions = []
    
    professeurs = ['Prof. Kalala', 'Prof. Mbaya', 'Prof. Nseka', 'Prof. Tshimanga', 'Prof. Kasongo']
    
    for i, course in enumerate(courses):
        for j in range(3):  # 3 sessions par cours
            session = Session.objects.create(
                course=course,
                date=now - timedelta(days=(i * 7 + j * 2)),
                professeur=professeurs[i % len(professeurs)]
            )
            sessions.append(session)
    
    print(f"  + {len(sessions)} sessions creees")
    return sessions


def create_summaries(courses, sessions, users):
    """Cree les resumes"""
    print("[SUMMARY] Creation des resumes...")
    
    # Trouver les CP
    cp_users = [u for u in users if hasattr(u, 'profile') and u.profile.groupe == 'CP']
    if not cp_users:
        cp_users = users[:1]
    
    summaries_data = [
        {
            'titre': 'Introduction aux Algorithmes',
            'texte_resume': '''
# Introduction aux Algorithmes

## Définition
Un algorithme est une suite finie d'instructions permettant de résoudre un problème.

## Caractéristiques
- **Finitude** : L'algorithme doit se terminer
- **Précision** : Chaque étape doit être définie clairement
- **Entrées** : Données fournies à l'algorithme
- **Sorties** : Résultats produits

## Complexité
- O(1) : Constante
- O(n) : Linéaire
- O(n²) : Quadratique
- O(log n) : Logarithmique

## Exemples
1. Tri à bulles
2. Recherche binaire
3. Tri rapide (QuickSort)
            ''',
            'prix': Decimal('500.00'),
            'is_free': False,
        },
        {
            'titre': 'Les Bases de Python',
            'texte_resume': '''
# Les Bases de Python

## Variables et Types
- int, float, str, bool
- list, tuple, dict, set

## Structures de Contrôle
```python
if condition:
    # code
elif autre_condition:
    # code
else:
    # code
```

## Boucles
```python
for i in range(10):
    print(i)

while condition:
    # code
```

## Fonctions
```python
def ma_fonction(param1, param2):
    return resultat
```
            ''',
            'prix': Decimal('0.00'),
            'is_free': True,
        },
        {
            'titre': 'SQL et Bases de Données',
            'texte_resume': '''
# SQL et Bases de Données

## Commandes de Base
- SELECT : Récupérer des données
- INSERT : Ajouter des données
- UPDATE : Modifier des données
- DELETE : Supprimer des données

## Exemple SELECT
```sql
SELECT nom, prenom 
FROM etudiants 
WHERE promotion = 'L3'
ORDER BY nom;
```

## Jointures
- INNER JOIN
- LEFT JOIN
- RIGHT JOIN
- FULL JOIN
            ''',
            'prix': Decimal('750.00'),
            'is_free': False,
        },
        {
            'titre': 'Anatomie - Système Cardiovasculaire',
            'texte_resume': '''
# Système Cardiovasculaire

## Le Cœur
- 4 cavités : 2 oreillettes, 2 ventricules
- Poids moyen : 300g
- Fréquence : 60-100 bpm

## Circulation Sanguine
1. Circulation pulmonaire (petite circulation)
2. Circulation systémique (grande circulation)

## Vaisseaux Sanguins
- Artères : sang oxygéné
- Veines : sang désoxygéné
- Capillaires : échanges

## Pathologies Courantes
- Hypertension artérielle
- Insuffisance cardiaque
- Arythmies
            ''',
            'prix': Decimal('1000.00'),
            'is_free': False,
        },
        {
            'titre': 'Droit Constitutionnel - Introduction',
            'texte_resume': '''
# Droit Constitutionnel

## Définition
Le droit constitutionnel régit l'organisation et le fonctionnement de l'État.

## Sources
1. La Constitution
2. Les lois organiques
3. La jurisprudence constitutionnelle

## Principes Fondamentaux
- Séparation des pouvoirs
- Souveraineté nationale
- État de droit
- Droits fondamentaux

## Institutions
- Pouvoir exécutif
- Pouvoir législatif
- Pouvoir judiciaire
            ''',
            'prix': Decimal('600.00'),
            'is_free': False,
        },
    ]
    
    summaries = []
    for i, data in enumerate(summaries_data):
        course = courses[i % len(courses)]
        session = sessions[i % len(sessions)] if sessions else None
        author = cp_users[i % len(cp_users)]
        
        summary = Summary.objects.create(
            titre=data['titre'],
            texte_resume=data['texte_resume'],
            course=course,
            session=session,
            author_type='cp',
            author_user=author,
            prix=data['prix'],
            is_free=data['is_free'],
        )
        summaries.append(summary)
        print(f"  + {summary.titre}")
    
    return summaries


def create_services():
    """Cree les services"""
    print("[SERVICE] Creation des services...")
    services_data = [
        {'nom': 'Abonnement Mensuel', 'description': 'Accès illimité pendant 1 mois', 'prix': Decimal('5000.00')},
        {'nom': 'Abonnement Trimestriel', 'description': 'Accès illimité pendant 3 mois', 'prix': Decimal('12000.00')},
        {'nom': 'Abonnement Annuel', 'description': 'Accès illimité pendant 1 an', 'prix': Decimal('40000.00')},
        {'nom': 'Résumé à l\'unité', 'description': 'Achat d\'un seul résumé', 'prix': Decimal('500.00')},
    ]
    
    services = []
    for data in services_data:
        service, created = Service.objects.get_or_create(**data)
        services.append(service)
        print(f"  + {service.nom}")
    return services


def run_seed():
    """Execute le seed complet"""
    print("\n" + "="*50)
    print("SEED DATABASE - Debut")
    print("="*50 + "\n")
    
    # Nettoyer les données existantes
    clear_data()
    
    # Créer les données
    promotions = create_promotions()
    filieres = create_filieres()
    universites = create_universites()
    
    # Créer les liaisons
    link_universites_filieres(universites, filieres)
    link_filieres_promotions(filieres, promotions)
    
    # Créer les utilisateurs
    users = create_users(universites, filieres, promotions)
    
    # Créer les cours et sessions
    courses = create_courses(universites, filieres)
    sessions = create_sessions(courses, users)
    
    # Créer les résumés
    summaries = create_summaries(courses, sessions, users)
    
    # Créer les services
    services = create_services()
    
    print("\n" + "="*50)
    print("[OK] SEED DATABASE - Termine avec succes!")
    print("="*50)
    print(f"""
Resume:
   - {len(universites)} universités
   - {len(filieres)} filières
   - {len(promotions)} promotions
   - {len(users)} utilisateurs
   - {len(courses)} cours
   - {len(sessions)} sessions
   - {len(summaries)} résumés
   - {len(services)} services

Comptes de test:
   - admin / admin123 (Administrateur)
   - cp_info / cp123456 (Chef de Promo Informatique)
   - cp_medecine / cp123456 (Chef de Promo Médecine)
   - etudiant1 / etud123456 (Étudiant)
   - etudiant2 / etud123456 (Étudiant)
""")


if __name__ == '__main__':
    run_seed()
