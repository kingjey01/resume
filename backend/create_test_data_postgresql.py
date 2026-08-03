#!/usr/bin/env python3
"""
Script pour créer des données de test avec PostgreSQL
Usage: python create_test_data_postgresql.py
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')
django.setup()

from courses.models import Universite, Filiere, Promotion, Course
from django.contrib.auth.models import User
from users.models import UserProfile
from django.db import transaction

def create_test_data():
    print("=" * 50)
    print("🌱 Création des données de test (PostgreSQL)")
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
                    
                    profile_cp = UserProfile.objects.create(
                        user=user_cp,
                        groupe='CP',
                        universite=Universite.objects.first(),
                        filiere=Filiere.objects.first(),
                        promotion=Promotion.objects.first()
                    )
                    print(f"  ✓ Profil CP créé")
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
                    
                    profile_etudiant = UserProfile.objects.create(
                        user=user_etudiant,
                        groupe='ETUDIANT',
                        universite=Universite.objects.first(),
                        filiere=Filiere.objects.first(),
                        promotion=Promotion.objects.first()
                    )
                    print(f"  ✓ Profil Étudiant créé")
                else:
                    print(f"  ℹ Utilisateur Étudiant existe déjà")
            except Exception as e:
                print(f"  ✗ Erreur Étudiant: {e}")

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
            print("🔑 Comptes de test")
            print("=" * 50)
            print("\n👨‍🏫 Compte CP:")
            print("  Email: cp@test.com")
            print("  Password: TestCP123!")

            print("\n👨‍🎓 Compte Étudiant:")
            print("  Email: etudiant@test.com")
            print("  Password: TestEtudiant123!")

            print("\n✅ Données de test créées avec succès!")

    except Exception as e:
        print(f"\n❌ Erreur lors de la création des données: {e}")
        return False
    
    return True

if __name__ == '__main__':
    success = create_test_data()
    sys.exit(0 if success else 1)