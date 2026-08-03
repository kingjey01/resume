from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from users.models import UserProfile
from courses.models import Course, Session, Summary
from payments.models import Purchase
from datetime import datetime, timedelta
import random


class Command(BaseCommand):
    help = 'Créer des données fictives pour l\'application'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Création des données fictives...'))
        
        # Créer des utilisateurs
        self.create_users()
        
        # Créer des cours
        self.create_courses()
        
        # Créer des sessions
        self.create_sessions()
        
        # Créer des résumés
        self.create_summaries()
        
        # Créer des achats
        self.create_purchases()
        
        self.stdout.write(self.style.SUCCESS('Données fictives créées avec succès!'))

    def create_users(self):
        # Créer 3 CPs
        cp_data = [
            {'username': 'cp_alice', 'email': 'alice@cp.com', 'first_name': 'Alice', 'last_name': 'Martin'},
            {'username': 'cp_bob', 'email': 'bob@cp.com', 'first_name': 'Bob', 'last_name': 'Dupont'},
            {'username': 'cp_charlie', 'email': 'charlie@cp.com', 'first_name': 'Charlie', 'last_name': 'Durand'},
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
                user.set_password('password123')
                user.save()
                
                UserProfile.objects.create(
                    user=user,
                    role='cp',
                    phone=f'+33{random.randint(100000000, 999999999)}',
                    university='Université de Paris',
                    filiere='Informatique',
                    points=random.randint(50, 200)
                )
        
        # Créer quelques étudiants
        student_data = [
            {'username': 'student1', 'email': 'student1@univ.com', 'first_name': 'Marie', 'last_name': 'Leroy'},
            {'username': 'student2', 'email': 'student2@univ.com', 'first_name': 'Pierre', 'last_name': 'Bernard'},
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
                user.set_password('password123')
                user.save()
                
                UserProfile.objects.create(
                    user=user,
                    role='student',
                    phone=f'+33{random.randint(100000000, 999999999)}',
                    university='Université de Paris',
                    filiere='Informatique',
                    points=random.randint(0, 50)
                )

    def create_courses(self):
        courses_data = [
            {'nom': 'Programmation Python', 'filiere': 'Informatique', 'description': 'Cours de base en Python'},
            {'nom': 'Base de données', 'filiere': 'Informatique', 'description': 'Introduction aux bases de données'},
            {'nom': 'Algorithmes et structures de données', 'filiere': 'Informatique', 'description': 'Algorithmes fondamentaux'},
            {'nom': 'Développement Web', 'filiere': 'Informatique', 'description': 'HTML, CSS, JavaScript'},
            {'nom': 'Intelligence Artificielle', 'filiere': 'Informatique', 'description': 'Introduction à l\'IA'},
        ]
        
        for data in courses_data:
            Course.objects.get_or_create(
                nom=data['nom'],
                defaults={
                    'filiere': data['filiere'],
                    'description': data['description'],
                    'university': 'Université de Paris'
                }
            )

    def create_sessions(self):
        courses = Course.objects.all()
        professeurs = ['Prof. Martin', 'Prof. Dubois', 'Prof. Moreau', 'Prof. Laurent']
        
        for course in courses:
            for i in range(3):  # 3 sessions par cours
                Session.objects.get_or_create(
                    course=course,
                    date=datetime.now() - timedelta(days=random.randint(1, 30)),
                    defaults={
                        'professeur': random.choice(professeurs)
                    }
                )

    def create_summaries(self):
        courses = Course.objects.all()
        cps = User.objects.filter(profile__role='cp')
        
        summary_templates = [
            "Ce résumé couvre les concepts fondamentaux du cours {}. Les points clés incluent les définitions de base, les méthodes principales et les applications pratiques.",
            "Résumé détaillé du cours {} abordant les théories essentielles, les exemples concrets et les exercices pratiques vus en classe.",
            "Synthèse complète du cours {} avec focus sur les éléments importants pour l'examen et les projets à venir."
        ]
        
        for course in courses:
            # Créer 3-5 résumés par cours
            for i in range(random.randint(3, 5)):
                author_type = random.choice(['cp', 'ai'])
                author_user = random.choice(cps) if author_type == 'cp' else None
                
                Summary.objects.get_or_create(
                    titre=f"Résumé {i+1} - {course.nom}",
                    defaults={
                        'texte_resume': random.choice(summary_templates).format(course.nom),
                        'course': course,
                        'author_type': author_type,
                        'author_user': author_user,
                        'prix': random.choice([0.00, 2.99, 4.99, 7.99]) if author_type == 'cp' else 0.00,
                        'is_free': author_type == 'ai' or random.choice([True, False])
                    }
                )

    def create_purchases(self):
        students = User.objects.filter(profile__role='student')
        paid_summaries = Summary.objects.filter(prix__gt=0, is_free=False)
        
        for student in students:
            # Chaque étudiant achète 1-3 résumés
            for _ in range(random.randint(1, 3)):
                summary = random.choice(paid_summaries)
                Purchase.objects.get_or_create(
                    user=student,
                    summary=summary,
                    defaults={
                        'amount': summary.prix,
                        'payment_method': random.choice(['mobile_money', 'card']),
                        'status': random.choice(['completed', 'pending']),
                        'transaction_id': f'TXN_{random.randint(100000, 999999)}'
                    }
                )
