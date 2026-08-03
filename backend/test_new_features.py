#!/usr/bin/env python
"""
Script de test pour toutes les nouvelles fonctionnalités de Résumé+
- Authentification OTP
- Service d'exercices
- Validation des résumés
- Badges de distinction
"""
import os
import sys
import django
import json
import requests
from datetime import datetime, timedelta

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from users.models import UserProfile
from courses.models import Service, Abonnement, Summary, Course, Exercise, ExerciseQuestion
from courses.exercise_generator import generate_exercises_for_summary

class FeatureTestSuite:
    """Suite de tests pour les nouvelles fonctionnalités"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000/api"
        self.test_results = []
        
    def log_test(self, test_name, success, message=""):
        """Enregistre le résultat d'un test"""
        status = "[PASS]" if success else "[FAIL]"
        self.test_results.append({
            'name': test_name,
            'success': success,
            'message': message
        })
        print(f"{status} {test_name}: {message}")
    
    def test_otp_system(self):
        """Test du système OTP"""
        print("\n=== TEST SYSTÈME OTP ===")
        
        try:
            # Créer un utilisateur de test
            user, created = User.objects.get_or_create(
                username='test_otp_user',
                defaults={'email': 'test@example.com'}
            )
            
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={'phone': '+243123456789', 'groupe': 'ETUDIANT'}
            )
            
            # Test génération OTP
            otp_code = profile.generate_otp()
            self.log_test("Génération OTP", otp_code == "1234", f"Code généré: {otp_code}")
            
            # Test vérification OTP valide
            is_valid = profile.verify_otp("1234")
            self.log_test("Vérification OTP valide", is_valid, "Code 1234 accepté")
            
            # Test vérification OTP invalide
            profile.generate_otp()  # Régénérer
            is_invalid = not profile.verify_otp("0000")
            self.log_test("Vérification OTP invalide", is_invalid, "Code 0000 rejeté")
            
        except Exception as e:
            self.log_test("Système OTP", False, f"Erreur: {str(e)}")
    
    def test_exercise_service(self):
        """Test du service d'exercices"""
        print("\n=== TEST SERVICE EXERCICES ===")
        
        try:
            # Vérifier que le service d'exercices existe et est actif
            exercise_service = Service.objects.filter(nom="Exercices", is_active=True).first()
            self.log_test("Service Exercices actif", exercise_service is not None, 
                         f"Service trouvé: {exercise_service.nom if exercise_service else 'Aucun'}")
            
            # Vérifier que les autres services sont suspendus
            suspended_count = Service.objects.filter(is_active=False).count()
            self.log_test("Autres services suspendus", suspended_count > 0, 
                         f"{suspended_count} services suspendus")
            
        except Exception as e:
            self.log_test("Service Exercices", False, f"Erreur: {str(e)}")
    
    def test_summary_validation(self):
        """Test du système de validation des résumés"""
        print("\n=== TEST VALIDATION RÉSUMÉS ===")
        
        try:
            # Créer un CP de test
            cp_user, created = User.objects.get_or_create(
                username='test_cp',
                defaults={'email': 'cp@example.com', 'first_name': 'Chef', 'last_name': 'Promo'}
            )
            
            cp_profile, created = UserProfile.objects.get_or_create(
                user=cp_user,
                defaults={'groupe': 'CP'}
            )
            
            # Créer un cours de test
            course, created = Course.objects.get_or_create(
                nom="Cours de Test",
                defaults={'filiere': 'Informatique', 'university': 'Test University'}
            )
            
            # Test: Résumé créé manuellement par CP (doit être auto-validé)
            manual_summary = Summary.objects.create(
                titre="Résumé Manuel Test",
                texte_resume="Contenu du résumé créé manuellement par le CP.",
                course=course,
                author_type='cp',
                author_user=cp_user
            )
            
            self.log_test("Auto-validation résumé CP", manual_summary.is_validated, 
                         "Résumé CP automatiquement validé")
            
            # Test: Résumé généré par IA (non validé par défaut)
            ai_summary = Summary.objects.create(
                titre="Résumé IA Test",
                texte_resume="Contenu du résumé généré par l'IA.",
                course=course,
                author_type='ai'
            )
            
            self.log_test("Résumé IA non validé", not ai_summary.is_validated, 
                         "Résumé IA nécessite validation")
            
            # Test des badges
            cp_badge = manual_summary.author_badge
            ai_badge = ai_summary.author_badge
            
            self.log_test("Badge CP", cp_badge['label'] == 'CP', f"Badge: {cp_badge['label']}")
            self.log_test("Badge IA", ai_badge['label'] == 'IA', f"Badge: {ai_badge['label']}")
            
        except Exception as e:
            self.log_test("Validation Résumés", False, f"Erreur: {str(e)}")
    
    def test_exercise_generation(self):
        """Test de la génération d'exercices"""
        print("\n=== TEST GÉNÉRATION EXERCICES ===")
        
        try:
            # Créer un résumé validé pour les exercices
            course, created = Course.objects.get_or_create(
                nom="Cours Exercices Test",
                defaults={'filiere': 'Test', 'university': 'Test Uni'}
            )
            
            summary = Summary.objects.create(
                titre="Résumé pour Exercices",
                texte_resume="Ce résumé contient des informations importantes sur les concepts de base. Il couvre plusieurs sujets essentiels pour la compréhension.",
                course=course,
                author_type='cp',
                is_validated=True
            )
            
            # Générer des exercices
            exercise = generate_exercises_for_summary(summary.id)
            
            if exercise:
                questions_count = exercise.questions.count()
                self.log_test("Génération exercices", exercise.status == 'completed', 
                             f"Exercice créé avec {questions_count} questions")
                
                # Vérifier qu'il y a des questions
                self.log_test("Questions générées", questions_count > 0, 
                             f"{questions_count} questions créées")
                
                # Vérifier la structure d'une question
                if questions_count > 0:
                    first_question = exercise.questions.first()
                    has_all_options = all([
                        first_question.option_a,
                        first_question.option_b,
                        first_question.option_c,
                        first_question.option_d,
                        first_question.correct_answer in ['A', 'B', 'C', 'D']
                    ])
                    self.log_test("Structure question", has_all_options, 
                                 "Question avec 4 options et réponse correcte")
            else:
                self.log_test("Génération exercices", False, "Échec de génération")
                
        except Exception as e:
            self.log_test("Génération Exercices", False, f"Erreur: {str(e)}")
    
    def test_user_permissions(self):
        """Test des permissions utilisateur"""
        print("\n=== TEST PERMISSIONS UTILISATEUR ===")
        
        try:
            # Créer différents types d'utilisateurs
            etudiant, created = User.objects.get_or_create(
                username='test_etudiant',
                defaults={'email': 'etudiant@example.com'}
            )
            etudiant_profile, created = UserProfile.objects.get_or_create(
                user=etudiant,
                defaults={'groupe': 'ETUDIANT'}
            )
            
            cp, created = User.objects.get_or_create(
                username='test_cp2',
                defaults={'email': 'cp2@example.com'}
            )
            cp_profile, created = UserProfile.objects.get_or_create(
                user=cp,
                defaults={'groupe': 'CP'}
            )
            
            admin, created = User.objects.get_or_create(
                username='test_admin',
                defaults={'email': 'admin@example.com'}
            )
            admin_profile, created = UserProfile.objects.get_or_create(
                user=admin,
                defaults={'groupe': 'ADMIN'}
            )
            
            # Test permissions
            self.log_test("Étudiant - pas de création résumé", 
                         not etudiant_profile.can_create_summary(), 
                         "Étudiant ne peut pas créer de résumés")
            
            self.log_test("CP - peut créer résumé", 
                         cp_profile.can_create_summary(), 
                         "CP peut créer des résumés")
            
            self.log_test("Admin - peut créer résumé", 
                         admin_profile.can_create_summary(), 
                         "Admin peut créer des résumés")
            
            self.log_test("CP - accès gratuit", 
                         cp_profile.has_free_access(), 
                         "CP a accès gratuit")
            
            self.log_test("Étudiant - pas d'accès gratuit", 
                         not etudiant_profile.has_free_access(), 
                         "Étudiant n'a pas d'accès gratuit")
            
        except Exception as e:
            self.log_test("Permissions Utilisateur", False, f"Erreur: {str(e)}")
    
    def run_all_tests(self):
        """Exécute tous les tests"""
        print("=" * 60)
        print("DÉBUT DES TESTS - NOUVELLES FONCTIONNALITÉS RÉSUMÉ+")
        print("=" * 60)
        
        self.test_otp_system()
        self.test_exercise_service()
        self.test_summary_validation()
        self.test_exercise_generation()
        self.test_user_permissions()
        
        # Résumé des résultats
        print("\n" + "=" * 60)
        print("RÉSUMÉ DES TESTS")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total: {total_tests} tests")
        print(f"Réussis: {passed_tests} tests")
        print(f"Échoués: {failed_tests} tests")
        print(f"Taux de réussite: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n[ÉCHECS DÉTAILLÉS]")
            for result in self.test_results:
                if not result['success']:
                    print(f"- {result['name']}: {result['message']}")
        
        print("\n" + "=" * 60)
        if failed_tests == 0:
            print("[SUCCESS] Tous les tests sont passés avec succès!")
        else:
            print(f"[WARNING] {failed_tests} test(s) ont échoué")
        print("=" * 60)

if __name__ == "__main__":
    test_suite = FeatureTestSuite()
    test_suite.run_all_tests()
