from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
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
