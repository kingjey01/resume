from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Summary, Session
import logging

logger = logging.getLogger(__name__)

# Log AU CHARGEMENT : permet de confirmer dans les logs production (gunicorn /
# celery) que les signaux de courses sont bien enregistrés. Si ce message
# n'apparaît PAS au démarrage du worker, les signaux ne sont pas connectés
# (apps.ready() non appelé / worker non redémarré).
logger.info("🔌 [Signaux] Signaux courses enregistrés (on_session_summarized / on_summary_created)")


@receiver(pre_save, sender=Session)
def _track_session_processing_status(sender, instance, **kwargs):
    """
    TACHE2 : mémorise l'ancien statut de traitement avant chaque sauvegarde.
    Permet au signal post_save de détecter la transition RÉELLE vers
    « Résumé disponible » (processing_status == 'summarized').
    """
    if instance.pk:
        try:
            instance._previous_processing_status = Session.objects.get(pk=instance.pk).processing_status
        except Session.DoesNotExist:
            instance._previous_processing_status = None
    else:
        instance._previous_processing_status = None


@receiver(post_save, sender=Session)
def on_session_summarized(sender, instance, **kwargs):
    """
    TACHE2 : déclenchement SYSTÉMATIQUE des notifications quand le statut réel
    de la session passe à « Résumé disponible ».

    Ce signal est lié au CHANGEMENT RÉEL DE STATUT (processing_status →
    'summarized'), pas à la création du résumé : il fonctionne donc même si le
    résumé existait déjà (retry Celery, re-génération) — contrairement au
    signal post_save de Summary qui ne se déclenche qu'à l'insertion.

    Chaîne : statut → « Résumé disponible » → tâche notify_summary_available
    déclenchée → notification créée → envoi FCM (logs à chaque étape).
    """
    old_status = getattr(instance, '_previous_processing_status', None)
    new_status = instance.processing_status

    # Seule la transition RÉELLE vers 'summarized' déclenche (pas les re-saves)
    if new_status != 'summarized' or old_status == 'summarized':
        return

    logger.info(
        f"📌 [Signal] Session {instance.id} : statut → « Résumé disponible » "
        f"(processing_status: {old_status} → {new_status})"
    )

    # Résumé généré par IA pour cette session (couvre aussi le cas retry où le
    # résumé existait déjà avant le passage au statut)
    summary = instance.summaries.filter(author_type='ai').order_by('-id').first()
    if summary is None:
        logger.warning(
            f"⚠️ [Signal] Session {instance.id} en statut « Résumé disponible » "
            f"mais aucun résumé AI trouvé — notification ignorée"
        )
        return

    # Anti-doublon : la notification « en attente de validation » est créée à la
    # CRÉATION du résumé (on_summary_created). Ce signal ne fait que servir de
    # filet de sécurité si cette notification n'existe pas (ex. échec de la
    # tâche au moment de la création) — sinon pas de seconde notification.
    from notifications.models import AppNotification
    if AppNotification.objects.filter(
        notification_type='summary_created',
        summary_id=summary.id,
    ).exists():
        logger.info(
            f"✅ [Signal] Résumé {summary.id} déjà notifié à sa création — pas de doublon"
        )
        return

    author = summary.author_user
    if not author:
        logger.warning(
            f"⚠️ [Signal] Résumé {summary.id} (session {instance.id}) sans auteur — "
            f"fallback : notification adressée aux CP du cours"
        )

    try:
        from notifications.tasks import notify_summary_available
        logger.info(
            f"🚀 [Signal] Tâche de notification déclenchée — "
            f"notify_summary_available summary_id={summary.id}, "
            f"auteur={getattr(author, 'username', 'inconnu')} (id={author.id if author else 'None'})"
        )
        # author_user_id peut être None : la tâche notifie alors les CP du cours
        # (le résumé devient disponible → il faut TOUJOURS prévenir quelqu'un).
        notify_summary_available.apply_async(
            kwargs={'summary_id': summary.id, 'author_user_id': author.id if author else None},
            countdown=1,
        )
    except Exception as err:
        logger.error(f"❌ [Signal] Erreur planification notify_summary_available : {err}")


@receiver(post_save, sender=Summary)
def on_summary_created(sender, instance, created, **kwargs):
    """
    Signal déclenché à la CRÉATION d'un résumé (manuel 'cp' ou IA 'ai').

    Résumé MANUEL (cp) : auto-validé à la sauvegarde → confirmation CP +
    diffusion « résumé disponible » aux étudiants de la promotion.

    Résumé IA (ai) : dès sa création, on notifie le CP « en attente de
    validation » (le résumé existe et doit être validé). Le signal de statut
    de session (on_session_summarized) sert de filet de sécurité avec une
    garde anti-doublon.
    """
    if not created:
        return

    if instance.author_type not in ('cp', 'ai'):
        return

    author = instance.author_user

    try:
        from notifications.tasks import notify_summary_available

        if instance.author_type == 'ai':
            # Résumé IA créé → informer immédiatement le CP (fallback CP du cours
            # si le résumé est sans auteur). La garde anti-doublon dans
            # on_session_summarized évite une seconde notification au changement
            # de statut.
            logger.info(
                f"🔔 [Signal] Résumé IA créé — ID={instance.id}, "
                f"auteur={getattr(author, 'username', 'None')}"
            )
            notify_summary_available.apply_async(
                kwargs={
                    'summary_id': instance.id,
                    'author_user_id': author.id if author else None,
                },
                countdown=1,
            )
            return

        # ── Résumé manuel (cp) : flux inchangé ────────────────────────────
        from notifications.tasks import notify_summary_created, create_and_send_notification
        logger.info(
            f"🔔 [Signal] Résumé manuel créé — ID={instance.id}, "
            f"auteur={getattr(author, 'username', 'None')}"
        )

        # 1. Confirmation au CP créateur (le résumé est déjà auto-validé, pas « en attente »)
        if author:
            logger.info(f"🔔 [Signal] Confirmation planifiée pour l'auteur {author.username}")
            notify_summary_created.apply_async(
                kwargs={'summary_id': instance.id, 'author_user_id': author.id},
                countdown=1
            )
        else:
            logger.warning(
                f"⚠️ [Signal] Résumé {instance.id} sans auteur — confirmation CP ignorée"
            )

        # 2. Résumé manuel auto-validé → notifier immédiatement les étudiants de la
        #    promotion « résumé disponible » (même flux que validate_summary_view)
        course = instance.course
        create_and_send_notification.apply_async(kwargs={
            'title': '📚 Nouveau résumé disponible',
            'body': f'Le résumé « {instance.titre} » du cours {course.nom} est maintenant disponible.',
            'notification_type': 'summary_validated',
            'universite_id': course.universites.values_list('id', flat=True).first(),
            'filiere_id': course.filieres.values_list('id', flat=True).first(),
            'promotion_id': course.promotions.values_list('id', flat=True).first(),
            'summary_id': instance.id,
            'course_id': course.id,
        }, countdown=2)
        logger.info(
            f"🔔 [Signal] Diffusion étudiants planifiée pour le résumé manuel — summary_id={instance.id}"
        )
    except Exception as err:
        logger.warning(f"⚠️ [Signal] Erreur planification notifications : {err}")
