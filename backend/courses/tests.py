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
from payments.models import Purchase
from .models import Course, Session, Summary, Universite, Filiere, Promotion


def _requetes_app(captured):
    """Retire les requêtes d'instrumentation Silk et les commandes du TestCase."""
    result = []
    for q in captured:
        sql = q['sql'].strip().upper()
        if 'SILK_' in sql or sql.startswith('EXPLAIN'):
            continue
        if sql.startswith('SAVEPOINT') or sql.startswith('RELEASE SAVEPOINT'):
            continue
        result.append(q)
    return result


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

        requetes_app = _requetes_app(ctx.captured_queries)
        # 20 cours ne doivent pas produire 20 × N requêtes.
        self.assertLessEqual(len(requetes_app), 20)

        cours_ia = next(c for c in data if c['nom'] == 'Cours 0')
        cours_sans = next(c for c in data if c['nom'] == 'Cours 1')
        self.assertTrue(cours_ia['has_generic_summary'])
        self.assertFalse(cours_sans['has_generic_summary'])
        self.assertEqual(cours_ia['universites_noms'], ['Université Test'])
        self.assertEqual(cours_ia['filiere_nom'], 'Informatique')


class SummaryListNoNPlusOneTest(TestCase):
    """Tâche 60 — la liste des résumés ne doit pas produire de N+1.

    Avant : 70 requêtes pour 10 résumés (~7 par résumé, dont un
    `Purchase.exists()` et les relations course/auteur/professeur).
    Après : select_related + prefetch + un seul set d'IDs achetés.
    """

    @classmethod
    def setUpTestData(cls):
        cls.universite = Universite.objects.create(nom='Université Test')
        cls.filiere = Filiere.objects.create(nom='Informatique')
        cls.promotion = Promotion.objects.create(nom='L3', annee=2025)

        cls.user = User.objects.create_user(
            username='t60_sum_admin', password='testpass123'
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

        cls.course = Course.objects.create(
            nom='Cours résumé',
            filiere='Informatique',
            university='Université Test',
        )
        cls.course.universites.add(cls.universite)
        cls.course.filieres.add(cls.filiere)
        cls.course.promotions.add(cls.promotion)

        # `bulk_create` évite les signaux de notification par résumé.
        Summary.objects.bulk_create([
            Summary(
                titre=f'Résumé {i}',
                texte_resume='Contenu du résumé. ' * 20,
                course=cls.course,
                author_type='cp',
                is_validated=True,
            )
            for i in range(20)
        ])
        cls.achete = Summary.objects.get(titre='Résumé 0')
        Purchase.objects.bulk_create([Purchase(
            user=cls.user,
            summary=cls.achete,
            amount=0,
            payment_method='mobile_money',
            status='completed',
            transaction_id=None,
        )])

    def test_summary_list_query_count_is_constant(self):
        client = APIClient()
        token = str(RefreshToken.for_user(self.user).access_token)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        with CaptureQueriesContext(connection) as ctx:
            response = client.get('/api/summaries/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 20)

        requetes_app = _requetes_app(ctx.captured_queries)
        self.assertLessEqual(len(requetes_app), 20)

        achete = next(s for s in data if s['titre'] == 'Résumé 0')
        autre = next(s for s in data if s['titre'] == 'Résumé 1')
        self.assertTrue(achete['is_purchased'])
        self.assertFalse(autre['is_purchased'])
        self.assertEqual(achete['filiere_name'], 'Informatique')


class ReferenceDataNoNPlusOneTest(TestCase):
    """Tâche 60 — universités/filières/promotions sans N+1."""

    @classmethod
    def setUpTestData(cls):
        cls.universites = [
            Universite.objects.create(nom=f'Université {i}') for i in range(5)
        ]
        cls.filieres = [
            Filiere.objects.create(nom=f'Filière {i}') for i in range(6)
        ]
        cls.promotions = [
            Promotion.objects.create(nom=f'Promotion {i}', annee=2025)
            for i in range(5)
        ]
        for universite in cls.universites:
            for filiere in cls.filieres:
                universite.filieres.add(filiere)
        for filiere in cls.filieres:
            for promotion in cls.promotions:
                filiere.promotions.add(promotion)

    def _get(self, url):
        with CaptureQueriesContext(connection) as ctx:
            response = APIClient().get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response, _requetes_app(ctx.captured_queries)

    def test_universites_list(self):
        response, queries = self._get('/api/courses/universites/')
        self.assertEqual(len(response.json()), 5)
        self.assertLessEqual(len(queries), 20)

    def test_filieres_list(self):
        response, queries = self._get('/api/courses/filieres/')
        self.assertEqual(len(response.json()), 6)
        self.assertLessEqual(len(queries), 20)

    def test_universite_filieres_action(self):
        response, queries = self._get(
            f'/api/courses/universites/{self.universites[0].id}/filieres/'
        )
        self.assertEqual(len(response.json()), 6)
        self.assertLessEqual(len(queries), 20)

    def test_filiere_promotions_action(self):
        response, queries = self._get(
            f'/api/courses/filieres/{self.filieres[0].id}/promotions/'
        )
        self.assertEqual(len(response.json()), 5)
        self.assertLessEqual(len(queries), 20)

    def test_promotion_filieres_action(self):
        response, queries = self._get(
            f'/api/courses/promotions/{self.promotions[0].id}/filieres/'
        )
        self.assertEqual(len(response.json()), 6)
        self.assertLessEqual(len(queries), 20)


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
