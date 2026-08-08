"""
Celery tasks pour l'envoi des emails de statut des demandes CP.
Exécutées en arrière-plan pour ne pas bloquer l'action de l'administrateur.
"""
import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_cp_status_email(self, cp_request_id, approved):
    """
    Envoie un email d'approbation ou de refus au candidat CP.

    - Destinataire : l'email saisi dans la demande, sinon l'email du compte.
    - Relance automatique en cas d'échec SMTP (jusqu'à 3 tentatives, espacées de 30 s).
    """
    from .models import CPRequest

    try:
        cp_request = CPRequest.objects.select_related('user').get(id=cp_request_id)
    except CPRequest.DoesNotExist:
        logger.warning(f"Demande CP {cp_request_id} introuvable — email non envoyé")
        return {'sent': False, 'reason': 'cp_request_not_found'}

    recipient = (cp_request.email or '').strip() or cp_request.user.email
    if not recipient:
        logger.warning(f"Demande CP {cp_request_id}: aucun email pour notifier {cp_request.user.username}")
        return {'sent': False, 'reason': 'no_recipient'}

    user_display = cp_request.user.get_full_name() or cp_request.user.username

    if approved:
        subject = '🎉 Votre demande CP a été approuvée'
        message = f"""Bonjour {user_display},

Félicitations ! Votre demande pour devenir Chef de Promotion (CP) a été approuvée.

Vous pouvez maintenant vous connecter à l'application et :
- créer des cours
- enregistrer des séances audio
- publier des résumés pour les étudiants

À très bientôt sur Résumé+ !
L'équipe Résumé+
"""
    else:
        subject = 'Votre demande CP a été refusée'
        message = f"""Bonjour {user_display},

Nous vous informons que votre demande pour devenir Chef de Promotion (CP) a été refusée.
"""
        if cp_request.admin_comment:
            message += f"""
Commentaire de l'administrateur : {cp_request.admin_comment}
"""
        message += """
Vous pouvez soumettre une nouvelle demande à tout moment depuis l'application.

Cordialement,
L'équipe Résumé+
"""

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )
        logger.info(f"Email {'approbation' if approved else 'refus'} CP envoyé à {recipient}")
        return {'sent': True, 'recipient': recipient}
    except Exception as e:
        logger.warning(
            f"Échec envoi email {'approbation' if approved else 'refus'} CP à {recipient} "
            f"(tentative {self.request.retries + 1}): {e}"
        )
        raise self.retry(exc=e)


def _admin_notification_recipients():
    """Destinataires admin depuis settings.ADMIN_NOTIFICATION_EMAIL (séparés par des virgules)."""
    raw = getattr(settings, 'ADMIN_NOTIFICATION_EMAIL', '') or ''
    return [addr.strip() for addr in raw.split(',') if addr.strip()]


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def notify_admin_new_cp_request(self, cp_request_id):
    """
    Notifie l'administration par email (uniquement — pas de push) qu'une
    nouvelle demande CP est en attente.

    Destinataires : settings.ADMIN_NOTIFICATION_EMAIL (dynamique depuis .env).
    """
    from .models import CPRequest

    recipients = _admin_notification_recipients()
    if not recipients:
        logger.warning(f"Demande CP {cp_request_id}: ADMIN_NOTIFICATION_EMAIL non configuré — email admin non envoyé")
        return {'sent': False, 'reason': 'admin_email_not_configured'}

    try:
        cp_request = CPRequest.objects.select_related('user').get(id=cp_request_id)
    except CPRequest.DoesNotExist:
        logger.warning(f"Demande CP {cp_request_id} introuvable — email admin non envoyé")
        return {'sent': False, 'reason': 'cp_request_not_found'}

    user_display = cp_request.user.get_full_name() or cp_request.user.username
    candidate_email = (cp_request.email or '').strip() or cp_request.user.email
    motivation = (cp_request.motivation or '').strip() or 'Non renseignée'

    subject = '📬 Nouvelle demande CP en attente'
    message = f"""Bonjour,

Une nouvelle demande pour devenir Chef de Promotion (CP) est en attente de traitement.

Candidat : {user_display}
Email : {candidate_email or 'Non renseigné'}
Motivation : {motivation}

Connectez-vous à l'administration (https://votre-domaine/admin/users/cprequest/) pour approuver ou refuser cette demande.

Cordialement,
L'équipe Résumé+
"""

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            fail_silently=False,
        )
        logger.info(f"Email admin nouvelle demande CP envoyé à {', '.join(recipients)}")
        return {'sent': True, 'recipients': recipients}
    except Exception as e:
        logger.warning(
            f"Échec envoi email admin nouvelle demande CP "
            f"(tentative {self.request.retries + 1}): {e}"
        )
        raise self.retry(exc=e)
