#!/usr/bin/env python3
"""
Script pour créer des données de test avec votre configuration MySQL existante
Usage: python run_seed.py
"""

import os
import sys
import pymysql
from pathlib import Path

# Installer PyMySQL comme MySQLdb (comme dans votre config)
pymysql.install_as_MySQLdb()

# Ajouter le répertoire du projet au path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Configuration Django avec votre configuration MySQL existante
import django.conf

try:
    from decouple import config
except ImportError:
    print("⚠️ python-decouple non installé, utilisation des valeurs par défaut")
    def config(key, default=None):
        return os.environ.get(key, default)

# Configuration directe avec vos paramètres
django.conf.settings.configure(
    DEBUG=True,
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': config('DB_NAME', default='jey_resume'),
            'USER': config('DB_USER', default='jey_resume'),
            'PASSWORD': config('DB_PASSWORD', default='1234'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='3306'),
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
    SECRET_KEY='temp-key-for-data-creation',
    DEFAULT_AUTO_FIELD='django.db.models.BigAutoField'
)

import django
django.setup()

from courses.models import Universite, Filiere, Promotion, Course
from django.contrib.auth.models import User
from users.models import UserProfile
from django.db import transaction

def create_test_data():
    print("=" * 50)
    print("🌱 Création des données de test (MySQL - Config existante)")
    print("=" * 50)
    
    # Afficher la configuration utilisée
    db_config = django.conf.settings.DATABASES['default']
    print(f"📊 Configuration MySQL:")
    print(f"  Database: {db_config['NAME']}")
    print(f"  User: {db_config['USER']}")
    print(f"  Host: {db_config['HOST']}:{db_config['PORT']}")
    print()

    try:
        # Test de connexion
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            print("✅ Connexion MySQL réussie")
        
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
            # 5. Créer des Résumés de test
            # ========================================
            print("\n� Création dde résumés de test...")

            try:
                from courses.models import Summary
                
                # Récupérer quelques cours pour les résumés
                cours_list = Course.objects.all()[:3]
                
                resumes_data = [
                    {
                        'title': 'Résumé - Variables et Types de Données',
                        'content': 'Les variables sont des espaces mémoire nommés qui stockent des valeurs. En Python, nous avons plusieurs types : int (entiers), float (décimaux), str (chaînes), bool (booléens). Exemple: age = 25, nom = "Jean", actif = True.',
                        'course': cours_list[0] if cours_list else None,
                        'summary_type': 'MANUAL'
                    },
                    {
                        'title': 'Résumé - Structures de Contrôle',
                        'content': 'Les structures de contrôle permettent de diriger l\'exécution du programme. If/else pour les conditions, for/while pour les boucles. Exemple: if age >= 18: print("Majeur") else: print("Mineur")',
                        'course': cours_list[1] if len(cours_list) > 1 else cours_list[0] if cours_list else None,
                        'summary_type': 'MANUAL'
                    },
                    {
                        'title': 'Résumé - Fonctions et Modules',
                        'content': 'Les fonctions sont des blocs de code réutilisables. Syntaxe: def nom_fonction(paramètres): return résultat. Les modules permettent d\'organiser le code en fichiers séparés.',
                        'course': cours_list[2] if len(cours_list) > 2 else cours_list[0] if cours_list else None,
                        'summary_type': 'MANUAL'
                    },
                    {
                        'title': 'Résumé Audio - Introduction aux Algorithmes',
                        'content': 'Résumé généré automatiquement à partir d\'un enregistrement audio du cours sur les algorithmes de tri. Contient les concepts de complexité temporelle O(n), tri à bulles, tri rapide.',
                        'course': cours_list[0] if cours_list else None,
                        'summary_type': 'AUDIO'
                    },
                    {
                        'title': 'Résumé Audio - Bases de Données Relationnelles',
                        'content': 'Résumé automatique du cours sur les SGBD. Couvre les concepts de tables, clés primaires, clés étrangères, jointures SQL, normalisation des données.',
                        'course': cours_list[1] if len(cours_list) > 1 else cours_list[0] if cours_list else None,
                        'summary_type': 'AUDIO'
                    }
                ]
                
                for data in resumes_data:
                    if data['course']:  # Seulement si on a un cours
                        resume, created = Summary.objects.get_or_create(
                            title=data['title'],
                            defaults={
                                'content': data['content'],
                                'course': data['course'],
                                'summary_type': data['summary_type']
                            }
                        )
                        if created:
                            print(f"  ✓ {data['title']} créé")
                        else:
                            print(f"  ℹ {data['title']} existe déjà")
                    else:
                        print(f"  ⚠ Pas de cours disponible pour {data['title']}")
                        
            except Exception as e:
                print(f"  ⚠ Erreur lors de la création des résumés: {e}")

            # ========================================
            # 6. Créer des Séances Audio de test
            # ========================================
            print("\n🎵 Création de séances audio de test...")

            try:
                from courses.models import AudioSession
                from datetime import datetime, timedelta
                import random
                
                # Récupérer quelques cours pour les séances
                cours_list = Course.objects.all()[:3]
                
                seances_data = [
                    {
                        'title': 'Séance 1 - Introduction à la Programmation',
                        'course': cours_list[0] if cours_list else None,
                        'professor_name': 'Prof. Martin Dubois',
                        'duration_minutes': 90,
                        'file_size_mb': 45.2,
                        'notes': 'Première séance du semestre, introduction aux concepts de base',
                        'status': 'COMPLETED'
                    },
                    {
                        'title': 'Séance 2 - Variables et Types',
                        'course': cours_list[0] if cours_list else None,
                        'professor_name': 'Prof. Martin Dubois',
                        'duration_minutes': 75,
                        'file_size_mb': 38.7,
                        'notes': 'Explication détaillée des types de données en Python',
                        'status': 'COMPLETED'
                    },
                    {
                        'title': 'Séance 3 - Structures de Données',
                        'course': cours_list[1] if len(cours_list) > 1 else cours_list[0] if cours_list else None,
                        'professor_name': 'Prof. Sarah Johnson',
                        'duration_minutes': 120,
                        'file_size_mb': 62.1,
                        'notes': 'Listes, dictionnaires, tuples et leurs utilisations',
                        'status': 'COMPLETED'
                    },
                    {
                        'title': 'Séance 4 - Algorithmes de Tri',
                        'course': cours_list[1] if len(cours_list) > 1 else cours_list[0] if cours_list else None,
                        'professor_name': 'Prof. Sarah Johnson',
                        'duration_minutes': 105,
                        'file_size_mb': 51.8,
                        'notes': 'Tri à bulles, tri par insertion, tri rapide',
                        'status': 'PROCESSING'
                    },
                    {
                        'title': 'Séance 5 - Bases de Données SQL',
                        'course': cours_list[2] if len(cours_list) > 2 else cours_list[0] if cours_list else None,
                        'professor_name': 'Prof. Ahmed Hassan',
                        'duration_minutes': 95,
                        'file_size_mb': 47.3,
                        'notes': 'Requêtes SELECT, JOIN, GROUP BY',
                        'status': 'COMPLETED'
                    },
                    {
                        'title': 'Séance 6 - Projet Final',
                        'course': cours_list[0] if cours_list else None,
                        'professor_name': 'Prof. Martin Dubois',
                        'duration_minutes': 60,
                        'file_size_mb': 29.5,
                        'notes': 'Présentation des projets étudiants',
                        'status': 'PENDING'
                    }
                ]
                
                for i, data in enumerate(seances_data):
                    if data['course']:  # Seulement si on a un cours
                        # Créer une date d'enregistrement réaliste (dans les 30 derniers jours)
                        recorded_date = datetime.now() - timedelta(days=random.randint(1, 30))
                        
                        seance, created = AudioSession.objects.get_or_create(
                            title=data['title'],
                            defaults={
                                'course': data['course'],
                                'professor_name': data['professor_name'],
                                'duration_minutes': data['duration_minutes'],
                                'file_size_mb': data['file_size_mb'],
                                'notes': data['notes'],
                                'status': data['status'],
                                'recorded_at': recorded_date,
                                'audio_file_path': f'/media/audio/session_{i+1}_{data["course"].id}.m4a',
                                'transcript': f'Transcript automatique de la séance: {data["title"]}. Contenu du cours enregistré et transcrit automatiquement.',
                            }
                        )
                        if created:
                            print(f"  ✓ {data['title']} créée")
                        else:
                            print(f"  ℹ {data['title']} existe déjà")
                    else:
                        print(f"  ⚠ Pas de cours disponible pour {data['title']}")
                        
            except Exception as e:
                print(f"  ⚠ Erreur lors de la création des séances audio: {e}")

            # ========================================
            # 7. Créer utilisateurs de test
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
            # 8. Statistiques
            # ========================================
            print("\n" + "=" * 50)
            print("📊 Statistiques")
            print("=" * 50)
            print(f"  Universités: {Universite.objects.count()}")
            print(f"  Filières: {Filiere.objects.count()}")
            print(f"  Promotions: {Promotion.objects.count()}")
            print(f"  Cours: {Course.objects.count()}")
            
            # Statistiques des résumés et séances
            try:
                from courses.models import Summary, AudioSession
                print(f"  Résumés: {Summary.objects.count()}")
                print(f"  Séances Audio: {AudioSession.objects.count()}")
                
                # Détail par type de résumé
                manual_count = Summary.objects.filter(summary_type='MANUAL').count()
                audio_count = Summary.objects.filter(summary_type='AUDIO').count()
                print(f"    - Résumés manuels: {manual_count}")
                print(f"    - Résumés audio: {audio_count}")
                
                # Détail par statut de séance
                completed_sessions = AudioSession.objects.filter(status='COMPLETED').count()
                processing_sessions = AudioSession.objects.filter(status='PROCESSING').count()
                pending_sessions = AudioSession.objects.filter(status='PENDING').count()
                print(f"    - Séances terminées: {completed_sessions}")
                print(f"    - Séances en traitement: {processing_sessions}")
                print(f"    - Séances en attente: {pending_sessions}")
                
            except Exception as e:
                print(f"  ⚠ Erreur statistiques résumés/séances: {e}")
            
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
    print("🔧 Utilisation de votre configuration MySQL existante...")
    print("Configuration détectée:")
    print(f"  DB_NAME: {config('DB_NAME', default='jey_resume')}")
    print(f"  DB_USER: {config('DB_USER', default='jey_resume')}")
    print(f"  DB_HOST: {config('DB_HOST', default='localhost')}")
    print(f"  DB_PORT: {config('DB_PORT', default='3306')}")
    print()
    
    success = create_test_data()
    sys.exit(0 if success else 1)