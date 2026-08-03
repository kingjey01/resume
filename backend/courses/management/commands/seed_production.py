"""
Commande de seed pour la production Resume+
Crée les données de base : universités, filières, promotions, cours et utilisateurs
"""
from django.core.management.base import BaseCommand
from decimal import Decimal
from django.contrib.auth.models import User
from users.models import UserProfile
from courses.models import (
    Course, Session, Summary,
    Universite, Filiere, Promotion,
    Professeur
)
from payments.models import Service
from datetime import datetime, timedelta
import random


class Command(BaseCommand):
    help = 'Créer les données de base pour la production'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Supprimer les données existantes avant de créer les nouvelles',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('=== SEED PRODUCTION Resume+ ==='))
        
        if options['clear']:
            self.stdout.write(self.style.WARNING('Suppression des données existantes...'))
            self.clear_data()
        
        # 1. Créer les promotions
        self.create_promotions()
        
        # 2. Créer les filières
        self.create_filieres()
        
        # 3. Créer les universités
        self.create_universites()
        
        # 4. Créer les cours
        self.create_courses()
        
        # 5. Créer les utilisateurs (admin, CP, étudiants)
        self.create_users()
        
        # 6. Créer les professeurs
        self.create_professeurs()
        
        # 7. Créer les services d'abonnement pour FlexPay
        self.create_services()
        
        # 8. Créer quelques résumés exemples
        self.create_sample_summaries()
        
        self.stdout.write(self.style.SUCCESS('=== SEED TERMINÉ AVEC SUCCÈS ==='))

    def clear_data(self):
        """Supprime les données existantes (sauf superuser)"""
        Summary.objects.all().delete()
        Session.objects.all().delete()
        Professeur.objects.all().delete()
        Course.objects.all().delete()
        Universite.objects.all().delete()
        Filiere.objects.all().delete()
        Promotion.objects.all().delete()
        UserProfile.objects.exclude(user__is_superuser=True).delete()
        User.objects.filter(is_superuser=False).delete()
        self.stdout.write(self.style.SUCCESS('Données supprimées'))

    def create_promotions(self):
        """Créer les promotions universitaires"""
        self.stdout.write('Création des promotions...')
        
        promotions_data = [
            {'nom': 'L1', 'annee': 2024},
            {'nom': 'L2', 'annee': 2024},
            {'nom': 'L3', 'annee': 2024},
            {'nom': 'M1', 'annee': 2024},
            {'nom': 'M2', 'annee': 2024},
        ]
        
        for data in promotions_data:
            promo, created = Promotion.objects.get_or_create(
                nom=data['nom'],
                defaults={'annee': data['annee']}
            )
            status = 'créée' if created else 'existante'
            self.stdout.write(f"  - Promotion {promo.nom}: {status}")

    def create_filieres(self):
        """Créer les filières"""
        self.stdout.write('Création des filières...')
        
        filieres_data = [
            {'nom': 'Informatique', 'description': 'Sciences informatiques et technologies'},
            {'nom': 'Droit', 'description': 'Sciences juridiques'},
            {'nom': 'Médecine', 'description': 'Sciences médicales'},
            {'nom': 'Économie', 'description': 'Sciences économiques et gestion'},
            {'nom': 'Lettres', 'description': 'Lettres et sciences humaines'},
            {'nom': 'Sciences', 'description': 'Sciences exactes et naturelles'},
        ]
        
        promotions = list(Promotion.objects.all())
        
        for data in filieres_data:
            filiere, created = Filiere.objects.get_or_create(
                nom=data['nom'],
                defaults={'description': data['description']}
            )
            status = 'créée' if created else 'existante'
            self.stdout.write(f"  - Filière {filiere.nom}: {status}")
            
            # Associer toutes les promotions à chaque filière
            filiere.promotions.add(*promotions)

    def create_universites(self):
        """Créer les universités"""
        self.stdout.write('Création des universités...')
        
        universites_data = [
            {'nom': 'Université de Kinshasa (UNIKIN)', 'adresse': 'Kinshasa, RDC'},
            {'nom': 'Université de Lubumbashi (UNILU)', 'adresse': 'Lubumbashi, RDC'},
            {'nom': 'Université Catholique du Congo (UCC)', 'adresse': 'Kinshasa, RDC'},
            {'nom': 'Université Protestante au Congo (UPC)', 'adresse': 'Kinshasa, RDC'},
            {'nom': 'Institut Supérieur de Commerce (ISC)', 'adresse': 'Kinshasa, RDC'},
        ]
        
        filieres = list(Filiere.objects.all())
        
        for data in universites_data:
            univ, created = Universite.objects.get_or_create(
                nom=data['nom'],
                defaults={'adresse': data['adresse']}
            )
            status = 'créée' if created else 'existante'
            self.stdout.write(f"  - Université {univ.nom}: {status}")
            
            # Associer toutes les filières à chaque université
            univ.filieres.add(*filieres)

    def create_courses(self):
        """Créer les cours"""
        self.stdout.write('Création des cours...')
        
        courses_data = [
            # Informatique
            {'nom': 'Programmation Python', 'filiere': 'Informatique', 'university': 'UNIKIN', 'description': 'Introduction à la programmation avec Python'},
            {'nom': 'Base de données', 'filiere': 'Informatique', 'university': 'UNIKIN', 'description': 'Conception et gestion des bases de données'},
            {'nom': 'Algorithmes', 'filiere': 'Informatique', 'university': 'UNIKIN', 'description': 'Algorithmes et structures de données'},
            {'nom': 'Développement Web', 'filiere': 'Informatique', 'university': 'UNIKIN', 'description': 'HTML, CSS, JavaScript et frameworks'},
            {'nom': 'Réseaux informatiques', 'filiere': 'Informatique', 'university': 'UNIKIN', 'description': 'Architecture et protocoles réseaux'},
            
            # Droit
            {'nom': 'Droit civil', 'filiere': 'Droit', 'university': 'UNIKIN', 'description': 'Principes fondamentaux du droit civil'},
            {'nom': 'Droit des affaires', 'filiere': 'Droit', 'university': 'UNIKIN', 'description': 'Droit commercial et des sociétés'},
            {'nom': 'Droit constitutionnel', 'filiere': 'Droit', 'university': 'UNIKIN', 'description': 'Organisation des pouvoirs publics'},
            
            # Médecine
            {'nom': 'Anatomie', 'filiere': 'Médecine', 'university': 'UNIKIN', 'description': 'Anatomie du corps humain'},
            {'nom': 'Physiologie', 'filiere': 'Médecine', 'university': 'UNIKIN', 'description': 'Fonctionnement des organes'},
            {'nom': 'Biochimie', 'filiere': 'Médecine', 'university': 'UNIKIN', 'description': 'Chimie du vivant'},
            
            # Économie
            {'nom': 'Microéconomie', 'filiere': 'Économie', 'university': 'UNIKIN', 'description': 'Comportement des agents économiques'},
            {'nom': 'Macroéconomie', 'filiere': 'Économie', 'university': 'UNIKIN', 'description': 'Économie à l\'échelle nationale'},
            {'nom': 'Comptabilité générale', 'filiere': 'Économie', 'university': 'UNIKIN', 'description': 'Principes comptables de base'},
        ]
        
        for data in courses_data:
            course, created = Course.objects.get_or_create(
                nom=data['nom'],
                filiere=data['filiere'],
                defaults={
                    'university': data['university'],
                    'description': data['description']
                }
            )
            status = 'créé' if created else 'existant'
            self.stdout.write(f"  - Cours {course.nom}: {status}")

    def create_users(self):
        """Créer les utilisateurs de test"""
        self.stdout.write('Création des utilisateurs...')
        
        # Récupérer une université et filière pour les profils
        universite = Universite.objects.first()
        filiere = Filiere.objects.first()
        promotion = Promotion.objects.first()
        
        # Admin
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@resumeplus.com',
                'first_name': 'Admin',
                'last_name': 'Resume+',
                'is_staff': True
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            UserProfile.objects.create(
                user=admin_user,
                groupe='ADMIN',
                phone='+243999000001',
                universite=universite,
                filiere=filiere,
                promotion=promotion,
                points=1000
            )
            self.stdout.write(self.style.SUCCESS(f"  - Admin créé: admin / admin123"))
        else:
            self.stdout.write(f"  - Admin existant")
        
        # CPs (Chefs de Promotion)
        cp_data = [
            {'username': 'cp_jean', 'email': 'jean@resumeplus.com', 'first_name': 'Jean', 'last_name': 'Mukendi'},
            {'username': 'cp_marie', 'email': 'marie@resumeplus.com', 'first_name': 'Marie', 'last_name': 'Kabongo'},
        ]
        
        for data in cp_data:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email': data['email'],
                    'first_name': data['first_name'],
                    'last_name': data['last_name']
                }
            )
            if created:
                user.set_password('cp123456')
                user.save()
                UserProfile.objects.create(
                    user=user,
                    groupe='CP',
                    phone=f'+243{random.randint(800000000, 899999999)}',
                    universite=universite,
                    filiere=filiere,
                    promotion=promotion,
                    points=random.randint(100, 500)
                )
                self.stdout.write(self.style.SUCCESS(f"  - CP créé: {data['username']} / cp123456"))
            else:
                self.stdout.write(f"  - CP existant: {data['username']}")
        
        # Étudiants
        student_data = [
            {'username': 'etudiant1', 'email': 'etudiant1@resumeplus.com', 'first_name': 'Patrick', 'last_name': 'Mwamba'},
            {'username': 'etudiant2', 'email': 'etudiant2@resumeplus.com', 'first_name': 'Grace', 'last_name': 'Lukusa'},
        ]
        
        for data in student_data:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email': data['email'],
                    'first_name': data['first_name'],
                    'last_name': data['last_name']
                }
            )
            if created:
                user.set_password('etudiant123')
                user.save()
                UserProfile.objects.create(
                    user=user,
                    groupe='ETUDIANT',
                    phone=f'+243{random.randint(800000000, 899999999)}',
                    universite=universite,
                    filiere=filiere,
                    promotion=promotion,
                    points=random.randint(0, 100)
                )
                self.stdout.write(self.style.SUCCESS(f"  - Étudiant créé: {data['username']} / etudiant123"))
            else:
                self.stdout.write(f"  - Étudiant existant: {data['username']}")

    def create_professeurs(self):
        """Créer les professeurs de test"""
        self.stdout.write('Création des professeurs...')
        
        universite = Universite.objects.first()
        filieres = list(Filiere.objects.all()[:3])  # 3 premières filières
        
        if not universite:
            self.stdout.write(self.style.WARNING('  Aucune université trouvée, professeurs non créés'))
            return
        
        professeurs_data = [
            {
                'username': 'prof_dr_mukendi',
                'email': 'mukendi@resumeplus.com',
                'first_name': 'Jean',
                'last_name': 'Mukendi',
                'specialite': 'Intelligence Artificielle',
                'telephone': '+243810000001'
            },
            {
                'username': 'prof_dr_kabongo',
                'email': 'kabongo@resumeplus.com',
                'first_name': 'Marie',
                'last_name': 'Kabongo',
                'specialite': 'Droit Constitutionnel',
                'telephone': '+243820000002'
            },
            {
                'username': 'prof_dr_mwamba',
                'email': 'mwamba@resumeplus.com',
                'first_name': 'Patrick',
                'last_name': 'Mwamba',
                'specialite': 'Médecine Interne',
                'telephone': '+243830000003'
            },
            {
                'username': 'prof_dr_lukusa',
                'email': 'lukusa@resumeplus.com',
                'first_name': 'Grace',
                'last_name': 'Lukusa',
                'specialite': 'Économétrie',
                'telephone': '+243840000004'
            },
        ]
        
        for data in professeurs_data:
            # Créer l'utilisateur
            user, user_created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email': data['email'],
                    'first_name': data['first_name'],
                    'last_name': data['last_name']
                }
            )
            if user_created:
                user.set_password('prof123456')
                user.save()
            
            # Créer le professeur
            professeur, prof_created = Professeur.objects.get_or_create(
                user=user,
                defaults={
                    'universite': universite,
                    'specialite': data['specialite'],
                    'telephone': data['telephone'],
                    'is_active': True
                }
            )
            
            # Associer les filières
            if prof_created:
                professeur.filieres.set(filieres)
                self.stdout.write(self.style.SUCCESS(f"  - Professeur créé: {data['first_name']} {data['last_name']} ({data['specialite']})"))
            else:
                self.stdout.write(f"  - Professeur existant: {data['first_name']} {data['last_name']}")

    def create_services(self):
        """Créer les services d'abonnement pour FlexPay"""
        self.stdout.write('Création des services d\'abonnement...')
        
        services_data = [
            {
                'nom': 'Abonnement Basic',
                'description': 'Accès à 5 résumés par mois',
                'type': 'basic',
                'price': Decimal('5000.00'),
                'currency': 'CDF',
                'duree_mois': 1,
                'features': ['5 résumés par mois', 'Support email', 'Accès aux résumés gratuits']
            },
            {
                'nom': 'Abonnement Premium',
                'description': 'Accès illimité à tous les résumés',
                'type': 'premium',
                'price': Decimal('15000.00'),
                'currency': 'CDF',
                'duree_mois': 1,
                'features': ['Résumés illimités', 'Support prioritaire', 'Accès aux PDF', 'Lecture audio']
            },
            {
                'nom': 'Abonnement VIP',
                'description': 'Accès illimité + fonctionnalités premium',
                'type': 'vip',
                'price': Decimal('35000.00'),
                'currency': 'CDF',
                'duree_mois': 3,
                'features': ['Résumés illimités', 'Support 24/7', 'PDF', 'Audio', 'Hors ligne', 'Partage']
            },
        ]
        
        for data in services_data:
            service, created = Service.objects.get_or_create(
                nom=data['nom'],
                defaults={
                    'description': data['description'],
                    'type': data['type'],
                    'price': data['price'],
                    'currency': data['currency'],
                    'duree_mois': data['duree_mois'],
                    'features': data['features'],
                    'is_active': True
                }
            )
            status = 'créé' if created else 'existant'
            self.stdout.write(f"  - Service {service.nom}: {status}")

    def create_sample_summaries(self):
        """Créer quelques résumés exemples"""
        self.stdout.write('Création des résumés exemples...')
        
        courses = Course.objects.all()[:5]  # 5 premiers cours
        cps = User.objects.filter(profile__groupe='CP')
        professeurs = list(Professeur.objects.filter(is_active=True))
        
        if not cps.exists():
            self.stdout.write(self.style.WARNING('  Aucun CP trouvé, résumés non créés'))
            return
        
        if not professeurs:
            self.stdout.write(self.style.WARNING('  Aucun professeur trouvé, résumés non créés'))
            return
        
        summary_templates = [
            "Ce résumé couvre les concepts fondamentaux du cours {}. Les points clés incluent les définitions de base, les méthodes principales et les applications pratiques.",
            "Résumé détaillé du cours {} abordant les théories essentielles, les exemples concrets et les exercices pratiques vus en classe.",
            "Synthèse complète du cours {} avec focus sur les éléments importants pour l'examen et les projets à venir."
        ]
        
        for course in courses:
            for i in range(2):  # 2 résumés par cours
                author = random.choice(list(cps))
                professeur = random.choice(professeurs)
                prix = random.choice([0, 500, 1000, 2000])
                
                summary, created = Summary.objects.get_or_create(
                    titre=f"Résumé {i+1} - {course.nom}",
                    course=course,
                    defaults={
                        'texte_resume': random.choice(summary_templates).format(course.nom),
                        'author_type': 'cp',
                        'author_user': author,
                        'professeur': professeur,
                        'prix': prix,
                        'is_free': prix == 0
                    }
                )
                if created:
                    self.stdout.write(f"  - Résumé créé: {summary.titre} (Prof: {professeur.user.get_full_name()})")
