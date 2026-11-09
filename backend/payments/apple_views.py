"""Endpoints Apple In-App Purchase (tâche 71)."""

import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .apple_iap import (
    AppleIapError,
    _summary_products,
    ensure_app_account_token,
    process_notification,
    process_transaction,
)
from .models import Service

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def apple_products_view(request):
    """Configuration produits Apple pour le client iOS.

    Endpoint PUBLIC : uniquement les identifiants produits et les prix
    (informations App Store publiques). Aucun secret, aucun identifiant
    d'utilisateur ni donnée personnelle.

    `app_account_token` n'est renseigné que pour un appelant authentifié
    (c'est son propre jeton opaque StoreKit) ; il vaut `null` pour un appel
    anonyme.
    """
    summary_products = [
        {
            'product_id': offre.product_id,
            # Noms explicites : le prix métier du résumé est en CDF, le prix
            # Apple et sa devise sont distincts (aucune conversion supposée).
            'business_price': str(offre.summary_price),
            'business_currency': 'CDF',
            'apple_price': (
                str(offre.apple_price) if offre.apple_price is not None else None
            ),
            'apple_currency': offre.currency or None,
            # Compatibilité avec les clients précédents.
            'price': str(offre.summary_price),
            'currency': offre.currency or None,
        }
        for offre in sorted(
            _summary_products().values(), key=lambda item: item.summary_price
        )
    ]

    subscriptions = list(
        Service.objects.filter(is_active=True)
        .exclude(apple_product_id='')
        .values(
            'id', 'nom', 'price', 'currency', 'apple_product_id',
            'apple_price', 'apple_currency',
        )
    )

    profile = getattr(request.user, 'profile', None)
    app_account_token = (
        ensure_app_account_token(profile) if profile is not None else None
    )

    return Response({
        'app_account_token': app_account_token,
        'summary_products': summary_products,
        'subscriptions': [
            {
                'service_id': service['id'],
                'service_name': service['nom'],
                'product_id': service['apple_product_id'],
                'business_price': str(service['price']),
                'business_currency': service['currency'],
                'apple_price': (
                    str(service['apple_price'])
                    if service['apple_price'] is not None else None
                ),
                'apple_currency': service['apple_currency'] or None,
                # Compatibilité avec les clients précédents.
                'price': str(service['price']),
                'currency': service['currency'],
            }
            for service in subscriptions
        ],
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def apple_verify_view(request):
    """Valide une transaction Apple signée et attribue le droit au compte."""
    signed_transaction = request.data.get('signed_transaction')
    summary_id = request.data.get('summary_id')

    if not signed_transaction:
        return Response(
            {'error': 'signed_transaction est requis'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        apple_transaction = process_transaction(
            request.user, signed_transaction, summary_id=summary_id
        )
    except AppleIapError as exc:
        return Response({'error': exc.message}, status=exc.status_code)
    except Exception:
        logger.exception('Erreur de validation Apple IAP')
        return Response(
            {'error': 'Impossible de valider la transaction Apple.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response({
        'success': True,
        'transaction_id': apple_transaction.transaction_id,
        'kind': apple_transaction.kind,
        'status': apple_transaction.status,
    }, status=status.HTTP_200_OK)


@csrf_exempt
@require_POST
def apple_notifications_view(request):
    """App Store Server Notifications V2 (Apple → backend)."""
    try:
        body = json.loads(request.body.decode('utf-8') if request.body else '{}')
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({'error': 'JSON invalide'}, status=400)

    signed_payload = body.get('signedPayload')
    if not signed_payload:
        return JsonResponse({'error': 'signedPayload requis'}, status=400)

    try:
        result = process_notification(signed_payload)
    except AppleIapError as exc:
        return JsonResponse({'error': exc.message}, status=exc.status_code)
    except Exception:
        logger.exception('Erreur de traitement d’une notification Apple')
        # 500 : Apple réessaiera la notification.
        return JsonResponse({'error': 'Erreur de traitement'}, status=500)

    return JsonResponse({'status': result.get('status', 'processed')})
