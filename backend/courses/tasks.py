"""
Tâches Celery pour le traitement audio asynchrone.
Après sauvegarde d'une session, Celery lance automatiquement :
  1. Transcription audio (Deepgram) — Tâche 1
  2. Génération de résumé intelligent (DeepSeek) — Tâche 2

Architecture en 2 tâches séparées :
- Si la transcription réussit mais le résumé échoue → on peut relancer juste le résumé
- Chaque tâche a son propre retry et timeout
"""
import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


def _validate_and_fix_duration(session):
    """
    Valide la durée de la session. Si audio_duration=0, re-lit via mutagen.
    Retourne (duration_seconds, duration_source, error_message_or_None)
    """
    import os
    
    MAX_AUDIO_DURATION_SECONDS = 10800
    raw_duration = session.audio_duration or 0
    duration_seconds = float(raw_duration)
    duration_source = 'db'
    
    # Si la durée stockée est 0 ou absente, re-lire depuis le fichier audio
    if duration_seconds <= 0 and session.audio_file:
        logger.warning(
            f"⚠️ [Celery] Session {session.id} - audio_duration=0 en base, "
            f"tentative de re-lecture via mutagen..."
        )
        try:
            file_path = session.audio_file.path if hasattr(session.audio_file, 'path') else None
            if file_path and os.path.exists(file_path):
                from mutagen import File as MutagenFile
                audio_info = MutagenFile(file_path)
                if audio_info and audio_info.info:
                    duration_seconds = float(audio_info.info.length)
                    duration_source = 'mutagen_celery'
                    session.audio_duration = duration_seconds
                    session.save(update_fields=['audio_duration'])
                    logger.info(
                        f"✅ [Celery] Durée re-lue via mutagen: {duration_seconds:.2f}s "
                        f"({duration_seconds/60:.2f}min)"
                    )
        except Exception as e:
            logger.warning(f"⚠️ [Celery] Impossible de re-lire la durée: {e}")
    
    duration_minutes = duration_seconds / 60.0
    logger.info(
        f"🎵 [Celery] Session {session.id} - durée: {duration_seconds:.2f}s "
        f"({duration_minutes:.2f}min) [source: {duration_source}] | "
        f"limite: {MAX_AUDIO_DURATION_SECONDS}s ({MAX_AUDIO_DURATION_SECONDS // 60}min)"
    )

    if duration_seconds > MAX_AUDIO_DURATION_SECONDS:
        error_msg = (
            f'Durée audio trop longue: {int(duration_seconds//3600)}h{int((duration_seconds%3600)//60):02d}m '
            f'({duration_minutes:.1f} minutes / {duration_seconds:.0f}s). '
            f'Maximum autorisé: 3 heures (180 minutes). [source: {duration_source}]'
        )
        return duration_seconds, duration_source, error_msg
    
    return duration_seconds, duration_source, None


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def transcribe_audio_task(self, session_id):
    """
    Tâche Celery 1/2 : Transcription audio via Deepgram.
    
    Si réussie, lance automatiquement la tâche de génération de résumé.
    Si échouée, met la session en 'failed' sans perdre le fichier audio.
    """
    from .models import Session
    from .audio_processing import audio_processor

    logger.info(f"🎤 [Celery T1] Début transcription session {session_id}")

    try:
        session = Session.objects.get(id=session_id)
    except Session.DoesNotExist:
        logger.error(f"❌ [Celery T1] Session {session_id} introuvable")
        return {'success': False, 'error': 'Session introuvable'}

    # Valider la durée
    duration_seconds, duration_source, error_msg = _validate_and_fix_duration(session)
    if error_msg:
        session.processing_status = 'failed'
        session.error_message = error_msg
        session.save()
        logger.warning(f"⚠️ [Celery T1] Session {session_id} rejetée: {error_msg}")
        return {'success': False, 'error': error_msg}

    # Passer en statut "processing"
    session.processing_status = 'processing'
    session.error_message = None
    session.save()

    # Étape 1 : Transcription
    try:
        transcription = audio_processor._step1_transcribe_audio(session)
        
        if not transcription:
            raise Exception('Échec de la transcription audio (résultat vide)')
        
        # Statut intermédiaire : transcrit avec succès
        session.processing_status = 'transcribed'
        session.error_message = None
        session.save()
        
        logger.info(
            f"✅ [Celery T1] Transcription réussie session {session_id} — "
            f"Transcription #{transcription.id} ({len(transcription.texte_transcription)} chars)"
        )
        
        return {
            'success': True,
            'session_id': session_id,
            'transcription_id': transcription.id,
        }
        
    except Exception as exc:
        logger.error(f"❌ [Celery T1] Erreur transcription session {session_id}: {exc}")
        session.refresh_from_db()
        session.processing_status = 'failed'
        session.error_message = f'Erreur transcription: {str(exc)}'
        session.save()
        # Retry automatique si tentatives restantes
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def generate_summary_task(self, session_id, author_user_id=None):
    """
    Tâche Celery 2/2 : Génération du résumé via DeepSeek.
    
    Utilise la transcription existante pour générer le résumé intelligent.
    Peut être relancée indépendamment si la transcription a réussi.
    """
    from .models import Session, Transcription
    from .audio_processing import audio_processor
    from django.contrib.auth.models import User

    logger.info(f"📝 [Celery T2] Début génération résumé session {session_id}")

    try:
        session = Session.objects.get(id=session_id)
    except Session.DoesNotExist:
        logger.error(f"❌ [Celery T2] Session {session_id} introuvable")
        return {'success': False, 'error': 'Session introuvable'}

    # Vérifier qu'une transcription existe
    transcription = Transcription.objects.filter(
        session=session,
        status='completed'
    ).first()
    
    if not transcription:
        error_msg = 'Aucune transcription disponible pour générer le résumé'
        session.processing_status = 'failed'
        session.error_message = error_msg
        session.save()
        logger.error(f"❌ [Celery T2] {error_msg} (session {session_id})")
        return {'success': False, 'error': error_msg}

    # Mettre à jour le statut
    session.processing_status = 'processing'
    session.error_message = None
    session.save()

    # Résoudre l'auteur
    author_user = None
    if author_user_id:
        try:
            author_user = User.objects.get(id=author_user_id)
        except User.DoesNotExist:
            logger.warning(f"⚠️ [Celery T2] Utilisateur {author_user_id} introuvable")

    # Étape 2 : Génération du résumé
    try:
        summary_result = audio_processor._step2_generate_summary(
            transcription=transcription,
            session=session,
            summary_title=session.summary_title or None,
            summary_price=session.summary_price or 0.0,
            author_user=author_user
        )
        
        summary = summary_result.get('summary') if isinstance(summary_result, dict) else summary_result
        
        if not summary:
            raise Exception('Échec de la génération du résumé (résultat vide)')
        
        # Succès total
        session.processing_status = 'summarized'
        session.processed_at = timezone.now()
        session.error_message = None
        session.save()
        
        logger.info(
            f"✅ [Celery T2] Résumé généré session {session_id} — "
            f"Summary #{summary.id}"
        )

        # La notification de l'auteur et des CP est gérée automatiquement par le signal post_save du modèle Summary.
        return {
            'success': True,
            'session_id': session_id,
            'summary_id': summary.id,
            'transcription_id': transcription.id,
        }
        
    except Exception as exc:
        logger.error(f"❌ [Celery T2] Erreur résumé session {session_id}: {exc}")
        session.refresh_from_db()
        # On garde 'transcribed' si la transcription existe déjà
        if transcription:
            session.processing_status = 'transcribed'
            session.error_message = f'Transcription OK, erreur résumé: {str(exc)}'
        else:
            session.processing_status = 'failed'
            session.error_message = f'Erreur résumé: {str(exc)}'
        session.save()
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def process_audio_session_task(self, session_id, author_user_id=None):
    """
    Tâche Celery orchestratrice : lance transcription puis résumé en séquence.
    
    Appelée automatiquement après upload_audio_session via .delay().
    Découpe le traitement en 2 étapes indépendantes pour robustesse.
    """
    from .models import Session, Transcription
    from django.contrib.auth.models import User

    logger.info(f"🚀 [Celery] Début traitement complet session {session_id}")

    try:
        session = Session.objects.get(id=session_id)
    except Session.DoesNotExist:
        logger.error(f"❌ [Celery] Session {session_id} introuvable")
        return {'success': False, 'error': 'Session introuvable'}

    # Valider la durée
    duration_seconds, duration_source, error_msg = _validate_and_fix_duration(session)
    if error_msg:
        session.processing_status = 'failed'
        session.error_message = error_msg
        session.save()
        logger.warning(f"⚠️ [Celery] Session {session_id} rejetée: {error_msg}")
        return {'success': False, 'error': error_msg}

    # Passer en statut "processing"
    session.processing_status = 'processing'
    session.submitted_at = timezone.now()
    session.error_message = None
    session.save()

    # Résoudre l'auteur
    author_user = None
    if author_user_id:
        try:
            author_user = User.objects.get(id=author_user_id)
        except User.DoesNotExist:
            logger.warning(f"⚠️ [Celery] Utilisateur {author_user_id} introuvable, résumé sans auteur")

    # ========================================
    # ÉTAPE 1 : TRANSCRIPTION (Deepgram)
    # ========================================
    from .audio_processing import audio_processor
    
    try:
        logger.info(f"🎤 [Celery] Étape 1/2 : Transcription session {session_id}...")
        transcription = audio_processor._step1_transcribe_audio(session)
        
        if not transcription:
            raise Exception('Échec de la transcription audio (résultat vide)')
        
        # Statut intermédiaire
        session.processing_status = 'transcribed'
        session.error_message = None
        session.save()
        logger.info(f"✅ [Celery] Étape 1/2 terminée: Transcription #{transcription.id}")
        
    except Exception as exc:
        logger.error(f"❌ [Celery] Erreur étape 1 (transcription) session {session_id}: {exc}")
        session.refresh_from_db()
        session.processing_status = 'failed'
        session.error_message = f'Erreur transcription: {str(exc)}'
        session.save()
        raise self.retry(exc=exc)

    # ========================================
    # ÉTAPE 2 : GÉNÉRATION DU RÉSUMÉ (DeepSeek)
    # ========================================
    try:
        logger.info(f"📝 [Celery] Étape 2/2 : Résumé session {session_id}...")
        summary_result = audio_processor._step2_generate_summary(
            transcription=transcription,
            session=session,
            summary_title=session.summary_title or None,
            summary_price=session.summary_price or 0.0,
            author_user=author_user
        )
        
        summary = summary_result.get('summary') if isinstance(summary_result, dict) else summary_result
        
        if not summary:
            raise Exception('Échec de la génération du résumé (résultat vide)')
        
        # Succès total
        session.processing_status = 'summarized'
        session.processed_at = timezone.now()
        session.error_message = None
        session.save()
        
        logger.info(
            f"✅ [Celery] Session {session_id} terminée — "
            f"Transcription #{transcription.id}, Résumé #{summary.id}"
        )

        # La notification de l'auteur et des CP est gérée automatiquement par le signal post_save du modèle Summary.
        return {
            'success': True,
            'session_id': session_id,
            'summary_id': summary.id,
            'transcription_id': transcription.id,
        }
        
    except Exception as exc:
        logger.error(f"❌ [Celery] Erreur étape 2 (résumé) session {session_id}: {exc}")
        session.refresh_from_db()
        # La transcription a réussi, on garde ce statut intermédiaire
        session.processing_status = 'transcribed'
        session.error_message = f'Transcription OK, erreur résumé: {str(exc)}. Vous pouvez réessayer.'
        session.save()
        raise self.retry(exc=exc)
