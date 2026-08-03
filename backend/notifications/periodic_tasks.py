"""
Periodic Celery tasks for checking subscription expiration.
Should be scheduled with Celery Beat.
"""
import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


@shared_task
def check_subscriptions_expiring_soon():
    """
    Check for subscriptions expiring in 7 days and send notifications.
    Should be scheduled to run daily.
    """
    try:
        from payments.models import Abonnement
        from notifications.tasks import notify_subscription_expiring_soon
        
        now = timezone.now()
        expiry_threshold = now + timedelta(days=7)
        
        # Find subscriptions that are active and will expire in 7 days
        expiring_soon = Abonnement.objects.filter(
            status='active',
            date_fin__lte=expiry_threshold,
            date_fin__gt=now,
        ).select_related('user', 'service')
        
        count = 0
        for abonnement in expiring_soon:
            days_left = (abonnement.date_fin - now).days
            logger.info(f'⏰ [Periodic] Abonnement expire bientôt: {abonnement.user.username} — {days_left} jours')
            notify_subscription_expiring_soon.apply_async(
                args=[abonnement.id],
                countdown=2
            )
            count += 1
        
        logger.info(f'⏰ [Periodic] {count} notifications d\'expiration planifiées')
        return {'checked': count}
        
    except Exception as e:
        logger.error(f'❌ [Periodic] Erreur vérification abonnements: {e}')
        return {'error': str(e)}


@shared_task
def check_subscriptions_expired():
    """
    Check for subscriptions that have expired and update their status.
    Should be scheduled to run daily.
    """
    try:
        from payments.models import Abonnement
        from notifications.tasks import notify_subscription_expired
        
        now = timezone.now()
        
        # Find subscriptions that are still marked as active but have expired
        expired = Abonnement.objects.filter(
            status='active',
            date_fin__lte=now,
        ).select_related('user', 'service')
        
        count = 0
        for abonnement in expired:
            logger.info(f'❌ [Periodic] Abonnement expiré: {abonnement.user.username}')
            abonnement.status = 'expired'
            abonnement.save(update_fields=['status'])
            notify_subscription_expired.apply_async(
                args=[abonnement.id],
                countdown=2
            )
            count += 1
        
        logger.info(f'❌ [Periodic] {count} abonnements marqués comme expirés')
        return {'expired': count}
        
    except Exception as e:
        logger.error(f'❌ [Periodic] Erreur vérification expiration: {e}')
        return {'error': str(e)}
