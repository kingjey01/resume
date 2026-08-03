#!/usr/bin/env python3
"""
Script pour créer des données de test avec MySQL
Usage: python create_test_data_mysql.py
"""

import os
import sys
import django
from pathlib import Path

# Ajouter le répertoire du projet au path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Configuration Django avec MySQL
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# Configuration temporaire pour MySQL
import django.conf
if not django.conf.settings.configured:
    django.conf.settings.configure(
        DEBUG=True,
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.mysql',
                'NAME': os.environ.get('DB_NAME', 'resume_plus_db'),
                'USER': os.environ.get('DB_USER', 'resume_user'),
                'PASSWORD': os.environ.get('DB_PASSWORD', 'your_mysql_password'),
                'HOST': os.environ.get('DB_HOST', 'localhost'),
                'PORT': os.environ.get('DB_PORT', '3306'),
                'OPTIONS': {
                    'charset': 'utf8mb4',
                    'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
                }
            }
        },
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'courses',
            'users',
        ],
        USE_TZ=True,
        SECRET_KEY='temp-key-for-data-creation'
    )

django.setup()

from courses.models import Universite, Filiere, Promotion, Course
from django.contrib.auth.models import User
from users.models import UserProfile
from django.db import transaction

def create_test_data():
    print("=" * 50)
    print("🌱 Création des données de test (MySQL)")
    print("=" * 50)

    try:
        with transaction.atomic():
            # ========================================
            # 1. Créer des Universités
            # ========================================
            print("\n📚 Création des universités...")

            universites_data = [
                {'nom': 'Université de Kinshasa', 'adresse': 'Kinshasa, RDC'},
                {'nom': 'Université de Lubumbashi', 'adresse': 'Lubumbashi, RDC'},
                {'nom': 'Université de Kisangani', 'adresse': 'Kisangani, RDC'},
                {'nom': 'Université Protestante au Congo', 'adresse': 'Kinshasa, RDC'},
                {'nom': 'Université Catholique du Congo', 'adresse': 'Kinshasa, RDC'},
            ]

            for data in universites_data:
                univ, created = Universite.objects.get_or_create(
                    nom=data['nom'],
                    defaults={'adresse': data['adresse']}
                )
                if created:
                    print(f"  ✓ {data['nom']} créée")
                else:
                    print(f"  ℹ {data['nom']} existe déjà")

            # ========================================
            # 2. Créer des Filières
            # ========================================
            print("\n🎓 Création des filières...")

            filieres_data = [
                {'nom': 'Informatique', 'description': 'Sciences Informatiques et Technologies'},
                {'nom': 'Médecine', 'description': 'Sciences Médicales'},
                {'nom': 'Droit', 'description': 'Sciences Juridiques'},
                {'nom': 'Économie', 'description': 'Sciences Économiques et Gestion'},
                {'nom': 'Ingénierie', 'description': 'Sciences de l\'Ingénieur'},
                {'nom': 'Lettres', 'description': 'Lettres et Sciences Humaines'},
                {'nom': 'Sciences', 'description': 'Sciences Exactes'},
            ]

            for data in filieres_data:
                filiere, created = Filiere.objects.get_or_create(
                    nom=data['nom'],
                    defaults={'description': data['description']}
                )
                if created:
                    print(f"  ✓ {data['nom']} créée")
                else:
                    print(f"  ℹ {data['nom']} existe déjà")

            # ========================================
            # 3. Créer des Promotions
            # ========================================
            print("\n📅 Création des promotions...")

            promotions_data = [
                {'nom': 'L1', 'annee': 1},
                {'nom': 'L2', 'annee': 2},
                {'nom': 'L3', 'annee': 3},
                {'nom': 'M1', 'annee': 4},
                {'nom': 'M2', 'annee': 5},
            ]

            for data in promotions_data:
                promo, created = Promotion.objects.get_or_create(
                    nom=data['nom'],
                    defaults={'annee': data['annee']}
                )
                if created:
                    print(f"  ✓ {data['nom']} (Année {data['annee']}) créée")
                else:
                    print(f"  ℹ {data['nom']} existe déjà")

            # ========================================
            # 4. Créer des Cours
            # ========================================
            print("\n📖 Création de cours exemples...")

            try:
                universite = Universite.objects.first()
                filiere_info = Filiere.objects.get(nom='Informatique')
                
                cours_data = [
                    {
                        'nom': 'Introduction à la Programmation',
                        'description': 'Cours d\'introduction aux concepts de base de la programmation',
                        'university': universite.nom,
                        'filiere': filiere_info.nom
                    },
                    {
                        'nom': 'Structures de Données',
                        'description': 'Étude des structures de données fondamentales',
                        'university': universite.nom,
                        'filiere': filiere_info.nom
                    },
                    {
                        'nom': 'Bases de Données',
                        'description': 'Introduction aux systèmes de gestion de bases de données',
                        'university': universite.nom,
                        'filiere': filiere_info.nom
                    },
                    {
                        'nom': 'Développement Web',
                        'description': 'Création d\'applications web modernes',
                        'university': universite.nom,
                        'filiere': filiere_info.nom
                    },
                    {
                        'nom': 'Intelligence Artificielle',
                        'description': 'Introduction aux concepts d\'IA et machine learning',
                        'university': universite.nom,
                        'filiere': filiere_info.nom
                    },
                ]
                
                for data in cours_data:
                    cours, created = Course.objects.get_or_create(
                        nom=data['nom'],
                        defaults={
                            'description': data['description'],
                            'university': data['university'],
                            'filiere': data['filiere']
                        }
                    )
                    if created:
                        print(f"  ✓ {data['nom']} créé")
                    else:
                        print(f"  ℹ {data['nom']} existe déjà")
            except Exception as e:
                print(f"  ⚠ Erreur lors de la création des cours: {e}")

            # ========================================
            # 5. Créer utilisateurs de test
            # ========================================
            print("\n👤 Création des utilisateurs de test...")

            # Utilisateur CP
            try:
                user_cp, created = User.objects.get_or_create(
                    email='cp@test.com',
                    defaults={
                        'username': 'cp_test',
                        'first_name': 'CP',
                        'last_name': 'Test',
                    }
                )
                
                if created:
                    user_cp.set_password('TestCP123!')
                    user_cp.save()
                    print(f"  ✓ Utilisateur CP créé")
                    
                    # Créer ou mettre à jour le profil
                    profile_cp, profile_created = UserProfile.objects.get_or_create(
                        user=user_cp,
                        defaults={
                            'groupe': 'CP',
                            'universite': Universite.objects.first(),
                            'filiere': Filiere.objects.first(),
                            'promotion': Promotion.objects.first()
                        }
                    )
                    if profile_created:
                        print(f"  ✓ Profil CP créé")
                    else:
                        print(f"  ℹ Profil CP existe déjà")
                else:
                    print(f"  ℹ Utilisateur CP existe déjà")
            except Exception as e:
                print(f"  ✗ Erreur CP: {e}")

            # Utilisateur Étudiant
            try:
                user_etudiant, created = User.objects.get_or_create(
                    email='etudiant@test.com',
                    defaults={
                        'username': 'etudiant_test',
                        'first_name': 'Étudiant',
                        'last_name': 'Test',
                    }
                )
                
                if created:
                    user_etudiant.set_password('TestEtudiant123!')
                    user_etudiant.save()
                    print(f"  ✓ Utilisateur Étudiant créé")
                    
                    profile_etudiant, profile_created = UserProfile.objects.get_or_create(
                        user=user_etudiant,
                        defaults={
                            'groupe': 'ETUDIANT',
                            'universite': Universite.objects.first(),
                            'filiere': Filiere.objects.first(),
                            'promotion': Promotion.objects.first()
                        }
                    )
                    if profile_created:
                        print(f"  ✓ Profil Étudiant créé")
                    else:
                        print(f"  ℹ Profil Étudiant existe déjà")
                else:
                    print(f"  ℹ Utilisateur Étudiant existe déjà")
            except Exception as e:
                print(f"  ✗ Erreur Étudiant: {e}")

            # Utilisateur Admin
            try:
                user_admin, created = User.objects.get_or_create(
                    email='admin@test.com',
                    defaults={
                        'username': 'admin_test',
                        'first_name': 'Admin',
                        'last_name': 'Test',
                        'is_staff': True,
                        'is_superuser': True,
                    }
                )
                
                if created:
                    user_admin.set_password('AdminTest123!')
                    user_admin.save()
                    print(f"  ✓ Utilisateur Admin créé")
                else:
                    print(f"  ℹ Utilisateur Admin existe déjà")
            except Exception as e:
                print(f"  ✗ Erreur Admin: {e}")

            # ========================================
            # 6. Statistiques
            # ========================================
            print("\n" + "=" * 50)
            print("📊 Statistiques")
            print("=" * 50)
            print(f"  Universités: {Universite.objects.count()}")
            print(f"  Filières: {Filiere.objects.count()}")
            print(f"  Promotions: {Promotion.objects.count()}")
            print(f"  Cours: {Course.objects.count()}")
            print(f"  Utilisateurs: {User.objects.count()}")
            print(f"  Profils: {UserProfile.objects.count()}")

            print("\n" + "=" * 50)
            print("🔑 Comptes de test créés")
            print("=" * 50)
            print("\n👨‍🏫 Compte CP:")
            print("  Email: cp@test.com")
            print("  Password: TestCP123!")
            print("  Rôle: CP (Chargé de Promotion)")

            print("\n👨‍🎓 Compte Étudiant:")
            print("  Email: etudiant@test.com")
            print("  Password: TestEtudiant123!")
            print("  Rôle: ETUDIANT")

            print("\n👨‍💼 Compte Admin:")
            print("  Email: admin@test.com")
            print("  Password: AdminTest123!")
            print("  Rôle: ADMIN (Superuser)")

            print("\n✅ Données de test créées avec succès!")

    except Exception as e:
        print(f"\n❌ Erreur lors de la création des données: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    print("🔧 Configuration pour MySQL...")
    print("Assurez-vous que votre base de données MySQL est accessible")
    print("Variables d'environnement utilisées:")
    print(f"  DB_NAME: {os.environ.get('DB_NAME', 'resume_plus_db')}")
    print(f"  DB_USER: {os.environ.get('DB_USER', 'resume_user')}")
    print(f"  DB_HOST: {os.environ.get('DB_HOST', 'localhost')}")
    print(f"  DB_PORT: {os.environ.get('DB_PORT', '3306')}")
    print()
    
    success = create_test_data()
    sys.exit(0 if success else 1)