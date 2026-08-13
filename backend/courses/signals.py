from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Summary, Session
import logging

logger = logging.getLogger(__name__)


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

    author = summary.author_user
    if not author:
        logger.warning(
            f"⚠️ [Signal] Résumé {summary.id} (session {instance.id}) sans auteur — "
            f"notification CP ignorée"
        )
        return

    try:
        from notifications.tasks import notify_summary_available
        logger.info(
            f"🚀 [Signal] Tâche de notification déclenchée — "
            f"notify_summary_available summary_id={summary.id}, "
            f"auteur={author.username} (id={author.id})"
        )
        notify_summary_available.apply_async(
            kwargs={'summary_id': summary.id, 'author_user_id': author.id},
            countdown=1,
        )
    except Exception as err:
        logger.error(f"❌ [Signal] Erreur planification notify_summary_available : {err}")


@receiver(post_save, sender=Summary)
def on_summary_created(sender, instance, created, **kwargs):
    """
    Signal déclenché à la création d'un résumé MANUEL (author_type='cp'),
    qui n'a pas de session à statut (donc pas de transition « Résumé disponible »).

    TACHE2 : les résumés générés depuis un audio (author_type='ai') sont
    désormais notifiés par le signal de statut de session (on_session_summarized),
    lié au vrai passage à « Résumé disponible » — ce signal ne les gère plus,
    pour éviter le double déclenchement.
    """
    if not created:
        return

    if instance.author_type != 'cp':
        return

    author = instance.author_user
    logger.info(
        f"🔔 [Signal] Résumé manuel créé — ID={instance.id}, "
        f"auteur={getattr(author, 'username', 'None')}"
    )

    if author:
        try:
            from notifications.tasks import notify_summary_created, notify_summary_to_validate
            logger.info(f"🔔 [Signal] Notification push planifiée pour l'auteur {author.username}")
            notify_summary_created.apply_async(
                kwargs={'summary_id': instance.id, 'author_user_id': author.id},
                countdown=1
            )
            # Notifier l'auteur CP que son résumé est en attente de validation
            logger.info(f"🔔 [Signal] Notification validation planifiée pour l'auteur CP — summary_id={instance.id}")
            notify_summary_to_validate.apply_async(
                kwargs={'summary_id': instance.id, 'author_user_id': author.id},
                countdown=2
            )
        except Exception as err:
            logger.warning(f"⚠️ [Signal] Erreur planification notifications : {err}")
    else:
        logger.warning(
            f"⚠️ [Signal] Résumé {instance.id} sans auteur — notification push ignorée"
        )
