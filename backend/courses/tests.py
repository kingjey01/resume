from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import UserProfile
from .models import Course, Session, Summary, Universite, Filiere, Promotion


class CourseModelTest(TestCase):
    def test_course_creation(self):
        course = Course.objects.create(
            nom='Test Course',
            filiere='Informatique',
            description='Test description',
            university='Test University'
        )
        self.assertEqual(str(course), 'Test Course - Informatique')


class SummaryAPITest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Créer un utilisateur pour les tests
        cls.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        # Créer un cours de test
        cls.course = Course.objects.create(
            nom='Test Course',
            filiere='Informatique',
            university='Test University'
        )
        
        # Créer un résumé de test
        cls.summary = Summary.objects.create(
            titre='Test Summary',
            texte_resume='Test content',
            course=cls.course,
            author_type='cp',
            author_user=cls.user
        )
    
    def test_summary_creation(self):
        # Vérifier que le résumé a été créé
        self.assertEqual(Summary.objects.count(), 1)
        summary = Summary.objects.first()
        self.assertEqual(summary.titre, 'Test Summary')
        self.assertEqual(summary.course, self.course)
        self.assertEqual(summary.author_user, self.user)


class FilierePromotionTest(TestCase):
    def setUp(self):
        self.filiere = Filiere.objects.create(
            nom='Informatique',
            description='Filière en informatique'
        )
        self.promotion = Promotion.objects.create(
            nom='L3',
            annee=2023
        )
    
    def test_relation_filiere_promotion_creation(self):
        self.filiere.promotions.add(self.promotion)
        
        # Vérifier la relation dans les deux sens
        self.assertIn(self.promotion, self.filiere.promotions.all())
        self.assertIn(self.filiere, self.promotion.filieres.all())


class CourseListNoNPlusOneTest(TestCase):
    """Tâche 60 — la liste des cours ne doit pas produire de N+1.

    Avant l'optimisation, 14 cours généraient 146 requêtes (~10 par cours).
    Après `_courses_optimises()`, le nombre de requêtes reste constant quel
    que soit le nombre de cours.
    """

    @classmethod
    def setUpTestData(cls):
        cls.universite = Universite.objects.create(nom='Université Test')
        cls.filiere = Filiere.objects.create(nom='Informatique')
        cls.promotion = Promotion.objects.create(nom='L3', annee=2025)

        cls.user = User.objects.create_user(
            username='t60_admin', password='testpass123'
        )
        cls.user.is_staff = True
        cls.user.is_superuser = True
        cls.user.save()
        UserProfile.objects.create(
            user=cls.user,
            groupe='ADMIN',
            universite=cls.universite,
            filiere=cls.filiere,
            promotion=cls.promotion,
        )

        for i in range(20):
            course = Course.objects.create(
                nom=f'Cours {i}',
                filiere='Informatique',
                university='Université Test',
            )
            course.universites.add(cls.universite)
            course.filieres.add(cls.filiere)
            course.promotions.add(cls.promotion)

        # `bulk_create` évite le signal post_save de Summary (notifications).
        Summary.objects.bulk_create([Summary(
            titre='Résumé IA de test',
            texte_resume='Contenu',
            course=Course.objects.get(nom='Cours 0'),
            author_type='ai',
        )])

    def test_course_list_query_count_is_constant(self):
        client = APIClient()
        token = str(RefreshToken.for_user(self.user).access_token)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        with CaptureQueriesContext(connection) as ctx:
            response = client.get('/api/course-list/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 20)

        # Silk peut être actif (ENABLE_SILK=True dans .env) : ses écritures
        # (silk_request, silk_sqlquery…), ses EXPLAIN d'analyse et les
        # SAVEPOINT du TestCase ne sont pas des requêtes de l'application.
        # On les exclut pour mesurer le N+1 réel.
        requetes_app = []
        for q in ctx.captured_queries:
            sql = q['sql'].strip().upper()
            if 'SILK_' in sql:
                continue
            if sql.startswith('EXPLAIN'):
                continue
            if sql.startswith('SAVEPOINT') or sql.startswith('RELEASE SAVEPOINT'):
                continue
            requetes_app.append(q)
        # 20 cours ne doivent pas produire 20 × N requêtes.
        self.assertLessEqual(len(requetes_app), 20)

        cours_ia = next(c for c in data if c['nom'] == 'Cours 0')
        cours_sans = next(c for c in data if c['nom'] == 'Cours 1')
        self.assertTrue(cours_ia['has_generic_summary'])
        self.assertFalse(cours_sans['has_generic_summary'])
        self.assertEqual(cours_ia['universites_noms'], ['Université Test'])
        self.assertEqual(cours_ia['filiere_nom'], 'Informatique')


class UniversiteFiliereM2MTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Créer des données de test
        cls.universite = Universite.objects.create(nom='Université de Test')
        cls.filiere = Filiere.objects.create(nom='Informatique')

    def test_relation_universite_filiere(self):
        # Vérifier que la relation peut être créée via le M2M auto
        self.universite.filieres.add(self.filiere)

        # Vérifier que la relation a été créée
        self.assertIn(self.filiere, self.universite.filieres.all())
        self.assertIn(self.universite, self.filiere.universites.all())
