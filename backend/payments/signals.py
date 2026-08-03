"""
Signals for payment-related events (subscriptions, purchases).
Triggers notifications when subscriptions are paid, expiring, or purchases are completed.
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from .models import Abonnement, Purchase

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Abonnement)
def on_abonnement_created_or_updated(sender, instance, created, **kwargs):
    """
    Signal handler for Abonnement creation/update.
    - When created with status='active' → notify subscription paid
    - Check if expiring soon (7 days) → notify expiring soon
    - Check if expired → notify expired
    """
    try:
        from notifications.tasks import (
            notify_subscription_paid,
            notify_subscription_expiring_soon,
            notify_subscription_expired,
        )
        
        # Only process if subscription is being created or status changed
        if not created and instance.status != 'active':
            return
        
        now = timezone.now()
        days_until_expiry = (instance.date_fin - now).days
        
        # Case 1: Subscription just became active (payment completed)
        if created and instance.status == 'active':
            logger.info(f'🎉 [Signal] Abonnement créé pour {instance.user.username}')
            notify_subscription_paid.apply_async(
                args=[instance.id],
                countdown=2
            )
        
        # Case 2: Subscription is expiring soon (7 days or less)
        elif instance.status == 'active' and 0 < days_until_expiry <= 7:
            logger.info(f'⏰ [Signal] Abonnement expire bientôt pour {instance.user.username} ({days_until_expiry} jours)')
            notify_subscription_expiring_soon.apply_async(
                args=[instance.id],
                countdown=2
            )
        
        # Case 3: Subscription has expired
        elif instance.status == 'expired' or (instance.status == 'active' and instance.date_fin <= now):
            logger.info(f'❌ [Signal] Abonnement expiré pour {instance.user.username}')
            instance.status = 'expired'
            instance.save(update_fields=['status'])
            notify_subscription_expired.apply_async(
                args=[instance.id],
                countdown=2
            )
    
    except Exception as e:
        logger.error(f'❌ [Signal] Erreur traitement abonnement: {e}')


@receiver(post_save, sender=Purchase)
def on_purchase_completed(sender, instance, created, **kwargs):
    """
    Signal handler for Purchase completion.
    When purchase status changes to 'completed' → notify user.
    """
    try:
        from notifications.tasks import notify_summary_purchased
        
        # Only notify when purchase is completed
        if instance.status == 'completed' and instance.summary:
            logger.info(f'📥 [Signal] Achat complété pour {instance.user.username} — {instance.summary.titre}')
            notify_summary_purchased.apply_async(
                args=[instance.id],
                countdown=2
            )
    
    except Exception as e:
        logger.error(f'❌ [Signal] Erreur traitement achat: {e}')
