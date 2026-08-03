#!/usr/bin/env python3
"""
Script pour créer des données de test avec votre configuration MySQL existante
Usage: python create_test_data.py
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

from courses.models import Universite, Filiere, Promotion, Course, Summary, Session
from django.contrib.auth.models import User
from users.models import UserProfile
from django.db import transaction
from datetime import datetime, timedelta
import random

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
            # 5. Créer des Séances de test
            # ========================================
            print("\n🎵 Création de séances de test...")

            try:
                # Récupérer quelques cours pour les séances
                cours_list = Course.objects.all()[:3]
                
                seances_data = [
                    {
                        'course': cours_list[0] if cours_list else None,
                        'professeur': 'Prof. Martin Dubois',
                        'date': datetime.now() - timedelta(days=7)
                    },
                    {
                        'course': cours_list[1] if len(cours_list) > 1 else cours_list[0] if cours_list else None,
                        'professeur': 'Prof. Sarah Johnson',
                        'date': datetime.now() - timedelta(days=14)
                    },
                    {
                        'course': cours_list[2] if len(cours_list) > 2 else cours_list[0] if cours_list else None,
                        'professeur': 'Prof. Ahmed Hassan',
                        'date': datetime.now() - timedelta(days=21)
                    }
                ]
                
                for i, data in enumerate(seances_data):
                    if data['course']:
                        seance, created = Session.objects.get_or_create(
                            course=data['course'],
                            date=data['date'],
                            defaults={
                                'professeur': data['professeur']
                            }
                        )
                        if created:
                            print(f"  ✓ Séance {data['course'].nom} créée")
                        else:
                            print(f"  ℹ Séance {data['course'].nom} existe déjà")
                    else:
                        print(f"  ⚠ Pas de cours disponible pour la séance {i+1}")
                        
            except Exception as e:
                print(f"  ⚠ Erreur lors de la création des séances: {e}")

            # ========================================
            # 6. Créer des fichiers audio de test
            # ========================================
            print("\n🎵 Création de fichiers audio de test...")
            
            try:
                import os
                from django.core.files.base import ContentFile
                
                # Créer le répertoire media/audio_sessions s'il n'existe pas
                media_root = os.path.join(BASE_DIR, 'media', 'audio_sessions')
                os.makedirs(media_root, exist_ok=True)
                
                # Créer des fichiers audio factices pour les tests
                audio_files_created = 0
                for i, session in enumerate(Session.objects.all()[:3]):
                    if not session.audio_file:
                        # Créer un fichier audio factice (silence)
                        fake_audio_content = b'RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x08\x00\x00' + b'\x00' * 2048
                        
                        filename = f'session_{session.id}_demo.wav'
                        session.audio_file.save(
                            filename,
                            ContentFile(fake_audio_content),
                            save=True
                        )
                        audio_files_created += 1
                        print(f"  ✓ Fichier audio créé pour session {session.id}")
                
                if audio_files_created == 0:
                    print("  ℹ Toutes les sessions ont déjà des fichiers audio")
                else:
                    print(f"  ✅ {audio_files_created} fichiers audio de test créés")
                    
            except Exception as e:
                print(f"  ⚠ Erreur lors de la création des fichiers audio: {e}")

            # ========================================
            # 7. Créer des Résumés de test
            # ========================================
            print("\n📝 Création de résumés de test...")

            try:
                # Récupérer quelques cours pour les résumés
                cours_list = Course.objects.all()[:3]
                sessions_list = Session.objects.all()[:2]
                
                resumes_data = [
                    {
                        'titre': 'Résumé - Variables et Types de Données',
                        'texte_resume': 'Les variables sont des espaces mémoire nommés qui stockent des valeurs. En Python, nous avons plusieurs types : int (entiers), float (décimaux), str (chaînes), bool (booléens). Exemple: age = 25, nom = "Jean", actif = True.',
                        'course': cours_list[0] if cours_list else None,
                        'author_type': 'cp',
                        'prix': 0.00,
                        'is_free': True
                    },
                    {
                        'titre': 'Résumé - Structures de Contrôle',
                        'texte_resume': 'Les structures de contrôle permettent de diriger l\'exécution du programme. If/else pour les conditions, for/while pour les boucles. Exemple: if age >= 18: print("Majeur") else: print("Mineur")',
                        'course': cours_list[1] if len(cours_list) > 1 else cours_list[0] if cours_list else None,
                        'author_type': 'cp',
                        'prix': 5.00,
                        'is_free': False
                    },
                    {
                        'titre': 'Résumé - Fonctions et Modules',
                        'texte_resume': 'Les fonctions sont des blocs de code réutilisables. Syntaxe: def nom_fonction(paramètres): return résultat. Les modules permettent d\'organiser le code en fichiers séparés.',
                        'course': cours_list[2] if len(cours_list) > 2 else cours_list[0] if cours_list else None,
                        'author_type': 'cp',
                        'prix': 3.50,
                        'is_free': False
                    },
                    {
                        'titre': 'Résumé IA - Introduction aux Algorithmes',
                        'texte_resume': 'Résumé généré automatiquement à partir d\'un enregistrement audio du cours sur les algorithmes de tri. Contient les concepts de complexité temporelle O(n), tri à bulles, tri rapide.',
                        'course': cours_list[0] if cours_list else None,
                        'session': sessions_list[0] if sessions_list else None,
                        'author_type': 'ai',
                        'prix': 2.00,
                        'is_free': False
                    },
                    {
                        'titre': 'Résumé IA - Bases de Données Relationnelles',
                        'texte_resume': 'Résumé automatique du cours sur les SGBD. Couvre les concepts de tables, clés primaires, clés étrangères, jointures SQL, normalisation des données.',
                        'course': cours_list[1] if len(cours_list) > 1 else cours_list[0] if cours_list else None,
                        'session': sessions_list[1] if len(sessions_list) > 1 else sessions_list[0] if sessions_list else None,
                        'author_type': 'ai',
                        'prix': 0.00,
                        'is_free': True
                    }
                ]
                
                for data in resumes_data:
                    if data['course']:
                        defaults = {
                            'texte_resume': data['texte_resume'],
                            'course': data['course'],
                            'author_type': data['author_type'],
                            'prix': data['prix'],
                            'is_free': data['is_free']
                        }
                        if 'session' in data and data['session']:
                            defaults['session'] = data['session']
                            
                        resume, created = Summary.objects.get_or_create(
                            titre=data['titre'],
                            defaults=defaults
                        )
                        if created:
                            print(f"  ✓ {data['titre']} créé")
                        else:
                            print(f"  ℹ {data['titre']} existe déjà")
                    else:
                        print(f"  ⚠ Pas de cours disponible pour {data['titre']}")
                        
            except Exception as e:
                print(f"  ⚠ Erreur lors de la création des résumés: {e}")

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
            print(f"  Séances: {Session.objects.count()}")
            print(f"  Résumés: {Summary.objects.count()}")
            
            # Détail par type de résumé
            try:
                cp_count = Summary.objects.filter(author_type='cp').count()
                ai_count = Summary.objects.filter(author_type='ai').count()
                free_count = Summary.objects.filter(is_free=True).count()
                paid_count = Summary.objects.filter(is_free=False).count()
                
                print(f"    - Résumés par CP: {cp_count}")
                print(f"    - Résumés par IA: {ai_count}")
                print(f"    - Résumés gratuits: {free_count}")
                print(f"    - Résumés payants: {paid_count}")
            except Exception as e:
                print(f"  ⚠ Erreur statistiques résumés: {e}")
            
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