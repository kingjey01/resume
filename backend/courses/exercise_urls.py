"""
URLs pour les exercices QCM
"""
from django.urls import path
from . import exercise_views
from . import personalized_exercise_views

urlpatterns = [
    # Exercices standards (existants)
    path('summaries/<int:summary_id>/generate-exercise/', exercise_views.generate_exercise_view, name='generate-exercise'),
    path('exercises/<int:exercise_id>/', exercise_views.get_exercise_view, name='get-exercise'),
    path('exercises/<int:exercise_id>/submit/', exercise_views.submit_exercise_view, name='submit-exercise'),
    path('exercises/attempts/', exercise_views.get_exercise_attempts_view, name='exercise-attempts'),
    path('exercises/attempts/<int:attempt_id>/result/', exercise_views.get_attempt_result_view, name='attempt-result'),
    path('exercises/subscription/check/', exercise_views.check_exercise_subscription_view, name='check-exercise-subscription'),

    # ═══════════════════════════════════════════════════════════════════════════════
    #  EXERCICES PERSONNALISÉS (NOUVEAU - QCM uniques par utilisateur)
    # ═══════════════════════════════════════════════════════════════════════════════

    # Génération avec sélection de difficulté
    path('summaries/<int:summary_id>/personalized-exercise/generate/', personalized_exercise_views.generate_personalized_exercise_view, name='generate-personalized-exercise'),

    # Vérifier si exercice existe déjà
    path('summaries/<int:summary_id>/personalized-exercise/check/', personalized_exercise_views.check_personalized_exercise_exists, name='check-personalized-exercise'),

    # Récupérer exercice avec questions
    path('personalized-exercises/<int:exercise_id>/', personalized_exercise_views.get_personalized_exercise_view, name='get-personalized-exercise'),

    # Soumettre réponses
    path('personalized-exercises/<int:exercise_id>/submit/', personalized_exercise_views.submit_personalized_exercise_view, name='submit-personalized-exercise'),

    # Historique des tentatives
    path('personalized-exercises/attempts/', personalized_exercise_views.get_personalized_attempts_view, name='personalized-exercise-attempts'),
    path('personalized-exercises/attempts/<int:attempt_id>/', personalized_exercise_views.get_personalized_attempt_detail_view, name='personalized-attempt-detail'),
]
