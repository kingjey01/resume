#!/usr/bin/env python3
"""
🌱 SEED DATABASE - Resume+ Application
=====================================

Script complet pour remplir la base de données avec des données fictives réalistes.

Usage:
    python manage.py shell < seed_database.py

Ou directement:
    python seed_database.py

Auteur: Kiro IDE
Date: 2024-11-13
"""

import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone

# Configuration Django
# if __name__ == "__main__":
#     os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')
#     django.setup()

from django.contrib.auth.models import User
from courses.models import (
    Universite, Filiere, Promotion, Course, Session, Summary,
    Service, Abonnement
)
from users.models import UserProfile

def print_header(title):
    """Affiche un en-tête formaté"""
    print("\n" + "=" * 60)
    print(f"🌱 {title}")
    print("=" * 60)

def print_section(title):
    """Affiche une section formatée"""
    print(f"\n📋 {title}")
    print("-" * 40)

def create_universites():
    """Crée les universités de la RDC"""
    print_section("Création des Universités")
    
    universites_data = [
        {
            'nom': 'Université de Kinshasa (UNIKIN)',
            'adresse': 'Avenue de l\'Université, Kinshasa, République Démocratique du Congo'
        },
        {
            'nom': 'Université de Lubumbashi (UNILU)',
            'adresse': 'Avenue Kato, Lubumbashi, Haut-Katanga, RDC'
        },
        {
            'nom': 'Université de Kisangani (UNIKIS)',
            'adresse': 'Boulevard Kithima, Kisangani, Tshopo, RDC'
        },
        {
            'nom': 'Université Protestante au Congo (UPC)',
            'adresse': 'Avenue Libération, Kinshasa, RDC'
        },
        {
            'nom': 'Université Catholique du Congo (UCC)',
            'adresse': 'Avenue de la Paix, Kinshasa, RDC'
        },
        {
            'nom': 'Université Pédagogique Nationale (UPN)',
            'adresse': 'Croisement des Avenues de la Science et Kimbanguiste, Kinshasa, RDC'
        },
        {
            'nom': 'Institut Supérieur de Commerce (ISC)',
            'adresse': 'Avenue Kasavubu, Kinshasa, RDC'
        },
        {
            'nom': 'Université de Goma (UNIGOM)',
            'adresse': 'Avenue Rond-Point, Goma, Nord-Kivu, RDC'
        }
    ]
    
    created_count = 0
    for data in universites_data:
        univ, created = Universite.objects.get_or_create(
            nom=data['nom'],
            defaults={'adresse': data['adresse']}
        )
        if created:
            print(f"  ✅ {data['nom']}")
            created_count += 1
        else:
            print(f"  ℹ️  {data['nom']} (existe déjà)")
    
    print(f"\n📊 {created_count} nouvelles universités créées")
    return Universite.objects.all()

def create_filieres():
    """Crée les filières d'études"""
    print_section("Création des Filières")
    
    filieres_data = [
        {
            'nom': 'Informatique et Technologies',
            'description': 'Sciences Informatiques, Génie Logiciel, Réseaux et Télécommunications'
        },
        {
            'nom': 'Médecine Générale',
            'description': 'Formation médicale générale, anatomie, physiologie, pathologie'
        },
        {
            'nom': 'Sciences Juridiques',
            'description': 'Droit civil, droit pénal, droit international, droit des affaires'
        },
        {
            'nom': 'Sciences Économiques et Gestion',
            'description': 'Économie, finance, comptabilité, management, marketing'
        },
        {
            'nom': 'Génie Civil',
            'description': 'Construction, infrastructure, géotechnique, hydraulique'
        },
        {
            'nom': 'Génie Électrique',
            'description': 'Électronique, automatique, télécommunications, énergie'
        },
        {
            'nom': 'Lettres et Sciences Humaines',
            'description': 'Littérature, philosophie, histoire, sociologie, psychologie'
        },
        {
            'nom': 'Sciences Exactes',
            'description': 'Mathématiques, physique, chimie, biologie'
        },
        {
            'nom': 'Agronomie',
            'description': 'Agriculture, élevage, foresterie, développement rural'
        },
        {
            'nom': 'Architecture',
            'description': 'Conception architecturale, urbanisme, design d\'intérieur'
        },
        {
            'nom': 'Sciences Politiques',
            'description': 'Relations internationales, administration publique, diplomatie'
        },
        {
            'nom': 'Communication et Journalisme',
            'description': 'Journalisme, relations publiques, communication digitale'
        }
    ]
    
    created_count = 0
    for data in filieres_data:
        filiere, created = Filiere.objects.get_or_create(
            nom=data['nom'],
            defaults={'description': data['description']}
        )
        if created:
            print(f"  ✅ {data['nom']}")
            created_count += 1
        else:
            print(f"  ℹ️  {data['nom']} (existe déjà)")
    
    print(f"\n📊 {created_count} nouvelles filières créées")
    return Filiere.objects.all()

def create_promotions():
    """Crée les promotions/niveaux d'études"""
    print_section("Création des Promotions")
    
    promotions_data = [
        {'nom': 'L1', 'annee': 1},
        {'nom': 'L2', 'annee': 2},
        {'nom': 'L3', 'annee': 3},
        {'nom': 'M1', 'annee': 4},
        {'nom': 'M2', 'annee': 5},
        {'nom': 'D1', 'annee': 6},
        {'nom': 'D2', 'annee': 7},
        {'nom': 'D3', 'annee': 8},
    ]
    
    created_count = 0
    for data in promotions_data:
        promo, created = Promotion.objects.get_or_create(
            nom=data['nom'],
            defaults={'annee': data['annee']}
        )
        if created:
            print(f"  ✅ {data['nom']} - Année {data['annee']}")
            created_count += 1
        else:
            print(f"  ℹ️  {data['nom']} (existe déjà)")
    
    print(f"\n📊 {created_count} nouvelles promotions créées")
    return Promotion.objects.all()

def create_relations(universites, filieres, promotions):
    """Crée les relations entre universités, filières et promotions"""
    print_section("Création des Relations")
    
    # Relations Université-Filière
    print("🔗 Relations Université-Filière...")
    univ_fil_count = 0
    for universite in universites:
        for filiere in filieres:
            if universite.nom == 'Institut Supérieur de Commerce (ISC)':
                if filiere.nom not in ['Sciences Économiques et Gestion', 'Communication et Journalisme']:
                    continue
            
            if not universite.filieres.filter(pk=filiere.pk).exists():
                universite.filieres.add(filiere)
                univ_fil_count += 1

    print(f"  ✅ {univ_fil_count} relations université-filière créées")
    
    # Relations Filière-Promotion
    print("🔗 Relations Filière-Promotion...")
    fil_promo_count = 0
    for filiere in filieres:
        for promotion in promotions:
            if filiere.nom == 'Médecine Générale' and promotion.annee > 5:
                continue
            
            if not filiere.promotions.filter(pk=promotion.pk).exists():
                filiere.promotions.add(promotion)
                fil_promo_count += 1
    
    print(f"  ✅ {fil_promo_count} relations filière-promotion créées")

def create_courses():
    """Crée des cours réalistes"""
    print_section("Création des Cours")
    
    cours_par_filiere = {
        'Informatique et Technologies': [
            'Introduction à la Programmation',
            'Structures de Données et Algorithmes',
            'Bases de Données Relationnelles',
            'Génie Logiciel',
            'Réseaux Informatiques',
            'Sécurité Informatique',
            'Intelligence Artificielle',
            'Développement Web',
            'Systèmes d\'Exploitation',
            'Architecture des Ordinateurs'
        ],
        'Médecine Générale': [
            'Anatomie Humaine',
            'Physiologie',
            'Pathologie Générale',
            'Pharmacologie',
            'Microbiologie',
            'Cardiologie',
            'Neurologie',
            'Pédiatrie',
            'Chirurgie Générale',
            'Médecine Interne'
        ],
        'Sciences Juridiques': [
            'Droit Civil',
            'Droit Pénal',
            'Droit Constitutionnel',
            'Droit International',
            'Droit des Affaires',
            'Procédure Civile',
            'Droit du Travail',
            'Droit Fiscal',
            'Droit de la Famille',
            'Criminologie'
        ],
        'Sciences Économiques et Gestion': [
            'Microéconomie',
            'Macroéconomie',
            'Comptabilité Générale',
            'Finance d\'Entreprise',
            'Marketing Stratégique',
            'Management des Organisations',
            'Statistiques Appliquées',
            'Économétrie',
            'Gestion des Ressources Humaines',
            'Commerce International'
        ]
    }
    
    created_count = 0
    universites = list(Universite.objects.all())
    
    for filiere_nom, cours_list in cours_par_filiere.items():
        try:
            filiere = Filiere.objects.get(nom=filiere_nom)
            for cours_nom in cours_list:
                for universite in universites[:3]:
                    cours, created = Course.objects.get_or_create(
                        nom=cours_nom,
                        filiere=filiere.nom,
                        university=universite.nom,
                        defaults={
                            'description': f'Cours de {cours_nom} en {filiere.nom} à {universite.nom}'
                        }
                    )
                    if created:
                        created_count += 1
        except Filiere.DoesNotExist:
            print(f"  ⚠️  Filière {filiere_nom} non trouvée")
    
    print(f"\n📊 {created_count} nouveaux cours créés")
    return Course.objects.all()

def create_users():
    """Crée des utilisateurs de test réalistes"""
    print_section("Création des Utilisateurs")
    
    users_data = [
        {
            'username': 'admin',
            'email': 'admin@resumeplus.cd',
            'first_name': 'Admin',
            'last_name': 'System',
            'password': 'AdminResume2024!',
            'groupe': 'ADMIN'
        },
        {
            'username': 'cp_info',
            'email': 'cp.info@unikin.cd',
            'first_name': 'Jean-Claude',
            'last_name': 'Mukendi',
            'password': 'CPInfo2024!',
            'groupe': 'CP',
            'filiere': 'Informatique et Technologies',
            'universite': 'Université de Kinshasa (UNIKIN)',
            'promotion': 'L3'
        },
        {
            'username': 'etudiant1',
            'email': 'etudiant1@gmail.com',
            'first_name': 'Prisca',
            'last_name': 'Kalala',
            'password': 'Etudiant2024!',
            'groupe': 'ETUDIANT',
            'filiere': 'Informatique et Technologies',
            'universite': 'Université de Kinshasa (UNIKIN)',
            'promotion': 'L2'
        },
        {
            'username': 'etudiant2',
            'email': 'etudiant2@gmail.com',
            'first_name': 'David',
            'last_name': 'Tshimanga',
            'password': 'Etudiant2024!',
            'groupe': 'ETUDIANT',
            'filiere': 'Sciences Économiques et Gestion',
            'universite': 'Institut Supérieur de Commerce (ISC)',
            'promotion': 'L1'
        }
    ]
    
    created_count = 0
    
    for user_data in users_data:
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults={
                'email': user_data['email'],
                'first_name': user_data['first_name'],
                'last_name': user_data['last_name'],
            }
        )
        
        if created:
            user.set_password(user_data['password'])
            user.save()
            created_count += 1
            
            profile_data = {'groupe': user_data['groupe']}
            
            if 'filiere' in user_data:
                try:
                    profile_data['filiere'] = Filiere.objects.get(nom=user_data['filiere'])
                except Filiere.DoesNotExist:
                    pass
            
            if 'universite' in user_data:
                try:
                    profile_data['universite'] = Universite.objects.get(nom=user_data['universite'])
                except Universite.DoesNotExist:
                    pass
            
            if 'promotion' in user_data:
                try:
                    profile_data['promotion'] = Promotion.objects.get(nom=user_data['promotion'])
                except Promotion.DoesNotExist:
                    pass
            
            UserProfile.objects.create(user=user, **profile_data)
            print(f"  ✅ {user_data['username']} ({user_data['groupe']})")
        else:
            print(f"  ℹ️  {user_data['username']} (existe déjà)")
    
    print(f"\n📊 {created_count} nouveaux utilisateurs créés")

def create_sessions_and_summaries():
    """Crée des sessions de cours et des résumés"""
    print_section("Création des Sessions et Résumés")
    
    courses = Course.objects.all()[:5]
    cp_users = User.objects.filter(profile__groupe='CP')
    
    sessions_created = 0
    summaries_created = 0
    
    for course in courses:
        for i in range(2, 4):
            session_date = timezone.now() - timedelta(days=i*7)
            
            session, created = Session.objects.get_or_create(
                course=course,
                date=session_date,
                defaults={
                    'professeur': f'Prof. {["Mukendi", "Kabila", "Tshisekedi"][i%3]}'
                }
            )
            
            if created:
                sessions_created += 1
                
                if cp_users.exists():
                    cp_user = cp_users.first()
                    
                    summary, created = Summary.objects.get_or_create(
                        titre=f'Résumé - {course.nom} - Session {i}',
                        course=course,
                        session=session,
                        defaults={
                            'texte_resume': f'''# Résumé du cours: {course.nom}
## Session du {session_date.strftime("%d/%m/%Y")}

### Points clés:
1. Introduction aux concepts fondamentaux
2. Développement théorique approfondi
3. Applications pratiques et exercices
4. Synthèse et récapitulatif

### Objectifs:
- Comprendre les bases
- Maîtriser les applications
- Développer l'esprit critique

*Résumé par: {cp_user.get_full_name()}*''',
                            'author_type': 'cp',
                            'author_user': cp_user,
                            'prix': Decimal('5.00'),
                            'is_free': False
                        }
                    )
                    
                    if created:
                        summaries_created += 1
    
    print(f"  ✅ {sessions_created} sessions créées")
    print(f"  ✅ {summaries_created} résumés créés")

def create_services():
    """Crée les services disponibles"""
    print_section("Création des Services")
    
    services_data = [
        {
            'nom': 'Accès Premium Mensuel',
            'description': 'Accès illimité à tous les résumés pendant 1 mois',
            'prix': Decimal('25.00')
        },
        {
            'nom': 'Accès Premium Annuel',
            'description': 'Accès illimité à tous les résumés pendant 1 an',
            'prix': Decimal('180.00')
        },
        {
            'nom': 'Résumé à l\'unité',
            'description': 'Achat d\'un résumé spécifique',
            'prix': Decimal('3.00')
        }
    ]
    
    created_count = 0
    for data in services_data:
        service, created = Service.objects.get_or_create(
            nom=data['nom'],
            defaults={
                'description': data['description'],
                'prix': data['prix']
            }
        )
        if created:
            print(f"  ✅ {data['nom']} - {data['prix']} USD")
            created_count += 1
        else:
            print(f"  ℹ️  {data['nom']} (existe déjà)")
    
    print(f"\n📊 {created_count} nouveaux services créés")

def display_statistics():
    """Affiche les statistiques"""
    print_header("STATISTIQUES")
    
    stats = {
        'Universités': Universite.objects.count(),
        'Filières': Filiere.objects.count(),
        'Promotions': Promotion.objects.count(),
        'Cours': Course.objects.count(),
        'Sessions': Session.objects.count(),
        'Résumés': Summary.objects.count(),
        'Services': Service.objects.count(),
        'Utilisateurs': User.objects.count(),
        'Profils': UserProfile.objects.count(),
    }
    
    for key, value in stats.items():
        print(f"📊 {key:<15}: {value:>3}")

def display_accounts():
    """Affiche les comptes de test"""
    print_header("COMPTES DE TEST")
    
    print("\n🔐 ADMINISTRATEUR:")
    print("   Email: admin@resumeplus.cd")
    print("   Password: AdminResume2024!")
    
    print("\n👨‍🏫 CHEF DE PROMOTION:")
    print("   Email: cp.info@unikin.cd")
    print("   Password: CPInfo2024!")
    
    print("\n👨‍🎓 ÉTUDIANTS:")
    print("   Email: etudiant1@gmail.com")
    print("   Password: Etudiant2024!")
    print("   Email: etudiant2@gmail.com")
    print("   Password: Etudiant2024!")

def main():
    """Fonction principale"""
    print_header("SEED DATABASE RESUME+")
    
    try:
        universites = create_universites()
        filieres = create_filieres()
        promotions = create_promotions()
        create_relations(universites, filieres, promotions)
        create_courses()
        create_users()
        create_sessions_and_summaries()
        create_services()
        display_statistics()
        display_accounts()
        
        print_header("✅ SUCCÈS!")
        print("🚀 Base de données initialisée avec succès!")
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()

# if __name__ == "__main__":
#     main()