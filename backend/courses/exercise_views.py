"""
Vues pour la gestion des exercices QCM
"""
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from .models import Summary, Exercise, ExerciseQuestion, ExerciseAttempt
from payments.models import Service, Abonnement
from .exercise_generator import generate_exercises_for_summary
from .permissions import HasActiveSubscription
from django.utils import timezone
import logging
import threading

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, HasActiveSubscription])
def generate_exercise_view(request, summary_id):
    """
    Génère un exercice pour un résumé donné
    Accessible uniquement aux utilisateurs abonnés
    """
    try:
        # Lire le niveau de difficulté demandé et force_regenerate
        difficulty = request.data.get('difficulty', 'medium') if request.data else 'medium'
        force_regenerate = request.data.get('force_regenerate', False) if request.data else False
        
        # Vérifier que le résumé existe et est validé
        summary = get_object_or_404(Summary, id=summary_id, is_validated=True)
        
        # Vérifier l'abonnement exercice spécifique
        if not has_exercise_subscription(request.user):
            return Response({
                'error': 'Abonnement requis',
                'subscription_required': True
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Vérifier si CET utilisateur a déjà un exercice pour ce résumé+difficulté
        existing_exercise = Exercise.objects.filter(
            summary=summary,
            created_by=request.user,
            difficulty=difficulty
        ).first()
        
        if existing_exercise and not force_regenerate:
            if existing_exercise.status == 'completed':
                return Response({
                    'message': 'Exercice déjà disponible',
                    'exercise_id': existing_exercise.id,
                    'status': 'completed',
                    'generated_by_ai': existing_exercise.generated_by_ai,
                    'difficulty': difficulty,
                }, status=status.HTTP_200_OK)
            elif existing_exercise.status == 'generating':
                return Response({
                    'message': 'Exercice en cours de génération',
                    'exercise_id': existing_exercise.id,
                    'status': 'generating',
                    'generated_by_ai': existing_exercise.generated_by_ai,
                    'difficulty': difficulty,
                }, status=status.HTTP_202_ACCEPTED)
            elif existing_exercise.status == 'failed':
                # Relancer la génération si elle a échoué
                existing_exercise.status = 'generating'
                existing_exercise.save()
                def rerun_generation():
                    generate_exercises_for_summary(summary_id, existing_exercise=existing_exercise, difficulty=difficulty)
                threading.Thread(target=rerun_generation, daemon=True).start()
                return Response({
                    'message': 'Nouvelle génération lancée',
                    'exercise_id': existing_exercise.id,
                    'status': 'generating',
                    'generated_by_ai': existing_exercise.generated_by_ai,
                    'difficulty': difficulty,
                }, status=status.HTTP_202_ACCEPTED)
        
        # Si force_regenerate, supprimer uniquement l'exercice de CET utilisateur
        if force_regenerate and existing_exercise:
            existing_exercise.delete()
        
        # Créer un exercice propre à cet utilisateur
        exercise = Exercise.objects.create(
            summary=summary,
            created_by=request.user,
            titre=f"Exercices - {summary.titre}",
            description=f"Questions à choix multiples basées sur le résumé: {summary.titre}",
            difficulty=difficulty,
            status='generating'
        )

        # Lancer la génération en background (ne pas bloquer la requête)
        def run_generation():
            generate_exercises_for_summary(summary_id, existing_exercise=exercise, difficulty=difficulty)

        thread = threading.Thread(target=run_generation, daemon=True)
        thread.start()

        return Response({
            'message': 'Génération en cours...',
            'exercise_id': exercise.id,
            'status': 'generating',
            'generated_by_ai': exercise.generated_by_ai,
            'difficulty': difficulty,
        }, status=status.HTTP_201_CREATED)
            
    except Summary.DoesNotExist:
        return Response({
            'error': 'Résumé introuvable ou non validé'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Erreur génération exercice: {str(e)}")
        return Response({
            'error': 'Erreur interne du serveur'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, HasActiveSubscription])
def get_exercise_view(request, exercise_id):
    """
    Récupère un exercice avec ses questions
    """
    try:
        exercise = get_object_or_404(Exercise, id=exercise_id)

        # S'assurer que l'exercice appartient à cet utilisateur (ou est legacy sans propriétaire)
        if exercise.created_by is not None and exercise.created_by != request.user:
            return Response({'error': 'Exercice introuvable'}, status=status.HTTP_404_NOT_FOUND)

        # Si encore en génération, retourner juste le statut (pour le polling Flutter)
        if exercise.status != 'completed':
            return Response({
                'status': exercise.status,
                'exercise_id': exercise.id,
                'generated_by_ai': exercise.generated_by_ai,
                'message': 'Génération en cours...' if exercise.status == 'generating' else 'Génération échouée',
            }, status=status.HTTP_200_OK)

        questions = exercise.questions.all().order_by('order')
        
        # Préparer les données des questions (sans les bonnes réponses)
        questions_data = []
        for question in questions:
            questions_data.append({
                'id': question.id,
                'question_text': question.question_text,
                'options': {
                    'A': question.option_a,
                    'B': question.option_b,
                    'C': question.option_c,
                    'D': question.option_d
                },
                'order': question.order,
                'code_language': question.code_language,
                'code_block': question.code_block,
            })
        
        return Response({
            'status': 'completed',
            'exercise': {
                'id': exercise.id,
                'titre': exercise.titre,
                'description': exercise.description,
                'summary_title': exercise.summary.titre,
                'questions_count': exercise.questions_count,
                'generated_by_ai': exercise.generated_by_ai,
            },
            'questions': questions_data
        }, status=status.HTTP_200_OK)
        
    except Exercise.DoesNotExist:
        return Response({
            'error': 'Exercice introuvable ou non disponible'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Erreur récupération exercice: {str(e)}")
        return Response({
            'error': 'Erreur interne du serveur'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, HasActiveSubscription])
def submit_exercise_view(request, exercise_id):
    """
    Soumet les réponses d'un exercice et calcule le score
    """
    try:
        exercise = get_object_or_404(Exercise, id=exercise_id, status='completed')

        # S'assurer que l'exercice appartient à cet utilisateur
        if exercise.created_by is not None and exercise.created_by != request.user:
            return Response({'error': 'Exercice introuvable'}, status=status.HTTP_404_NOT_FOUND)

        answers = request.data.get('answers', {})
        
        if not answers:
            return Response({
                'error': 'Réponses requises'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Créer la tentative
        attempt = ExerciseAttempt.objects.create(
            exercise=exercise,
            student=request.user,
            answers=answers
        )
        
        # Calculer le score
        score = attempt.calculate_score()
        
        # Préparer les résultats détaillés
        results = []
        questions = exercise.questions.all().order_by('order')
        
        for question in questions:
            user_answer = answers.get(str(question.id))
            is_correct = user_answer == question.correct_answer
            
            results.append({
                'question_id': question.id,
                'question_text': question.question_text,
                'user_answer': user_answer,
                'correct_answer': question.correct_answer,
                'is_correct': is_correct,
                'explanation': question.explanation,
                'code_language': question.code_language,
                'code_block': question.code_block,
            })
        
        return Response({
            'attempt_id': attempt.id,
            'score': score,
            'total_questions': len(questions),
            'correct_answers': sum(1 for r in results if r['is_correct']),
            'results': results
        }, status=status.HTTP_200_OK)
        
    except Exercise.DoesNotExist:
        return Response({
            'error': 'Exercice introuvable'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Erreur soumission exercice: {str(e)}")
        return Response({
            'error': 'Erreur interne du serveur'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_attempt_result_view(request, attempt_id):
    """
    Récupère les détails d'une tentative (questions, réponses, corrections)
    """
    try:
        attempt = get_object_or_404(ExerciseAttempt, id=attempt_id, student=request.user)
        exercise = attempt.exercise
        questions = exercise.questions.all().order_by('order')
        answers = attempt.answers or {}

        results = []
        for question in questions:
            user_answer = answers.get(str(question.id))
            is_correct = user_answer == question.correct_answer
            results.append({
                'question_id': question.id,
                'question_text': question.question_text,
                'options': {
                    'A': question.option_a,
                    'B': question.option_b,
                    'C': question.option_c,
                    'D': question.option_d,
                },
                'user_answer': user_answer,
                'correct_answer': question.correct_answer,
                'is_correct': is_correct,
                'explanation': question.explanation,
                'code_language': question.code_language,
                'code_block': question.code_block,
            })

        correct_count = sum(1 for r in results if r['is_correct'])
        return Response({
            'attempt_id': attempt.id,
            'score': attempt.score,
            'total_questions': len(results),
            'correct_answers': correct_count,
            'exercise_title': exercise.titre,
            'summary_title': exercise.summary.titre,
            'results': results,
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Erreur récupération résultat tentative: {str(e)}")
        return Response({'error': 'Erreur interne du serveur'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_exercise_attempts_view(request):
    """
    Récupère l'historique des tentatives d'exercices de l'utilisateur
    """
    try:
        attempts = ExerciseAttempt.objects.filter(
            student=request.user
        ).select_related('exercise', 'exercise__summary').order_by('-completed_at')
        
        attempts_data = []
        for attempt in attempts:
            attempts_data.append({
                'id': attempt.id,
                'exercise_title': attempt.exercise.titre,
                'summary_title': attempt.exercise.summary.titre,
                'score': attempt.score,
                'completed_at': attempt.completed_at.isoformat(),
                'exercise_id': attempt.exercise.id
            })
        
        return Response({
            'attempts': attempts_data,
            'total_attempts': len(attempts_data)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur récupération tentatives: {str(e)}")
        return Response({
            'error': 'Erreur interne du serveur'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_exercise_subscription_view(request):
    """
    Vérifie si l'utilisateur a un abonnement actif au service d'exercices.
    Retourne aussi si l'abonnement est expiré.
    """
    try:
        user = request.user
        has_active = has_exercise_subscription(user)
        
        # Vérifier s'il y a un abonnement expiré
        is_expired = False
        if not has_active:
            exercise_service = Service.objects.filter(nom__icontains="qcm", is_active=True).first()
            if exercise_service:
                is_expired = Abonnement.objects.filter(
                    user=user,
                    service=exercise_service,
                    date_fin__lt=timezone.now()
                ).exists()

        subscription_info = None
        if has_active:
            # Récupérer les détails de l'abonnement (payments app)
            # Priorité au service QCM, sinon tout abonnement actif
            exercise_service = Service.objects.filter(
                nom__icontains="qcm", is_active=True
            ).first()

            active_subscription = None
            if exercise_service:
                active_subscription = Abonnement.objects.filter(
                    user=user,
                    service=exercise_service,
                    status='active',
                    date_debut__lte=timezone.now(),
                    date_fin__gte=timezone.now()
                ).first()

            if active_subscription is None:
                active_subscription = Abonnement.objects.filter(
                    user=user,
                    status='active',
                    date_debut__lte=timezone.now(),
                    date_fin__gte=timezone.now()
                ).first()

            if active_subscription:
                subscription_info = {
                    'service': active_subscription.service.nom,
                    'date_debut': active_subscription.date_debut.isoformat(),
                    'date_fin': active_subscription.date_fin.isoformat(),
                    'montant': float(active_subscription.service.price),
                    'devise': active_subscription.service.currency
                }
        
        return Response({
            'has_subscription': has_active,
            'is_expired': is_expired,
            'subscription_info': subscription_info
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur vérification abonnement: {str(e)}")
        return Response({
            'error': 'Erreur interne du serveur'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def has_exercise_subscription(user):
    """
    Vérifie si l'utilisateur a un abonnement actif au service d'exercices.

    Logique robuste :
    1. Cherche d'abord le service QCM/Exercices par nom (compatibilité).
    2. Si aucun service QCM n'existe OU si l'abonnement n'est pas lié à ce
       service précis, vérifie TOUT abonnement actif de l'utilisateur.
    """
    try:
        now = timezone.now()

        # 1) Essayer le service QCM/Exercices nommé (compatibilité)
        exercise_service = Service.objects.filter(
            nom__icontains="qcm", is_active=True
        ).first()

        if exercise_service:
            has_qcm_sub = Abonnement.objects.filter(
                user=user,
                service=exercise_service,
                status='active',
                date_debut__lte=now,
                date_fin__gte=now
            ).exists()
            if has_qcm_sub:
                return True

        # 2) Fallback : TOUT abonnement actif donne accès aux exercices
        #    (l'app ne vend qu'un seul type d'abonnement : exercices)
        return Abonnement.objects.filter(
            user=user,
            status='active',
            date_debut__lte=now,
            date_fin__gte=now
        ).exists()

    except Exception as e:
        logger.error(f"Erreur vérification abonnement: {str(e)}")
        return False
