from unittest.mock import patch

from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.core.cache import caches
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import UserProfile
from payments.models import Purchase
from .cache_catalogue import (
    cache_get_safe,
    cache_set_safe,
    cle_catalogue,
    invalider_catalogue,
    version_catalogue,
)
from .models import Course, Session, Summary, Universite, Filiere, Promotion


LOCMEM_CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 't60-default',
    },
    'catalog': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 't60-catalog',
    },
    'fallback': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 't60-fallback',
    },
}


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


@override_settings(CACHES=LOCMEM_CACHES, ENABLE_CATALOG_CACHE=True)
class CatalogCacheTest(TestCase):
    """Tâche 60, axe 3 — mécanique du cache catalogue (sans Redis)."""

    def setUp(self):
        caches['catalog'].clear()
        caches['default'].clear()

    def test_version_et_cle_versionnee(self):
        version = version_catalogue()
        cle = cle_catalogue('refs', 'universites')
        self.assertTrue(cle.startswith(f'catalog:{version}:'))

        invalider_catalogue()
        self.assertEqual(version_catalogue(), version + 1)
        self.assertFalse(
            cle_catalogue('refs', 'universites').startswith(f'catalog:{version}:')
        )

    def test_get_set(self):
        cle = cle_catalogue('test')
        self.assertIsNone(cache_get_safe(cle))
        cache_set_safe(cle, {'a': 1}, timeout=60)
        self.assertEqual(cache_get_safe(cle), {'a': 1})

    def test_redis_indisponible_ne_leve_pas(self):
        class CacheIndisponible:
            def get(self, *args, **kwargs):
                raise RuntimeError('down')

            def set(self, *args, **kwargs):
                raise RuntimeError('down')

            def incr(self, *args, **kwargs):
                raise RuntimeError('down')

        with patch(
            'courses.cache_catalogue._cache',
            return_value=CacheIndisponible(),
        ):
            self.assertIsNone(cache_get_safe('x'))
            cache_set_safe('x', 1)
            invalider_catalogue()  # ne doit pas lever

    def test_signal_save_invalide(self):
        version = version_catalogue()
        Universite.objects.create(nom='Université cache')
        self.assertGreater(version_catalogue(), version)

    def test_signal_m2m_invalide(self):
        universite = Universite.objects.create(nom='U m2m')
        filiere = Filiere.objects.create(nom='F m2m')
        version = version_catalogue()
        universite.filieres.add(filiere)
        self.assertGreater(version_catalogue(), version)


@override_settings(CACHES=LOCMEM_CACHES, ENABLE_CATALOG_CACHE=True)
class ReferenceEndpointsCacheTest(TestCase):
    """Tâche 60, axe 3 — HIT/MISS et invalidation sur les référentiels."""

    @classmethod
    def setUpTestData(cls):
        cls.universite = Universite.objects.create(nom='Université cache')
        cls.filiere = Filiere.objects.create(nom='Filière cache')
        cls.promotion = Promotion.objects.create(nom='Promotion cache', annee=2025)
        cls.universite.filieres.add(cls.filiere)
        cls.filiere.promotions.add(cls.promotion)

    def setUp(self):
        caches['catalog'].clear()
        caches['default'].clear()

    def test_list_hit_miss_et_invalidation(self):
        client = APIClient()

        premiere = client.get('/api/courses/universites/')
        self.assertEqual(premiere.status_code, 200)
        self.assertEqual(premiere['X-Catalog-Cache'], 'MISS')
        donnees = premiere.json()

        with CaptureQueriesContext(connection) as ctx:
            deuxieme = client.get('/api/courses/universites/')
        self.assertEqual(deuxieme.status_code, 200)
        self.assertEqual(deuxieme['X-Catalog-Cache'], 'HIT')
        self.assertEqual(deuxieme.json(), donnees)
        self.assertEqual(len(_requetes_app(ctx.captured_queries)), 0)

        # Une écriture invalide la version : la clé change → MISS.
        Universite.objects.create(nom='Nouvelle université')
        troisieme = client.get('/api/courses/universites/')
        self.assertEqual(troisieme['X-Catalog-Cache'], 'MISS')

    def test_action_filieres_hit(self):
        client = APIClient()
        url = f'/api/courses/universites/{self.universite.id}/filieres/'

        premiere = client.get(url)
        self.assertEqual(premiere['X-Catalog-Cache'], 'MISS')
        deuxieme = client.get(url)
        self.assertEqual(deuxieme['X-Catalog-Cache'], 'HIT')
        self.assertEqual(deuxieme.json(), premiere.json())


@override_settings(CACHES=LOCMEM_CACHES, ENABLE_CATALOG_CACHE=True)
class CourseListCacheTest(TestCase):
    """Tâche 60, axe 3 — cache de la liste des cours par cohorte."""

    @classmethod
    def setUpTestData(cls):
        cls.universite = Universite.objects.create(nom='Université A')
        cls.filiere = Filiere.objects.create(nom='Filière A')
        cls.promotion = Promotion.objects.create(nom='Promo A', annee=2025)

        cls.admin = User.objects.create_user(
            username='t60_cache_admin', password='testpass123'
        )
        cls.admin.is_staff = True
        cls.admin.is_superuser = True
        cls.admin.save()
        UserProfile.objects.create(
            user=cls.admin,
            groupe='ADMIN',
            universite=cls.universite,
            filiere=cls.filiere,
            promotion=cls.promotion,
        )

        for i in range(3):
            course = Course.objects.create(
                nom=f'Cours cache {i}',
                filiere='Filière A',
                university='Université A',
            )
            course.universites.add(cls.universite)
            course.filieres.add(cls.filiere)
            course.promotions.add(cls.promotion)

        # Deuxième cohorte, pour vérifier que les clés ne sont pas partagées.
        cls.universite_b = Universite.objects.create(nom='Université B')
        cls.filiere_b = Filiere.objects.create(nom='Filière B')
        cls.promotion_b = Promotion.objects.create(nom='Promo B', annee=2025)
        cls.etudiant_b = User.objects.create_user(
            username='t60_cache_etudiant_b', password='testpass123'
        )
        UserProfile.objects.create(
            user=cls.etudiant_b,
            groupe='ETUDIANT',
            universite=cls.universite_b,
            filiere=cls.filiere_b,
            promotion=cls.promotion_b,
        )
        cls.cours_b = Course.objects.create(
            nom='Cours exclusif B',
            filiere='Filière B',
            university='Université B',
        )
        cls.cours_b.universites.add(cls.universite_b)
        cls.cours_b.filieres.add(cls.filiere_b)
        cls.cours_b.promotions.add(cls.promotion_b)

    def setUp(self):
        caches['catalog'].clear()
        caches['default'].clear()

    def _client(self, user):
        client = APIClient()
        token = str(RefreshToken.for_user(user).access_token)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        return client

    def test_hit_miss_et_invalidation(self):
        client = self._client(self.admin)

        premiere = client.get('/api/course-list/')
        self.assertEqual(premiere.status_code, 200)
        self.assertEqual(premiere['X-Catalog-Cache'], 'MISS')
        donnees = premiere.json()

        with CaptureQueriesContext(connection) as ctx:
            deuxieme = client.get('/api/course-list/')
        self.assertEqual(deuxieme['X-Catalog-Cache'], 'HIT')
        self.assertEqual(deuxieme.json(), donnees)

        # L'authentification et la permission relisent l'utilisateur/le profil
        # (5 requêtes, incompressibles ici). En revanche, la liste des cours
        # elle-même ne doit plus être interrogée.
        requetes_hit = _requetes_app(ctx.captured_queries)
        self.assertLessEqual(len(requetes_hit), 5)
        self.assertFalse(any(
            'courses_course' in q['sql'].lower() for q in requetes_hit
        ))

        # Un nouveau cours invalide la version globale.
        Course.objects.create(
            nom='Cours ajouté',
            filiere='Filière A',
            university='Université A',
        )
        troisieme = client.get('/api/course-list/')
        self.assertEqual(troisieme['X-Catalog-Cache'], 'MISS')

    def test_cohortes_differentes_ne_partagent_pas(self):
        client = self._client(self.etudiant_b)

        premiere = client.get('/api/course-list/')
        self.assertEqual(premiere.status_code, 200)
        self.assertEqual(premiere['X-Catalog-Cache'], 'MISS')
        donnees = premiere.json()
        self.assertEqual([c['nom'] for c in donnees], ['Cours exclusif B'])

        deuxieme = client.get('/api/course-list/')
        self.assertEqual(deuxieme['X-Catalog-Cache'], 'HIT')
        self.assertEqual(deuxieme.json(), donnees)


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
