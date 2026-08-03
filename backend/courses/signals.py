from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Summary
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Summary)
def on_summary_created(sender, instance, created, **kwargs):
    """
    Signal déclenché à la création d'un résumé.
    Notifie UNIQUEMENT le CP auteur que son résumé est prêt et en attente de validation.
    Ce push FCM déclenche le rafraîchissement du badge "Validation" dans son application.
    """
    if not created:
        return

    author = instance.author_user
    logger.info(
        f"🔔 [Signal] Nouveau résumé créé — ID={instance.id}, "
        f"auteur={getattr(author, 'username', 'None')}, is_validated={instance.is_validated}"
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
