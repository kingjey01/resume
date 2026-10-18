"""
Vues API pour les exercices QCM personnalisés.
Endpoints pour génération, soumission et historique.
"""
import random
import threading
import logging
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import Summary, UserPersonalizedExercise, UserPersonalizedAttempt
from .personalized_exercise_generator import generate_personalized_exercise
from .permissions import HasActiveSubscription, user_can_access_summary
from .qcm_quota import (
    consommer_quota,
    get_active_subscription,
    periode_courante,
    quota_snapshot,
    rembourser_quota,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
#  GÉNÉRATION D'EXERCICE PERSONNALISÉ
# ═══════════════════════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, HasActiveSubscription])
def generate_personalized_exercise_view(request, summary_id):
    """
    Génère un exercice QCM personnalisé pour l'utilisateur.
    Si déjà existant, retourne l'existant. Si régénération demandée, crée nouveau.

    Body:
    {
        "difficulty": "easy|medium|hard" (défaut: medium),
        "regenerate": false (true pour forcer nouvelle génération)
    }

    Retourne le statut de génération avec progress polling possible.
    """
    try:
        # Paramètres
        difficulty = request.data.get('difficulty', 'medium')
        regenerate = request.data.get('regenerate', False)

        if difficulty not in ['easy', 'medium', 'hard']:
            return Response(
                {'error': 'Difficulté invalide. Choisissez: easy, medium, hard'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Vérifier résumé
        summary = get_object_or_404(Summary, id=summary_id, is_validated=True)
        user = request.user

        # Un QCM ne peut être lancé que sur un résumé acheté (ou gratuit/CP)
        if not user_can_access_summary(user, summary):
            return Response({
                'error': "Vous devez d'abord acheter ce résumé",
                'purchase_required': True,
                'code': 'purchase_required',
            }, status=status.HTTP_403_FORBIDDEN)

        # Vérifier abonnement exercices
        abonnement = get_active_subscription(user)
        if abonnement is None:
            return Response({
                'error': 'Abonnement exercices requis',
                'subscription_required': True,
                'code': 'subscription_required',
                'quota': quota_snapshot(None),
            }, status=status.HTTP_403_FORBIDDEN)

        # Chercher l'exercice existant POUR CE NIVEAU uniquement.
        # Depuis la restructuration (1 exercice par user, résumé ET niveau),
        # les questions Faciles, Moyennes et Difficiles sont isolées dans des
        # exercices distincts — comme dans l'ancien système standard.
        existing = UserPersonalizedExercise.objects.filter(
            user=user, summary=summary, difficulty=difficulty
        ).first()

        if existing and not regenerate:
            # Retourner l'existant selon son statut
            if existing.status == 'completed':
                return Response({
                    'status': 'completed',
                    'exercise_id': existing.id,
                    'difficulty': existing.difficulty,
                    'questions_count': existing.questions_count,
                    'regenerated_count': existing.regenerated_count,
                    'created_at': existing.created_at.isoformat(),
                    'message': 'Exercice personnalisé disponible',
                    'quota': quota_snapshot(abonnement),
                }, status=status.HTTP_200_OK)

            elif existing.status == 'generating':
                # Réponse idempotente : une nouvelle tentative réseau sur une
                # génération déjà lancée NE consomme PAS une seconde unité.
                return Response({
                    'status': 'generating',
                    'exercise_id': existing.id,
                    'difficulty': existing.difficulty,
                    'message': 'Génération en cours...',
                    'quota': quota_snapshot(abonnement),
                }, status=status.HTTP_202_ACCEPTED)

        # ── UNITÉ DE QUOTA = PACK ─────────────────────────────────────────────
        # Les 3 niveaux d'un même résumé, sur la même période d'abonnement, ne
        # consomment qu'UNE unité (24 questions), conformément au calcul retenu
        # (Basic : 15 packs = 360 questions).
        periode = periode_courante(abonnement)

        with transaction.atomic():
            # Verrouille le résumé : deux requêtes simultanées (deux niveaux)
            # ne peuvent pas payer deux fois le même pack.
            Summary.objects.select_for_update().get(pk=summary_id)
            pack_deja_paye = UserPersonalizedExercise.objects.filter(
                user=user,
                summary=summary,
                quota_periode_debut=periode,
            ).exists()

            if pack_deja_paye:
                # Pack déjà réglé pour cette période : ce niveau est inclus.
                quota = quota_snapshot(abonnement)
                quota_consomme_le = None
                quota_abonnement_id = None
            else:
                quota_ok, quota, abonnement_id = consommer_quota(user)
                if not quota_ok:
                    code = quota.get('raison_blocage') or 'quota_exhausted'
                    return Response({
                        'error': quota.get('message_blocage')
                                 or 'Quota de générations QCM épuisé.',
                        'code': code,
                        'quota_exhausted': code == 'quota_exhausted',
                        'quota': quota,
                    }, status=status.HTTP_403_FORBIDDEN)
                quota_consomme_le = timezone.now()
                quota_abonnement_id = abonnement_id

            if existing and regenerate:
                # Régénération demandée : relancer UNIQUEMENT l'exercice de ce niveau
                existing.status = 'generating'
                existing.seed = random.randint(1, 1000000)  # Nouveau seed pour variation
                existing.regenerated_count += 1
                existing.save()
                exercise = existing
                logger.info(
                    f"🔄 Régénération exercice perso #{exercise.id} pour user={user.id} "
                    f"(difficulty={difficulty}, regenerate=True)"
                )
            elif existing and existing.status in ('failed', 'pending'):
                # Relancer la génération (jamais créer un doublon du même niveau)
                existing.status = 'generating'
                existing.seed = random.randint(1, 1000000)
                existing.save()
                exercise = existing
                logger.info(
                    f"♻️ Relance exercice perso #{exercise.id} après échec "
                    f"(difficulty={difficulty}) pour user={user.id}"
                )
            else:
                # Nouvel exercice pour ce niveau (les autres niveaux restent intacts)
                seed = random.randint(1, 1000000)
                try:
                    # Savepoint : permet de rattraper une création concurrente
                    # sans casser la transaction extérieure.
                    with transaction.atomic():
                        exercise = UserPersonalizedExercise.objects.create(
                            user=user,
                            summary=summary,
                            difficulty=difficulty,
                            seed=seed,
                            status='generating'
                        )
                except IntegrityError:
                    # Requête concurrente : l'exercice de ce niveau vient d'être
                    # créé par un autre appel. On rend l'unité réservée.
                    if quota_abonnement_id:
                        rembourser_quota(quota_abonnement_id, quota_consomme_le)
                    quota_abonnement_id = None  # déjà remboursé
                    concurrent = UserPersonalizedExercise.objects.filter(
                        user=user, summary=summary, difficulty=difficulty
                    ).first()
                    if concurrent is None:
                        raise
                    return Response({
                        'status': concurrent.status,
                        'exercise_id': concurrent.id,
                        'difficulty': concurrent.difficulty,
                        'message': 'Génération déjà lancée',
                        'quota': quota_snapshot(get_active_subscription(user)),
                    }, status=(
                        status.HTTP_200_OK
                        if concurrent.status == 'completed'
                        else status.HTTP_202_ACCEPTED
                    ))
                logger.info(f"🆕 Nouvel exercice perso créé #{exercise.id} (difficulty={difficulty}) pour user={user.id}")

            # Marque CET exercice comme payeur du pack pour la période.
            if quota_abonnement_id:
                exercise.quota_periode_debut = periode
                exercise.save(update_fields=['quota_periode_debut'])

        # Lancer génération en background (hors transaction)
        _launch_generation(
            exercise, user.id, summary_id, difficulty, exercise.seed,
            quota_abonnement_id=quota_abonnement_id,
            quota_consomme_le=quota_consomme_le,
            quota_periode_debut=periode if quota_abonnement_id else None,
        )

        return Response({
            'status': 'generating',
            'exercise_id': exercise.id,
            'difficulty': difficulty,
            'regenerated_count': exercise.regenerated_count,
            'seed': exercise.seed,
            'message': 'Génération lancée en arrière-plan',
            'quota': quota,
        }, status=status.HTTP_202_ACCEPTED)

    except Summary.DoesNotExist:
        return Response(
            {'error': 'Résumé introuvable ou non validé'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        # Une erreur dans le bloc atomique annule aussi la réservation
        # (transaction) ; après le commit, `_launch_generation` gère seul le
        # remboursement en cas d'échec du thread.
        logger.error(f"❌ Erreur génération exercice perso: {e}")
        return Response(
            {'error': 'Erreur interne du serveur'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _launch_generation(exercise, user_id, summary_id, difficulty, seed,
                       quota_abonnement_id=None, quota_consomme_le=None,
                       quota_periode_debut=None):
    """Lance la génération en thread background.

    `quota_abonnement_id` / `quota_consomme_le` identifient la réservation
    faite dans la vue. Si la génération n'aboutit pas à un exercice complet,
    l'unité est rendue et le pack est libéré pour cette période : le quota ne
    doit pas être débité pour un échec.
    """
    def rembourser():
        if not quota_abonnement_id:
            return
        rembourser_quota(quota_abonnement_id, quota_consomme_le)
        if quota_periode_debut:
            UserPersonalizedExercise.objects.filter(
                pk=exercise.pk,
                quota_periode_debut=quota_periode_debut,
            ).update(quota_periode_debut=None)
        logger.info(
            f"↩️ Quota remboursé (génération sans résultat) "
            f"abonnement={quota_abonnement_id}"
        )

    def run_gen():
        try:
            resultat = generate_personalized_exercise(
                user_id=user_id,
                summary_id=summary_id,
                difficulty=difficulty,
                seed=seed,
                existing_exercise=exercise
            )
            exercice_genere = resultat[0] if resultat else None
            if exercice_genere is None or exercice_genere.status != 'completed':
                rembourser()
        except Exception as e:
            logger.error(f"❌ Erreur thread génération: {e}")
            exercise.status = 'failed'
            exercise.save()
            rembourser()

    try:
        thread = threading.Thread(target=run_gen, daemon=True)
        thread.start()
    except Exception:
        # Le thread n'a pas démarré : la réservation est annulée.
        rembourser()
        raise


# ═══════════════════════════════════════════════════════════════════════════════
#  RÉCUPÉRATION D'EXERCICE
# ═══════════════════════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, HasActiveSubscription])
def get_personalized_exercise_view(request, exercise_id):
    """
    Récupère un exercice personnalisé avec ses questions.
    Si en cours de génération, retourne juste le statut (polling).
    """
    try:
        exercise = get_object_or_404(
            UserPersonalizedExercise,
            id=exercise_id,
            user=request.user
        )

        # L'accès au QCM est conditionné à l'achat du résumé concerné
        if not user_can_access_summary(request.user, exercise.summary):
            return Response({
                'error': "Vous devez d'abord acheter ce résumé",
                'purchase_required': True,
                'code': 'purchase_required',
            }, status=status.HTTP_403_FORBIDDEN)

        # Mettre à jour la date d'accès
        exercise.mark_accessed()

        if exercise.status == 'generating':
            return Response({
                'status': 'generating',
                'exercise_id': exercise.id,
                'difficulty': exercise.difficulty,
                'message': 'Génération en cours... Rafraîchissez dans quelques secondes.'
            }, status=status.HTTP_200_OK)

        if exercise.status == 'failed':
            return Response({
                'status': 'failed',
                'exercise_id': exercise.id,
                'message': 'La génération a échoué. Vous pouvez réessayer.',
                'can_retry': True
            }, status=status.HTTP_200_OK)

        if exercise.status == 'completed':
            # Préparer les questions (sans réponses correctes) depuis les lignes
            questions_data = []
            for idx, q in enumerate(exercise.questions.all().order_by('order')):
                questions_data.append({
                    'index': idx,
                    'question_text': q.question_text,
                    'options': q.options,
                    'code_language': q.code_language,
                    'code_block': q.code_block,
                })

            return Response({
                'status': 'completed',
                'exercise': {
                    'id': exercise.id,
                    'summary_id': exercise.summary_id,
                    'summary_title': exercise.summary.titre,
                    'difficulty': exercise.difficulty,
                    'difficulty_label': _get_difficulty_label(exercise.difficulty),
                    'questions_count': len(questions_data),
                    'generated_by_ai': exercise.generated_by_ai,
                    'regenerated_count': exercise.regenerated_count,
                    'created_at': exercise.created_at.isoformat(),
                },
                'questions': questions_data
            }, status=status.HTTP_200_OK)

        return Response({
            'status': exercise.status,
            'exercise_id': exercise.id
        }, status=status.HTTP_200_OK)

    except UserPersonalizedExercise.DoesNotExist:
        return Response(
            {'error': 'Exercice introuvable'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"❌ Erreur récupération exercice perso: {e}")
        return Response(
            {'error': 'Erreur interne du serveur'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _get_difficulty_label(difficulty):
    """Retourne le libellé de la difficulté."""
    labels = {'easy': 'Facile', 'medium': 'Moyen', 'hard': 'Difficile'}
    return labels.get(difficulty, 'Moyen')


# ═══════════════════════════════════════════════════════════════════════════════
#  SOUMISSION DES RÉPONSES
# ═══════════════════════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, HasActiveSubscription])
def submit_personalized_exercise_view(request, exercise_id):
    """
    Soumet les réponses et calcule le score.

    Body:
    {
        "answers": {"0": "A", "1": "B", "2": "C", ...},  // index_question: réponse
        "time_spent_seconds": 143                        // OPTIONNEL (secondes)
    }

    `time_spent_seconds` est la durée réellement passée sur l'exercice, mesurée
    par le chronomètre de l'app. Elle doit venir du client : côté serveur la
    tentative est créée AU MOMENT de la soumission (`started_at` est en
    `auto_now_add`), donc aucune durée calculable n'existe. Sans ce champ, le
    temps enregistré reste 0 (comportement historique).

    Retourne le score détaillé avec corrections.
    """
    try:
        exercise = get_object_or_404(
            UserPersonalizedExercise,
            id=exercise_id,
            user=request.user,
            status='completed'
        )

        # L'accès au QCM est conditionné à l'achat du résumé concerné
        if not user_can_access_summary(request.user, exercise.summary):
            return Response({
                'error': "Vous devez d'abord acheter ce résumé",
                'purchase_required': True,
                'code': 'purchase_required',
            }, status=status.HTTP_403_FORBIDDEN)

        answers = request.data.get('answers', {})

        if not answers:
            return Response(
                {'error': 'Réponses requises (format: {"0": "A", "1": "B", ...})'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Durée réelle mesurée par le chronomètre de l'app. Champ OPTIONNEL :
        # absent, on garde le comportement historique (temps laissé à 0).
        raw_time_spent = request.data.get('time_spent_seconds')
        time_spent_seconds = None
        if raw_time_spent is not None:
            try:
                # Accepte un entier, un flottant JSON ou une chaîne numérique.
                time_spent_seconds = max(0, int(float(raw_time_spent)))
            except (TypeError, ValueError):
                return Response(
                    {'error': 'time_spent_seconds doit être un nombre de secondes'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Créer la tentative
        attempt = UserPersonalizedAttempt.objects.create(
            personalized_exercise=exercise,
            user=request.user,
            answers=answers
        )

        # Calculer le score — les résultats sont reconstruits depuis les lignes
        # de questions (la tentative ne stocke plus les questions)
        attempt.calculate_results(time_spent_seconds=time_spent_seconds)

        # Formater la réponse
        results_formatted = []
        for r in attempt.build_results():
            results_formatted.append({
                'question_index': r['question_index'],
                'question_text': r['question_text'],
                'user_answer': r['user_answer'],
                'correct_answer': r['correct_answer'],
                'is_correct': r['is_correct'],
                'explanation': r['explanation'],
                'options': r.get('options', {}),
                'code_language': r.get('code_language'),
                'code_block': r.get('code_block'),
            })

        return Response({
            'attempt_id': attempt.id,
            'score': attempt.score,
            'correct_answers': attempt.correct_answers_count,
            'total_questions': exercise.questions_count,
            'time_spent_seconds': attempt.time_spent_seconds,
            'results': results_formatted,
            'message': _get_score_message(attempt.score)
        }, status=status.HTTP_200_OK)

    except UserPersonalizedExercise.DoesNotExist:
        return Response(
            {'error': 'Exercice introuvable ou non complété'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"❌ Erreur soumission exercice perso: {e}")
        return Response(
            {'error': 'Erreur interne du serveur'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _get_score_message(score):
    """Message personnalisé selon le score."""
    if score >= 80:
        return "Excellent ! Maîtrise très bonne du sujet."
    elif score >= 60:
        return "Bien ! Continue à réviser pour t'améliorer."
    elif score >= 40:
        return "Passable. Tu devrais réétudier ce résumé."
    else:
        return "Continue tes efforts ! Révise ce résumé attentivement."


# ═══════════════════════════════════════════════════════════════════════════════
#  HISTORIQUE DES TENTATIVES
# ═══════════════════════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_personalized_attempts_view(request):
    """
    Récupère l'historique des tentatives de l'utilisateur.
    Query params: summary_id (optionnel pour filtrer par résumé)
    """
    try:
        summary_id = request.query_params.get('summary_id')

        attempts = UserPersonalizedAttempt.objects.filter(
            user=request.user
        ).select_related(
            'personalized_exercise',
            'personalized_exercise__summary'
        ).order_by('-started_at')

        if summary_id:
            attempts = attempts.filter(
                personalized_exercise__summary_id=summary_id
            )

        attempts_data = []
        for attempt in attempts:
            attempts_data.append({
                'id': attempt.id,
                'exercise_id': attempt.personalized_exercise_id,
                'summary_id': attempt.personalized_exercise.summary_id,
                'summary_title': attempt.personalized_exercise.summary.titre,
                'difficulty': attempt.personalized_exercise.difficulty,
                'difficulty_label': _get_difficulty_label(attempt.personalized_exercise.difficulty),
                'score': attempt.score,
                'correct_answers': attempt.correct_answers_count,
                'total_questions': attempt.personalized_exercise.questions_count,
                'time_spent_seconds': attempt.time_spent_seconds,
                'started_at': attempt.started_at.isoformat(),
                'completed_at': attempt.completed_at.isoformat() if attempt.completed_at else None,
            })

        return Response({
            'attempts': attempts_data,
            'total': len(attempts_data)
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"❌ Erreur récupération tentatives: {e}")
        return Response(
            {'error': 'Erreur interne du serveur'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_personalized_attempt_detail_view(request, attempt_id):
    """
    Récupère le détail complet d'une tentative avec toutes les corrections.
    """
    try:
        attempt = get_object_or_404(
            UserPersonalizedAttempt,
            id=attempt_id,
            user=request.user
        )

        exercise = attempt.personalized_exercise

        return Response({
            'attempt_id': attempt.id,
            'exercise': {
                'id': exercise.id,
                'summary_id': exercise.summary_id,
                'summary_title': exercise.summary.titre,
                'difficulty': exercise.difficulty,
                'difficulty_label': _get_difficulty_label(exercise.difficulty),
            },
            'score': attempt.score,
            'correct_answers': attempt.correct_answers_count,
            'total_questions': exercise.questions_count,
            'time_spent_seconds': attempt.time_spent_seconds,
            'started_at': attempt.started_at.isoformat(),
            'completed_at': attempt.completed_at.isoformat() if attempt.completed_at else None,
            'results': attempt.build_results()
        }, status=status.HTTP_200_OK)

    except UserPersonalizedAttempt.DoesNotExist:
        return Response(
            {'error': 'Tentative introuvable'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"❌ Erreur récupération détail tentative: {e}")
        return Response(
            {'error': 'Erreur interne du serveur'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ═══════════════════════════════════════════════════════════════════════════════
#  VÉRIFICATION EXERCICE EXISTANT POUR UN RÉSUMÉ
# ═══════════════════════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, HasActiveSubscription])
def check_personalized_exercise_exists(request, summary_id):
    """
    Vérifie si l'utilisateur a déjà un exercice personnalisé pour ce résumé.
    Utile avant d'afficher le bouton "Générer" ou "Continuer".

    Query param optionnel: difficulty (easy|medium|hard)
    — si fourni, ne vérifie que ce niveau ; sinon, retourne l'exercice le
      plus récemment consulté (pour "Continuer" sur le dernier niveau utilisé).
    """
    try:
        summary = get_object_or_404(Summary, id=summary_id, is_validated=True)

        # Un QCM ne peut être consulté que sur un résumé acheté (ou gratuit/CP)
        if not user_can_access_summary(request.user, summary):
            return Response({
                'error': "Vous devez d'abord acheter ce résumé",
                'purchase_required': True,
                'code': 'purchase_required',
            }, status=status.HTTP_403_FORBIDDEN)

        difficulty = request.query_params.get('difficulty')
        exercises = UserPersonalizedExercise.objects.filter(
            user=request.user,
            summary=summary
        )
        if difficulty:
            exercises = exercises.filter(difficulty=difficulty)

        # Dernier exercice consulté (ou le plus récent si jamais consulté)
        exercise = exercises.order_by('-last_accessed_at', '-created_at').first()
        quota = quota_snapshot(get_active_subscription(request.user))

        if exercise:
            return Response({
                'exists': True,
                'exercise_id': exercise.id,
                'status': exercise.status,
                'difficulty': exercise.difficulty,
                'difficulty_label': _get_difficulty_label(exercise.difficulty),
                'questions_count': exercise.questions_count if exercise.status == 'completed' else 0,
                'regenerated_count': exercise.regenerated_count,
                'created_at': exercise.created_at.isoformat(),
                'can_regenerate': exercise.status == 'completed',
                'attempts_count': exercise.attempts.count(),
                'quota': quota,
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'exists': False,
                'message': 'Aucun exercice personnalisé pour ce résumé',
                'quota': quota,
            }, status=status.HTTP_200_OK)

    except Summary.DoesNotExist:
        return Response(
            {'error': 'Résumé introuvable'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"❌ Erreur vérification exercice: {e}")
        return Response(
            {'error': 'Erreur interne du serveur'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ═══════════════════════════════════════════════════════════════════════════════
#  UTILITAIRES
# ═══════════════════════════════════════════════════════════════════════════════

def has_exercise_subscription(user):
    """Vérifie si l'utilisateur a un abonnement exercices actif.

    Logique robuste (identique à exercise_views) :
    1. Cherche d'abord un service QCM/Exercices nommé.
    2. Sinon, TOUT abonnement actif donne accès.
    """
    try:
        from payments.models import Service, Abonnement

        now = timezone.now()

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

        # Fallback : tout abonnement actif
        return Abonnement.objects.filter(
            user=user,
            status='active',
            date_debut__lte=now,
            date_fin__gte=now
        ).exists()

    except Exception as e:
        logger.error(f"❌ Erreur vérification abonnement: {e}")
        return False
