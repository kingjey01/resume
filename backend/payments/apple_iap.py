"""Validation Apple In-App Purchase (tâche 71).

Le backend reste l'autorité des droits :
- la transaction signée Apple (JWS) est vérifiée cryptographiquement avec la
  bibliothèque officielle `app-store-server-library` et les certificats racines
  Apple (publics, versionnés dans `apple_root_certs/`) ;
- l'identifiant produit, le bundle ID, la transaction et l'environnement sont
  contrôlés côté serveur ;
- les transactions et notifications sont idempotentes (contraintes uniques).

Aucune clé privée, aucun reçu brut et aucun identifiant Apple ne sont stockés.
"""

import json
import logging
import uuid
from datetime import datetime, timezone as dt_timezone
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.utils import timezone

from appstoreserverlibrary.models.Environment import Environment
from appstoreserverlibrary.signed_data_verifier import (
    SignedDataVerifier,
    VerificationException,
)

from courses.models import Summary
from users.models import UserProfile

from .models import Abonnement, AppleNotification, AppleTransaction, Purchase, Service

logger = logging.getLogger(__name__)


class AppleIapError(Exception):
    """Erreur métier Apple IAP, avec code HTTP associé."""

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def app_account_token_for_user(user_id):
    """UUID stable dérivé du compte Django (même valeur côté Flutter/Apple)."""
    return uuid.uuid5(uuid.NAMESPACE_URL, f'muhtasari:user:{user_id}')


def ensure_app_account_token(profile):
    """Retourne (et enregistre au besoin) le jeton StoreKit du profil."""
    if profile.apple_app_account_token:
        return str(profile.apple_app_account_token)
    token = app_account_token_for_user(profile.user_id)
    profile.apple_app_account_token = token
    profile.save(update_fields=['apple_app_account_token'])
    return str(token)


# ─── Configuration ───────────────────────────────────────────────────────────


def _summary_products():
    """Retourne {product_id: Decimal(prix_cdf)} depuis APPLE_SUMMARY_PRODUCTS."""
    raw = getattr(settings, 'APPLE_SUMMARY_PRODUCTS', '{}')
    if isinstance(raw, dict):
        data = raw
    else:
        try:
            data = json.loads(raw or '{}')
        except (TypeError, ValueError):
            logger.error('APPLE_SUMMARY_PRODUCTS invalide (JSON attendu)')
            return {}
    result = {}
    for product_id, value in (data or {}).items():
        try:
            result[str(product_id)] = Decimal(str(value))
        except Exception:
            continue
    return result


def _environment():
    name = (getattr(settings, 'APPLE_ENVIRONMENT', 'Sandbox') or 'Sandbox').strip().lower()
    mapping = {
        'sandbox': Environment.SANDBOX,
        'production': Environment.PRODUCTION,
        'xcode': Environment.XCODE,
        'localtesting': Environment.LOCAL_TESTING,
    }
    return mapping.get(name, Environment.SANDBOX)


def _root_certificates():
    dossier = Path(__file__).resolve().parent / 'apple_root_certs'
    return [fichier.read_bytes() for fichier in sorted(dossier.glob('*.cer'))]


_verifier_cache = None


def get_verifier():
    """Construit (et met en cache) le vérificateur Apple officiel."""
    global _verifier_cache
    if _verifier_cache is not None:
        return _verifier_cache

    certs = _root_certificates()
    if not certs:
        raise AppleIapError(
            "Certificats racines Apple absents sur le serveur.", 503
        )

    bundle_id = getattr(settings, 'APPLE_BUNDLE_ID', '')
    if not bundle_id:
        raise AppleIapError("APPLE_BUNDLE_ID n'est pas configuré.", 503)

    app_apple_id = getattr(settings, 'APPLE_APP_APPLE_ID', '')
    try:
        app_apple_id = int(app_apple_id) if str(app_apple_id).strip() else None
    except (TypeError, ValueError):
        app_apple_id = None

    environment = _environment()
    _verifier_cache = SignedDataVerifier(
        certs,
        enable_online_checks=(environment == Environment.PRODUCTION),
        environment=environment,
        bundle_id=bundle_id,
        app_apple_id=app_apple_id,
    )
    return _verifier_cache


def _env_value(value):
    return getattr(value, 'value', str(value) if value is not None else '')


def _ms_to_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value if timezone.is_aware(value) else timezone.make_aware(value)
    try:
        return datetime.fromtimestamp(int(value) / 1000, tz=dt_timezone.utc)
    except (TypeError, ValueError, OverflowError):
        return None


# ─── Vérification ────────────────────────────────────────────────────────────


def verify_signed_transaction(signed_transaction):
    """Vérifie la signature Apple et contrôle les champs essentiels."""
    if not signed_transaction or not isinstance(signed_transaction, str):
        raise AppleIapError('Transaction Apple signée manquante.')

    try:
        payload = get_verifier().verify_and_decode_signed_transaction(
            signed_transaction
        )
    except VerificationException:
        raise AppleIapError('Transaction Apple invalide ou signature refusée.')
    except AppleIapError:
        raise
    except Exception as exc:
        logger.warning('Apple IAP : vérification impossible (%s)', type(exc).__name__)
        raise AppleIapError('Transaction Apple invalide.')

    bundle_id = getattr(settings, 'APPLE_BUNDLE_ID', '')
    if getattr(payload, 'bundleId', None) != bundle_id:
        raise AppleIapError('Bundle ID Apple incohérent.')

    if not getattr(payload, 'productId', None):
        raise AppleIapError('Produit Apple absent de la transaction.')
    if not getattr(payload, 'transactionId', None):
        raise AppleIapError('Identifiant de transaction Apple absent.')

    if getattr(payload, 'revocationDate', None):
        raise AppleIapError('Cette transaction Apple a été révoquée ou remboursée.')

    return payload


# ─── Attribution ─────────────────────────────────────────────────────────────


def _creer_achat_apple(user, payload, **kwargs):
    environnement = _env_value(getattr(payload, 'environment', ''))
    return Purchase.objects.create(
        user=user,
        payer=user,
        source='apple',
        payment_method='apple',
        status='completed',
        completed_at=timezone.now(),
        transaction_id=payload.transactionId,
        apple_transaction_id=payload.transactionId,
        apple_original_transaction_id=getattr(
            payload, 'originalTransactionId', None
        ),
        apple_environment=environnement,
        **kwargs,
    )


def _grant_subscription(user, service, payload):
    expires = _ms_to_datetime(getattr(payload, 'expiresDate', None))
    now = timezone.now()
    if expires is not None and expires <= now:
        raise AppleIapError('Cet abonnement Apple a expiré.')

    original_id = getattr(payload, 'originalTransactionId', None) or payload.transactionId
    environnement = _env_value(getattr(payload, 'environment', ''))

    _creer_achat_apple(
        user, payload, summary=None, service=service, amount=service.price,
    )

    abonnement = (
        Abonnement.objects.select_for_update()
        .filter(
            user=user,
            service=service,
            source='apple',
            apple_original_transaction_id=original_id,
        )
        .order_by('-date_fin')
        .first()
    )

    if abonnement is None:
        abonnement = Abonnement.objects.create(
            user=user,
            payer=user,
            service=service,
            source='apple',
            apple_original_transaction_id=original_id,
            apple_environment=environnement,
            date_debut=now,
            date_fin=expires or service.get_date_fin(now),
            status='active',
            auto_renew=True,
            progress=0,
        )
    else:
        champs = ['auto_renew', 'status']
        abonnement.auto_renew = True
        abonnement.status = 'active'
        if expires is not None and expires > abonnement.date_fin:
            abonnement.date_fin = expires
            champs.append('date_fin')
        abonnement.apple_environment = environnement
        champs.append('apple_environment')
        abonnement.save(update_fields=champs)

    return abonnement


def process_transaction(user, signed_transaction, summary_id=None):
    """Vérifie et attribue une transaction Apple au compte authentifié.

    Retourne l'objet `AppleTransaction` (idempotent).
    """
    payload = verify_signed_transaction(signed_transaction)
    product_id = str(payload.productId)
    transaction_id = str(payload.transactionId)
    environnement = _env_value(getattr(payload, 'environment', ''))

    summary_products = _summary_products()

    with transaction.atomic():
        # Verrou par utilisateur : deux validations simultanées du même compte
        # (double requête, reprise réseau) sont sérialisées avant toute
        # création d'achat/abonnement.
        User.objects.select_for_update().get(pk=user.pk)

        existante = (
            AppleTransaction.objects.select_for_update()
            .filter(transaction_id=transaction_id)
            .first()
        )
        if existante is not None:
            if existante.user_id != user.id:
                raise AppleIapError(
                    'Cette transaction Apple est déjà associée à un autre compte.',
                    409,
                )
            return existante

        if product_id in summary_products:
            if not summary_id:
                raise AppleIapError('summary_id est requis pour ce produit Apple.')
            try:
                summary = Summary.objects.select_related('course').get(id=summary_id)
            except Summary.DoesNotExist:
                raise AppleIapError('Résumé introuvable.', 404)

            prix_attendu = summary_products[product_id]
            if Decimal(str(summary.prix)) != prix_attendu:
                raise AppleIapError(
                    'Le produit Apple ne correspond pas au prix du résumé.'
                )

            if Purchase.objects.filter(
                user=user, summary=summary, status='completed'
            ).exists():
                raise AppleIapError('Vous possédez déjà ce résumé.', 409)

            _creer_achat_apple(
                user, payload, summary=summary, service=None,
                amount=summary.prix,
            )
            kind = 'consumable'
            expires = None

        else:
            service = Service.objects.filter(
                apple_product_id=product_id, is_active=True
            ).first()
            if service is None:
                raise AppleIapError('Produit Apple inconnu pour ce service.')

            _grant_subscription(user, service, payload)
            kind = 'subscription'
            expires = _ms_to_datetime(getattr(payload, 'expiresDate', None))

        try:
            apple_transaction = AppleTransaction.objects.create(
                user=user,
                product_id=product_id,
                transaction_id=transaction_id,
                original_transaction_id=getattr(
                    payload, 'originalTransactionId', None
                ),
                purchase_date=_ms_to_datetime(
                    getattr(payload, 'purchaseDate', None)
                ),
                expires_date=expires,
                environment=environnement,
                status='granted',
                kind=kind,
            )
        except IntegrityError:
            # Course entre deux validations simultanées : la contrainte unique
            # a déjà enregistré la transaction.
            apple_transaction = AppleTransaction.objects.get(
                transaction_id=transaction_id
            )
            if apple_transaction.user_id != user.id:
                raise AppleIapError(
                    'Cette transaction Apple est déjà associée à un autre compte.',
                    409,
                )

    return apple_transaction


# ─── Notifications serveur Apple V2 ──────────────────────────────────────────


def _changer_etat_abonnement(original_id, *, statut=None, auto_renew=None):
    if not original_id:
        return 0
    qs = Abonnement.objects.filter(
        source='apple', apple_original_transaction_id=original_id
    )
    if statut is not None:
        qs = qs.update(status=statut)
    if auto_renew is not None:
        for abonnement in Abonnement.objects.select_for_update().filter(
            source='apple', apple_original_transaction_id=original_id
        ):
            abonnement.auto_renew = auto_renew
            abonnement.save(update_fields=['auto_renew'])
    return qs


def _refuser_achat_apple(transaction_id):
    if not transaction_id:
        return 0
    return Purchase.objects.filter(
        source='apple', apple_transaction_id=transaction_id
    ).update(status='refunded')


def process_notification(signed_payload):
    """Traite une App Store Server Notification V2, de façon idempotente."""
    if not signed_payload or not isinstance(signed_payload, str):
        raise AppleIapError('signedPayload manquant.')

    try:
        decoded = get_verifier().verify_and_decode_notification(signed_payload)
    except VerificationException:
        raise AppleIapError('Notification Apple invalide ou signature refusée.')
    except AppleIapError:
        raise
    except Exception as exc:
        logger.warning('Apple notification : vérification impossible (%s)',
                       type(exc).__name__)
        raise AppleIapError('Notification Apple invalide.')

    notification_uuid = getattr(decoded, 'notificationUUID', None)
    if not notification_uuid:
        raise AppleIapError('notificationUUID absent.')

    type_name = getattr(getattr(decoded, 'notificationType', None), 'name', None) \
        or _env_value(getattr(decoded, 'notificationType', ''))
    subtype = getattr(getattr(decoded, 'subtype', None), 'name', None) \
        or _env_value(getattr(decoded, 'subtype', '')) or None
    data = getattr(decoded, 'data', None)

    signed_txn = getattr(data, 'signedTransactionInfo', None)
    payload = None
    if signed_txn:
        try:
            payload = verify_signed_transaction(signed_txn)
        except AppleIapError:
            payload = None

    transaction_id = getattr(payload, 'transactionId', None) if payload else getattr(
        data, 'transactionId', None
    )
    original_id = getattr(payload, 'originalTransactionId', None) if payload else None
    environnement = getattr(payload, 'environment', None) if payload else getattr(
        data, 'environment', None
    )

    with transaction.atomic():
        notification_obj, created = AppleNotification.objects.get_or_create(
            notification_uuid=notification_uuid,
            defaults={
                'notification_type': type_name or 'UNKNOWN',
                'subtype': subtype,
                'transaction_id': transaction_id,
                'original_transaction_id': original_id,
                'environment': _env_value(environnement) or None,
            },
        )

        if not created and notification_obj.processing_status == 'processed':
            return {'status': 'duplicate'}

        try:
            record = AppleTransaction.objects.filter(
                transaction_id=transaction_id
            ).first() if transaction_id else None
            if record is None and original_id:
                record = (
                    AppleTransaction.objects
                    .filter(original_transaction_id=original_id)
                    .order_by('-created_at')
                    .first()
                )

            profil = None
            if record is None:
                # Achat initial avant validation client : StoreKit a transmis
                # l'appAccountToken, qui identifie le compte Django.
                token = getattr(payload, 'appAccountToken', None) if payload else None
                if token:
                    profil = (
                        UserProfile.objects.select_related('user')
                        .filter(apple_app_account_token=token)
                        .first()
                    )

            if record is None and profil is None:
                notification_obj.processing_status = 'ignored'
                notification_obj.processed_at = timezone.now()
                notification_obj.save(
                    update_fields=['processing_status', 'processed_at']
                )
                return {'status': 'ignored'}

            user = record.user if record is not None else profil.user

            if type_name in (
                'SUBSCRIBED', 'DID_RENEW', 'OFFER_REDEEMED',
                'RENEWAL_EXTENDED', 'MIGRATION',
            ) and payload is not None:
                service = Service.objects.filter(
                    apple_product_id=str(payload.productId), is_active=True
                ).first()
                if service is not None:
                    with transaction.atomic():
                        User.objects.select_for_update().get(pk=user.pk)
                        # Le client a peut-être déjà validé cette transaction :
                        # ne pas recréer un achat ni prolonger deux fois.
                        if not AppleTransaction.objects.filter(
                            transaction_id=payload.transactionId
                        ).exists():
                            _grant_subscription(user, service, payload)
                            AppleTransaction.objects.create(
                                user=user,
                                product_id=str(payload.productId),
                                transaction_id=payload.transactionId,
                                original_transaction_id=getattr(
                                    payload, 'originalTransactionId', None
                                ),
                                purchase_date=_ms_to_datetime(
                                    getattr(payload, 'purchaseDate', None)
                                ),
                                expires_date=_ms_to_datetime(
                                    getattr(payload, 'expiresDate', None)
                                ),
                                environment=_env_value(
                                    getattr(payload, 'environment', '')
                                ),
                                status='granted',
                                kind='subscription',
                            )

            elif type_name in ('EXPIRED', 'GRACE_PERIOD_EXPIRED'):
                _changer_etat_abonnement(original_id, statut='expired')

            elif type_name == 'DID_CHANGE_RENEWAL_STATUS':
                if subtype == 'AUTO_RENEW_DISABLED':
                    _changer_etat_abonnement(original_id, auto_renew=False)
                elif subtype == 'AUTO_RENEW_ENABLED':
                    _changer_etat_abonnement(original_id, auto_renew=True)

            elif type_name in ('REFUND', 'REVOKE'):
                _refuser_achat_apple(transaction_id)
                _changer_etat_abonnement(original_id, statut='cancelled')
                if transaction_id:
                    AppleTransaction.objects.filter(
                        transaction_id=transaction_id
                    ).update(status='refunded' if type_name == 'REFUND' else 'revoked')

            notification_obj.processing_status = 'processed'
            notification_obj.processed_at = timezone.now()
            notification_obj.save(
                update_fields=['processing_status', 'processed_at']
            )
            return {'status': 'processed', 'type': type_name, 'subtype': subtype}

        except Exception as exc:
            notification_obj.processing_status = 'error'
            notification_obj.error_message = str(exc)[:255]
            notification_obj.save(
                update_fields=['processing_status', 'error_message']
            )
            logger.error('Apple notification %s en erreur: %s', notification_uuid, exc)
            raise
