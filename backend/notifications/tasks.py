"""
Celery tasks for sending push notifications via FCM.
Falls back gracefully if firebase-admin is not configured.
"""
import logging
from celery import shared_task
from django.conf import settings

logger = logging.getLogger(__name__)


def _get_fcm_app():
    """Initialize and return the Firebase app, or None if not configured."""
    try:
        import firebase_admin
        from firebase_admin import credentials

        if not firebase_admin._apps:
            cred_path = getattr(settings, 'FIREBASE_CREDENTIALS_PATH', None)
            if not cred_path:
                logger.warning('⚠️ [FCM] FIREBASE_CREDENTIALS_PATH non configuré — push désactivé')
                return None
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)

        return firebase_admin.get_app()
    except ImportError:
        logger.warning('⚠️ [FCM] firebase-admin non installé — push désactivé')
        return None
    except Exception as e:
        logger.error(f'❌ [FCM] Erreur initialisation Firebase: {e}')
        return None


def _is_invalid_token_error(exception):
    """Returns True if the FCM error means the token is invalid/expired and must be deleted."""
    if exception is None:
        return False
    try:
        from firebase_admin import messaging
        if isinstance(exception, messaging.UnregisteredError):
            return True
        # InvalidArgumentError covers INVALID_ARGUMENT from FCM
        if isinstance(exception, messaging.InvalidArgumentError):
            return True
    except ImportError:
        pass
    # Fallback: check error code string
    code = getattr(exception, 'code', '') or ''
    return 'registration-token-not-registered' in str(code) or 'invalid-argument' in str(code)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_fcm_notification(self, user_notification_ids: list):
    """
    Send FCM push notifications for a list of UserNotification IDs using
    send_each_for_multicast (batch up to 500 tokens per call).
    Invalid/expired tokens are immediately deleted from the DB.
    """
    try:
        from .models import UserDevice, UserNotification

        if not user_notification_ids:
            return {'sent': 0, 'failed': 0}

        app = _get_fcm_app()
        if app is None:
            logger.info(f'ℹ️ [FCM] Firebase non configuré — {len(user_notification_ids)} notifs non envoyées par push')
            return {'sent': 0, 'failed': 0, 'reason': 'firebase_not_configured'}

        from firebase_admin import messaging
        from django.db.models import Count

        un_qs = UserNotification.objects.filter(
            id__in=user_notification_ids
        ).select_related('user', 'notification')

        # Pré-calculer le nombre de notifications non lues par utilisateur
        # (une seule requête pour tout le batch — utilisé pour le badge d'icône)
        user_ids = [un.user_id for un in un_qs]
        unread_by_user = dict(
            UserNotification.objects.filter(user_id__in=user_ids, is_read=False)
            .values('user_id')
            .annotate(count=Count('id'))
            .values_list('user_id', 'count')
        )

        sent = 0
        failed = 0
        invalid_tokens = []

        for un in un_qs:
            notif = un.notification
            tokens = list(
                UserDevice.objects.filter(user=un.user, is_active=True)
                .values_list('fcm_token', flat=True)
            )

            if not tokens:
                continue

            # Vrai compteur de non lues pour le badge d'icône
            unread_count = unread_by_user.get(un.user_id, 0)

            message_data = {
                'user_notification_id': str(un.id),
                'notification_type': notif.notification_type,
                'summary_id': str(notif.summary_id or ''),
                'course_id': str(notif.course_id or ''),
                'badge_count': str(unread_count),  # Badge d'icône (Android/iOS)
            }

            # Send in batches of 500 (FCM multicast limit)
            for i in range(0, len(tokens), 500):
                batch_tokens = tokens[i:i + 500]

                multicast_msg = messaging.MulticastMessage(
                    tokens=batch_tokens,
                    notification=messaging.Notification(
                        title=notif.title,
                        body=notif.body,
                        image=notif.image_url or None,
                    ),
                    data=message_data,
                    android=messaging.AndroidConfig(
                        priority='high',
                        notification=messaging.AndroidNotification(
                            sound='default',
                            click_action='FLUTTER_NOTIFICATION_CLICK',
                            channel_id='resume_plus_notifications',
                            # App branding: small icon + brand color
                            icon='@mipmap/ic_launcher',
                            color='#1E3A5F',
                        ),
                    ),
                    apns=messaging.APNSConfig(
                        payload=messaging.APNSPayload(
                            aps=messaging.Aps(sound='default', badge=unread_count),
                        ),
                    ),
                )

                batch_response = messaging.send_each_for_multicast(multicast_msg)

                for idx, response in enumerate(batch_response.responses):
                    token = batch_tokens[idx]
                    if response.success:
                        sent += 1
                    else:
                        failed += 1
                        if _is_invalid_token_error(response.exception):
                            # Token invalide ou expiré → supprimer immédiatement
                            invalid_tokens.append(token)
                            logger.warning(f'🗑️ [FCM] Token invalide marqué pour suppression: …{token[-10:]}')
                        else:
                            logger.error(f'❌ [FCM] Échec token …{token[-10:]}: {response.exception}')

        # Supprimer tous les tokens invalides en une seule requête DB
        if invalid_tokens:
            deleted_count, _ = UserDevice.objects.filter(fcm_token__in=invalid_tokens).delete()
            logger.warning(f'🗑️ [FCM] {deleted_count} tokens invalides supprimés de la DB')

        logger.info(f'📊 [FCM] Batch terminé — envoyés: {sent}, échoués: {failed}')
        return {'sent': sent, 'failed': failed}

    except Exception as exc:
        logger.error(f'❌ [FCM] Erreur tâche: {exc}')
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=10)
def create_and_send_notification(
    self,
    title: str,
    body: str,
    notification_type: str = 'general',
    universite_id: int = None,
    filiere_id: int = None,
    promotion_id: int = None,
    summary_id: int = None,
    course_id: int = None,
    sender_id: int = None,
    image_url: str = None,
):
    """
    Creates AppNotification + UserNotification records for all targeted users,
    then schedules FCM sends in batches.
    """
    try:
        from django.contrib.auth.models import User
        from .models import AppNotification, UserNotification
        from users.models import UserProfile

        # Create the notification
        notif_kwargs = {
            'title': title,
            'body': body,
            'notification_type': notification_type,
            'summary_id': summary_id,
            'course_id': course_id,
        }
        if image_url:
            notif_kwargs['image_url'] = image_url
        if universite_id:
            from courses.models import Universite
            notif_kwargs['target_universite'] = Universite.objects.get(id=universite_id)
        if filiere_id:
            from courses.models import Filiere
            notif_kwargs['target_filiere'] = Filiere.objects.get(id=filiere_id)
        if promotion_id:
            from courses.models import Promotion
            notif_kwargs['target_promotion'] = Promotion.objects.get(id=promotion_id)
        if sender_id:
            notif_kwargs['sender'] = User.objects.get(id=sender_id)

        notification = AppNotification.objects.create(**notif_kwargs)
        logger.info(f'🔔 [Task] Notification créée: id={notification.id} type={notification_type}')

        # Find target users based on targeting logic
        profile_qs = UserProfile.objects.select_related('user').filter(
            user__is_active=True
        )
        
        # Targeting logic:
        # - If universite_id: filter by universite
        # - If filiere_id: filter by filiere (requires universite_id)
        # - If promotion_id: filter by promotion (requires universite_id + filiere_id)
        if universite_id:
            profile_qs = profile_qs.filter(universite_id=universite_id)
        
        if filiere_id:
            # Filiere filtering requires universite context
            if universite_id:
                profile_qs = profile_qs.filter(filiere_id=filiere_id)
            else:
                logger.warning(f'⚠️ [Task] filiere_id={filiere_id} ignoré (universite_id requis)')
        
        if promotion_id:
            # Promotion filtering requires universite + filiere context
            if universite_id and filiere_id:
                profile_qs = profile_qs.filter(promotion_id=promotion_id)
            else:
                logger.warning(f'⚠️ [Task] promotion_id={promotion_id} ignoré (universite_id + filiere_id requis)')
        
        # NOTE: Sender is INCLUDED in recipients (CP receives their own notification)

        un_ids = []
        for profile in profile_qs:
            un, created = UserNotification.objects.get_or_create(
                user=profile.user,
                notification=notification,
            )
            if created:
                un_ids.append(un.id)

        logger.info(f'👥 [Task] {len(un_ids)} utilisateurs ciblés pour la notification {notification.id}')

        # Send push notifications in batches of 100
        batch_size = 100
        for i in range(0, len(un_ids), batch_size):
            batch = un_ids[i: i + batch_size]
            send_fcm_notification.apply_async(args=[batch], countdown=2)

        return {
            'notification_id': notification.id,
            'targeted_users': len(un_ids),
        }

    except Exception as exc:
        logger.error(f'❌ [Task] create_and_send_notification échoué: {exc}')
        raise self.retry(exc=exc)


# ─────────────────────────────────────────────────────────────────────────────
#  Summary Creation Notification (CP only)
# ─────────────────────────────────────────────────────────────────────────────

@shared_task(bind=True, max_retries=2, default_retry_delay=10)
def notify_summary_created(self, summary_id: int, author_user_id: int):
    """
    Notify the CP (author) that their summary has been successfully generated.
    This notification is sent ONLY to the CP who launched the creation.
    """
    logger.info(f'🔔 [Task] notify_summary_created DÉMARRÉ — summary_id={summary_id}, author_user_id={author_user_id}')
    
    try:
        from django.contrib.auth.models import User
        from .models import AppNotification, UserNotification

        try:
            author = User.objects.get(id=author_user_id)
            logger.info(f'🔔 [Task] Auteur trouvé: {author.username} (id={author.id})')
        except User.DoesNotExist:
            logger.warning(f'⚠️ [Task] notify_summary_created: Utilisateur {author_user_id} introuvable')
            return {'sent': 0, 'reason': 'user_not_found'}

        # Retrieve summary for notification body
        summary_title = None
        try:
            from courses.models import Summary
            summary = Summary.objects.get(id=summary_id)
            summary_title = summary.titre
        except Exception:
            pass

        body = (
            f'Votre résumé « {summary_title} » a été généré avec succès.'
            if summary_title
            else 'Votre résumé a été généré avec succès.'
        )

        notif = AppNotification.objects.create(
            title='✅ Résumé créé',
            body=body,
            notification_type='summary_created',
            summary_id=summary_id,
            sender=author,
        )

        un, _ = UserNotification.objects.get_or_create(
            user=author,
            notification=notif,
        )

        logger.info(
            f'🔔 [Task] Notification "résumé créé" créée — notif_id={notif.id}, user_notif_id={un.id}'
        )

        # Envoyer la notification FCM
        send_fcm_notification.apply_async(args=[[un.id]], countdown=1)
        logger.info(f'🔔 [Task] FCM planifié pour user_notification_id={un.id}')

        return {'notification_id': notif.id, 'user_id': author.id, 'summary_id': summary_id}

    except Exception as exc:
        logger.error(f'❌ [Task] notify_summary_created échoué: {exc}')
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=10)
def notify_summary_available(self, summary_id: int, author_user_id: int):
    """
    TACHE2 : notifie le CP qui a soumis l'audio que son résumé IA est généré
    et EN ATTENTE DE VALIDATION.

    Déclenchée par le signal de statut de session (courses.signals.on_session_summarized) :
    le déclenchement est lié au CHANGEMENT RÉEL de statut vers « Résumé disponible »,
    et non à la création du résumé ou à une action manuelle.

    Le résumé IA n'est pas encore validé : on informe donc le CP qu'il doit le
    valider. Le message « résumé disponible » vers les étudiants n'est envoyé
    qu'à la validation (validate_summary_view → create_and_send_notification).

    Logs de la chaîne complète :
      - statut → « Résumé disponible »          (signal on_session_summarized)
      - tâche de notification déclenchée         (signal on_session_summarized)
      - tâche démarrée                           (cette fonction)
      - notification créée                       (cette fonction)
      - tâche d'envoi déclenchée                 (cette fonction)
      - envoi réussi/échoué (+ raison)           (send_fcm_notification)
    """
    logger.info(
        f'🚀 [Task] notify_summary_available DÉMARRÉ — summary_id={summary_id}, author_user_id={author_user_id}'
    )

    try:
        from django.contrib.auth.models import User
        from courses.models import Summary
        from .models import AppNotification, UserNotification

        # 1. Résumé + auteur
        try:
            summary = Summary.objects.select_related('course').get(id=summary_id)
        except Summary.DoesNotExist:
            logger.warning(f'⚠️ [Task] notify_summary_available: Résumé {summary_id} introuvable')
            return {'sent': 0, 'reason': 'summary_not_found'}

        try:
            author = User.objects.get(id=author_user_id)
        except User.DoesNotExist:
            logger.warning(f'⚠️ [Task] notify_summary_available: auteur {author_user_id} introuvable')
            return {'sent': 0, 'reason': 'author_not_found'}

        logger.info(
            f'🔔 [Task] Résumé « {summary.titre} » (cours: {summary.course.nom}) — '
            f'auteur: {author.username} (id={author.id})'
        )

        # 2. Anti-doublon : si une notification « résumé disponible » existe déjà
        #    pour ce résumé, la réutiliser (retry Celery, re-save du statut…)
        existing = AppNotification.objects.filter(
            notification_type='summary_created',
            summary_id=summary.id,
        ).first()

        if existing:
            un, _ = UserNotification.objects.get_or_create(
                user=author,
                notification=existing,
            )
            logger.info(
                f'🔔 [Task] Notification existante réutilisée: id={existing.id} '
                f'— envoi relancé (user_notification_id={un.id})'
            )
            send_fcm_notification.apply_async(args=[[un.id]], countdown=1)
            logger.info(f'📨 [Task] Tâche d\'envoi FCM planifiée — user_notification_id={un.id}')
            return {
                'notification_id': existing.id,
                'user_id': author.id,
                'summary_id': summary_id,
                'reused': True,
            }

        # 3. Création de la notification pour le CP auteur de l'audio :
        #    le résumé IA est généré mais PAS encore validé → « en attente de validation ».
        #    Le message « résumé disponible » aux étudiants n'arrive qu'à la validation.
        notif = AppNotification.objects.create(
            title='📝 Résumé en attente de validation',
            body=f'Votre résumé « {summary.titre} » (cours: {summary.course.nom}) a été créé et attend votre validation.',
            notification_type='summary_created',
            summary_id=summary.id,
            course_id=summary.course.id,
            sender=author,
        )
        logger.info(
            f'🔔 [Task] Notification créée: id={notif.id} type=summary_created '
            f'(summary_id={summary.id})'
        )

        un, _ = UserNotification.objects.get_or_create(
            user=author,
            notification=notif,
        )
        logger.info(f'🔔 [Task] Destinataire ciblé: {author.username} — user_notification_id={un.id}')

        # 4. Déclencher la tâche d'envoi FCM
        send_fcm_notification.apply_async(args=[[un.id]], countdown=1)
        logger.info(f'📨 [Task] Tâche d\'envoi FCM planifiée — user_notification_id={un.id}')

        return {'notification_id': notif.id, 'user_id': author.id, 'summary_id': summary_id}

    except Exception as exc:
        logger.error(f'❌ [Task] notify_summary_available échoué: {exc}')
        raise self.retry(exc=exc)


# ─────────────────────────────────────────────────────────────────────────────
#  Subscription & Purchase Notifications
# ─────────────────────────────────────────────────────────────────────────────

@shared_task(bind=True, max_retries=2, default_retry_delay=10)
def notify_subscription_paid(self, abonnement_id: int):
    """
    Notify user when their subscription payment is completed.
    IMPORTANT: Notification is sent ONLY to the user who subscribed (individual, not broadcast).
    """
    try:
        from payments.models import Abonnement
        from .models import AppNotification, UserNotification
        
        abonnement = Abonnement.objects.select_related('user', 'service').get(id=abonnement_id)
        user = abonnement.user
        service = abonnement.service
        
        # Create notification for THIS USER ONLY (not broadcast)
        notif = AppNotification.objects.create(
            title='✅ Abonnement activé',
            body=f'Votre abonnement {service.nom} est maintenant actif, renouvelable après 30 jours.',
            notification_type='payment',
            sender=None,
        )
        
        # Create user notification ONLY for the subscriber
        un, _ = UserNotification.objects.get_or_create(
            user=user,
            notification=notif,
        )
        
        logger.info(f'💳 [Task] Notification paiement créée pour {user.username} UNIQUEMENT — abonnement {service.nom}')
        
        # Send FCM to this user only
        send_fcm_notification.apply_async(args=[[un.id]], countdown=1)
        
        return {'notification_id': notif.id, 'user_id': user.id, 'service': service.nom}
        
    except Exception as exc:
        logger.error(f'❌ [Task] notify_subscription_paid échoué: {exc}')
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=10)
def notify_subscription_expiring_soon(self, abonnement_id: int):
    """
    Notify user when their subscription is about to expire (7 days before).
    IMPORTANT: Notification is sent ONLY to the user whose subscription is expiring (individual, not broadcast).
    """
    try:
        from payments.models import Abonnement
        from .models import AppNotification, UserNotification
        from django.utils import timezone

        abonnement = Abonnement.objects.select_related('user', 'service').get(id=abonnement_id)
        user = abonnement.user
        service = abonnement.service
        days_left = (abonnement.date_fin - timezone.now()).days

        # Create notification for THIS USER ONLY (not broadcast)
        notif = AppNotification.objects.create(
            title='⏰ Abonnement expire bientôt',
            body=f'Votre abonnement {service.nom} expire dans {days_left} jours. Renouvelez-le pour continuer à accéder à tous les contenus.',
            notification_type='payment',
            sender=None,
        )
        
        # Create user notification ONLY for this user
        un, _ = UserNotification.objects.get_or_create(
            user=user,
            notification=notif,
        )
        
        logger.info(f'⏰ [Task] Notification expiration créée pour {user.username} UNIQUEMENT — {days_left} jours restants')
        
        # Send FCM to this user only
        send_fcm_notification.apply_async(args=[[un.id]], countdown=1)
        
        return {'notification_id': notif.id, 'user_id': user.id, 'service': service.nom, 'days_left': days_left}
        
    except Exception as exc:
        logger.error(f'❌ [Task] notify_subscription_expiring_soon échoué: {exc}')
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=10)
def notify_subscription_expired(self, abonnement_id: int):
    """
    Notify user when their subscription has expired.
    Includes link to resubscribe.
    IMPORTANT: Notification is sent ONLY to the user whose subscription expired (individual, not broadcast).
    """
    try:
        from payments.models import Abonnement
        from .models import AppNotification, UserNotification

        abonnement = Abonnement.objects.select_related('user', 'service').get(id=abonnement_id)
        user = abonnement.user
        service = abonnement.service

        # Create notification for THIS USER ONLY (not broadcast)
        notif = AppNotification.objects.create(
            title='❌ Abonnement expiré',
            body=f'Votre abonnement {service.nom} a expiré. Cliquez pour vous réabonner et retrouver l\'accès complet.',
            notification_type='payment',
            sender=None,
        )
        
        # Create user notification ONLY for this user
        un, _ = UserNotification.objects.get_or_create(
            user=user,
            notification=notif,
        )
        
        logger.info(f'❌ [Task] Notification expiration créée pour {user.username} UNIQUEMENT')
        
        # Send FCM to this user only
        send_fcm_notification.apply_async(args=[[un.id]], countdown=1)
        
        return {'notification_id': notif.id, 'user_id': user.id, 'service': service.nom}
        
    except Exception as exc:
        logger.error(f'❌ [Task] notify_subscription_expired échoué: {exc}')
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=10)
def notify_summary_purchased(self, purchase_id: int):
    """
    Notify user when they successfully purchase a summary.
    """
    try:
        from payments.models import Purchase
        from .models import AppNotification, UserNotification

        purchase = Purchase.objects.select_related('user', 'summary').get(id=purchase_id)
        user = purchase.user
        summary = purchase.summary

        # Create notification
        notif = AppNotification.objects.create(
            title='📥 Résumé acheté',
            body=f'Vous avez acheté le résumé « {summary.titre} ». Vous pouvez maintenant y accéder.',
            notification_type='payment',
            sender=None,
        )
        
        # Create user notification
        un, _ = UserNotification.objects.get_or_create(
            user=user,
            notification=notif,
        )
        
        logger.info(f'📥 [Task] Notification achat créée pour {user.username} — résumé {summary.titre}')
        
        # Send FCM
        send_fcm_notification.apply_async(args=[[un.id]], countdown=1)
        
        return {'notification_id': notif.id, 'user_id': user.id, 'summary_id': summary.id}
        
    except Exception as exc:
        logger.error(f'❌ [Task] notify_summary_purchased échoué: {exc}')
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=10)
def notify_subscription_payment_failed(self, abonnement_id: int, error_reason: str = None):
    """
    Notify user when their subscription payment fails.
    """
    try:
        from payments.models import Abonnement
        from .models import AppNotification, UserNotification

        abonnement = Abonnement.objects.select_related('user', 'service').get(id=abonnement_id)
        user = abonnement.user
        service = abonnement.service

        # Create notification
        error_msg = error_reason or 'Une erreur est survenue lors du traitement de votre paiement.'
        notif = AppNotification.objects.create(
            title='❌ Paiement échoué',
            body=f'Votre paiement pour l\'abonnement {service.nom} a échoué. {error_msg} Veuillez réessayer.',
            notification_type='payment',
            sender=None,
        )
        
        # Create user notification
        un, _ = UserNotification.objects.get_or_create(
            user=user,
            notification=notif,
        )
        
        logger.warning(f'❌ [Task] Notification échec paiement créée pour {user.username} — {error_msg}')
        
        # Send FCM
        send_fcm_notification.apply_async(args=[[un.id]], countdown=1)
        
        return {'notification_id': notif.id, 'user_id': user.id}
        
    except Exception as exc:
        logger.error(f'❌ [Task] notify_subscription_payment_failed échoué: {exc}')
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=10)
def notify_summary_purchase_failed(self, purchase_id: int, error_reason: str = None):
    """
    Notify user when their summary purchase fails.
    """
    try:
        from payments.models import Purchase
        from .models import AppNotification, UserNotification

        purchase = Purchase.objects.select_related('user', 'summary').get(id=purchase_id)
        user = purchase.user
        summary = purchase.summary

        # Create notification
        error_msg = error_reason or 'Une erreur est survenue lors du traitement de votre paiement.'
        notif = AppNotification.objects.create(
            title='❌ Achat échoué',
            body=f'Votre achat du résumé « {summary.titre} » a échoué. {error_msg} Veuillez réessayer.',
            notification_type='payment',
            sender=None,
        )
        
        # Create user notification
        un, _ = UserNotification.objects.get_or_create(
            user=user,
            notification=notif,
        )
        
        logger.warning(f'❌ [Task] Notification échec achat créée pour {user.username} — {error_msg}')
        
        # Send FCM
        send_fcm_notification.apply_async(args=[[un.id]], countdown=1)
        
        return {'notification_id': notif.id, 'user_id': user.id}
        
    except Exception as exc:
        logger.error(f'❌ [Task] notify_summary_purchase_failed échoué: {exc}')
        raise self.retry(exc=exc)


# ─────────────────────────────────────────────────────────────────────────────
#  Token Cleanup
# ─────────────────────────────────────────────────────────────────────────────

@shared_task(bind=True)
def cleanup_inactive_tokens(self):
    """
    Delete inactive FCM tokens older than 30 days to prevent database bloat.
    Run daily via Celery Beat.
    """
    try:
        from datetime import timedelta
        from django.utils import timezone
        from .models import UserDevice
        
        cutoff_date = timezone.now() - timedelta(days=30)
        
        # Delete inactive tokens older than 30 days
        deleted_count, _ = UserDevice.objects.filter(
            is_active=False,
            updated_at__lt=cutoff_date
        ).delete()
        
        logger.info(f'🗑️ [Task] {deleted_count} tokens inactifs supprimés (> 30 jours)')
        
        return {'deleted_count': deleted_count}
        
    except Exception as exc:
        logger.error(f'❌ [Task] cleanup_inactive_tokens échoué: {exc}')
        raise self.retry(exc=exc)
