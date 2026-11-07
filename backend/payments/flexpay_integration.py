import random
import string
import json
import requests
from django.conf import settings
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import timedelta
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import Service, Abonnement, Purchase
from .serializers import AbonnementSerializer
from .beneficiary import (
    BeneficiaryError,
    normaliser_numero_paiement,
    resoudre_beneficiaire,
)
from courses.models import Summary


def get_random_string(length):
    """Génère une chaîne aléatoire de lettres minuscules"""
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))


def _flexpay_configuration():
    """Retourne (url, token) depuis la configuration, jamais depuis le code.

    Le jeton FlexPay est un secret d'API : il doit être fourni par
    `FLEXPAY_API_TOKEN` (variable d'environnement / backend/.env).
    """
    url = getattr(
        settings,
        'FLEXPAY_API_URL',
        'https://backend.flexpay.cd/api/rest/v1/paymentService',
    )
    token = (getattr(settings, 'FLEXPAY_API_TOKEN', '') or '').strip()
    return url, token


def _erreur_flexpay_non_configure():
    return Response(
        {'error': 'Le service de paiement n\'est pas configuré.'},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


# Une tentative de paiement « pending » au-delà de ce délai est considérée
# comme abandonnée (callback jamais reçu) → on la solde pour permettre de
# réessayer sans créer de doublon.
PENDING_EXPIRY_MINUTES = 15


def _check_duplicate_summary_purchase(user, summary):
    """
    Garde anti-doublon à l'initiation d'un achat de résumé.

    Règle métier : un résumé est « acheté » uniquement si une transaction
    validée existe. Une tentative échouée ne compte pas. Deux callbacks de
    succès sur deux lignes distinctes du même résumé ne doivent pas créer deux
    droits d'accès ni deux lignes « Résumés achetés ».

    Comportement :
    - s'il existe déjà un achat 'completed' pour (user, summary) → bloqué
      (« déjà acheté ») ;
    - les tentatives 'pending' OBSOLÈTES (> PENDING_EXPIRY_MINUTES) sont
      soldées en 'failed' (l'utilisateur a abandonné) pour permettre un nouvel
      essai ;
    - s'il reste une tentative 'pending' encore valide → bloqué (« paiement en
      cours ») : on évite d'empiler deux lignes pending qui seraient toutes
      deux marquées 'completed' par les callbacks ultérieurs.

    Retourne une chaîne d'erreur à renvoyer, ou None si l'initiation peut
    continuer.
    """
    if Purchase.objects.filter(
        user=user, summary=summary, status='completed'
    ).exists():
        return 'Vous avez déjà acheté ce résumé'

    cutoff = timezone.now() - timedelta(minutes=PENDING_EXPIRY_MINUTES)
    stale_pending = Purchase.objects.filter(
        user=user, summary=summary, status='pending', created_at__lt=cutoff
    )
    for stale in stale_pending:
        stale.status = 'failed'
        stale.save(update_fields=['status'])

    if Purchase.objects.filter(
        user=user, summary=summary, status='pending'
    ).exists():
        return 'Un paiement pour ce résumé est déjà en cours de validation. Veuillez patienter.'

    return None


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def initiate_subscription_payment(request):
    """
    Initier le paiement d'un abonnement via FlexPay
    En mode DEBUG, simule le paiement directement
    """
    return _process_subscription_payment(request.user, request.data)


def _process_subscription_payment(user, data):
    """
    Logique principale de paiement d'abonnement — appelable depuis n'importe quelle vue.
    Prend l'objet User et un dict de données (service_id, phone_number, ...).
    Retourne une DRF Response.
    """
    try:
        print(f"🚀 Début _process_subscription_payment")
        print(f"📦 Données reçues: {data}")
        print(f"👤 Utilisateur: {user.username} (ID: {user.id})")

        service_id = data.get('service_id')
        phone_number_raw = data.get('phone_number')

        print(f"🔍 service_id: {service_id}")
        print(f"📱 phone_number: {phone_number_raw}")

        if not service_id:
            print("❌ ID du service manquant")
            return Response({'error': 'ID du service requis'}, status=status.HTTP_400_BAD_REQUEST)

        if not phone_number_raw:
            print("❌ Numéro de téléphone manquant")
            return Response({'error': 'Numéro de téléphone requis'}, status=status.HTTP_400_BAD_REQUEST)

        # VALIDATION CÔTÉ SERVEUR : numéro du payeur.
        payer_phone = normaliser_numero_paiement(phone_number_raw)
        if not payer_phone:
            return Response(
                {'error': 'Numéro du payeur invalide.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            service = Service.objects.get(id=service_id, is_active=True)
            print(f"✅ Service trouvé: {service.nom} - Prix: {service.price} - Devise: {service.currency}")
        except Service.DoesNotExist:
            print(f"❌ Service non trouvé pour ID: {service_id}")
            return Response({'error': 'Service non trouvé'}, status=status.HTTP_404_NOT_FOUND)

        # Bénéficiaire : le payeur lui-même, ou un autre étudiant actif résolu
        # en base (tâche 70). Le numéro envoyé n'identifie jamais directement
        # le compte.
        try:
            beneficiaire, profil_beneficiaire = resoudre_beneficiaire(
                user, data.get('beneficiary_phone')
            )
        except BeneficiaryError as exc:
            return Response(
                {'error': exc.message}, status=exc.status_code
            )

        beneficiary_phone = (
            profil_beneficiaire.phone
            if profil_beneficiaire and profil_beneficiaire.phone
            else payer_phone
        )

        if beneficiaire.id != user.id:
            # Payer un abonnement à quelqu'un qui l'a déjà actif n'a pas de
            # sens : on refuse AVANT d'envoyer la demande Mobile Money.
            if Abonnement.objects.filter(
                user=beneficiaire,
                service=service,
                status='active',
                date_fin__gt=timezone.now(),
            ).exists():
                return Response(
                    {'error': 'Le bénéficiaire a déjà un abonnement actif pour ce service.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Éviter deux cadeaux simultanés au même bénéficiaire (deux
            # callbacks créeraient un seul abonnement mais deux débits).
            cutoff = timezone.now() - timedelta(minutes=PENDING_EXPIRY_MINUTES)
            Purchase.objects.filter(
                user=beneficiaire,
                service=service,
                status='pending',
                created_at__lt=cutoff,
            ).update(status='failed')

            if Purchase.objects.filter(
                user=beneficiaire,
                service=service,
                status='pending',
            ).exists():
                return Response(
                    {'error': 'Un paiement pour ce bénéficiaire est déjà en cours de validation.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Format attendu par FlexPay (243XXXXXXXXX).
        phone_number = f"243{payer_phone[1:]}"
        print(f"📱 Numéro payeur normalisé: {payer_phone} → {phone_number}")

        # Générer une référence unique
        reference = f"{get_random_string(8)}{phone_number}"
        print(f"🔗 Référence générée: {reference}")

        # ===== MODE SIMULATION (DEBUG) =====
        if settings.DEBUG:
            print(f"🧪 Mode simulation activé pour {service.nom}")
            paiement = Purchase.objects.create(
                user=beneficiaire,
                payer=user,
                payer_phone=payer_phone,
                beneficiary_phone=beneficiary_phone,
                summary=None,
                service=service,
                amount=service.price,
                payment_method='mobile_money',
                status='completed',
                transaction_id=reference,
                completed_at=timezone.now(),
            )
            print(f"💳 Paiement simulé créé: ID {paiement.id}")

            date_debut = timezone.now()
            date_fin = service.get_date_fin(date_debut)
            print(f"📅 Abonnement: {date_debut.date()} → {date_fin.date()} ({service.duree_mois} mois)")

            existing_active = Abonnement.objects.filter(
                user=beneficiaire,
                service=service,
                status='active'
            ).exists()

            if not existing_active:
                abonnement = Abonnement.objects.create(
                    user=beneficiaire,
                    payer=user,
                    service=service,
                    date_debut=date_debut,
                    date_fin=date_fin,
                    status='active',
                    auto_renew=False,
                    progress=0
                )
                print(f"✅ Abonnement créé: ID {abonnement.id}")
            else:
                print("⚠️ Abonnement actif existant, non recréé")

            return Response({
                'success': True,
                'message': 'Paiement simulé avec succès (mode développement)',
                'reference': reference,
                'order_number': f'SIM-{reference[:8]}',
                'amount': str(service.price),
                'currency': service.currency,
                'service': service.nom,
                'simulated': True,
                'debug': {
                    'mode': 'simulation',
                    'service_id': service_id,
                    'service_name': service.nom,
                    'payment_id': paiement.id,
                    'subscription_period': f"{date_debut} to {date_fin}"
                }
            })

        # ===== MODE PRODUCTION (FlexPay) =====
        print("🌐 Mode production - Appel à FlexPay")

        date_debut = timezone.now()
        date_fin = service.get_date_fin(date_debut)
        print(f"📅 Abonnement: {date_debut.date()} → {date_fin.date()} ({service.duree_mois} mois)")

        try:
            callback_urls = getattr(settings, 'URL_CALLBACK', ['https://resumecours.gestionhospitaliare.site'])
            callback_url = f"{callback_urls[0]}/api/flexpay-callback/"
            print(f"🔗 URL de callback: {callback_url}")
        except Exception as e:
            print(f"⚠️ Erreur configuration URL_CALLBACK: {e}")
            callback_url = "https://resumecours.gestionhospitaliare.site/api/flexpay-callback/"

        flexpay_data = {
            "merchant": "DJANGO",
            "type": "1",
            "phone": phone_number,
            "reference": reference,
            "amount": str(service.price),
            "currency": service.currency,
            "callbackUrl": callback_url,
        }

        print(f"📤 Données FlexPay: {flexpay_data}")

        url, flexpay_token = _flexpay_configuration()
        if not flexpay_token:
            return _erreur_flexpay_non_configure()
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {flexpay_token}',
        }

        try:
            print("🌐 Envoi requête à FlexPay...")
            response = requests.post(url, headers=headers, data=json.dumps(flexpay_data), timeout=30)
            response.raise_for_status()

            print(f"✅ Réponse FlexPay status: {response.status_code}")
            jsonRes = response.json()
            print(f"📄 Réponse FlexPay: {jsonRes}")

            if jsonRes.get("code") == "0":
                paiement = Purchase.objects.create(
                    user=beneficiaire,
                    payer=user,
                    payer_phone=payer_phone,
                    beneficiary_phone=beneficiary_phone,
                    summary=None,
                    service=service,
                    amount=service.price,
                    payment_method='mobile_money',
                    status='pending',
                    transaction_id=reference,
                )
                print(f"💳 Paiement créé: ID {paiement.id}")

                return Response({
                    'success': True,
                    'message': jsonRes.get("message", "Paiement initié"),
                    'reference': reference,
                    'order_number': jsonRes.get('orderNumber'),
                    'amount': str(service.price),
                    'currency': service.currency,
                    'service': service.nom,
                    'debug': {
                        'mode': 'production',
                        'service_id': service_id,
                        'service_name': service.nom,
                        'payment_id': paiement.id,
                        'flexpay_response': jsonRes
                    }
                })
            else:
                print(f"❌ Erreur FlexPay: {jsonRes}")
                return Response({
                    'success': False,
                    'error': jsonRes.get("message", "Erreur lors de l'initiation du paiement"),
                    'debug': {
                        'flexpay_code': jsonRes.get("code"),
                        'flexpay_message': jsonRes.get("message"),
                        'sent_data': flexpay_data
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

        except requests.RequestException as e:
            print(f"❌ Erreur connexion FlexPay: {e}")
            import traceback
            print(f"📚 Traceback connexion: {traceback.format_exc()}")
            return Response({
                'success': False,
                'error': f'Erreur de connexion à FlexPay: {str(e)}',
                'debug': {
                    'exception_type': type(e).__name__,
                    'exception_message': str(e),
                    'url': url,
                    'timeout': 30
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        print(f"💥 Erreur générale dans _process_subscription_payment: {e}")
        import traceback
        print(f"📚 Traceback complet: {traceback.format_exc()}")
        return Response({
            'success': False,
            'error': f'Erreur serveur: {str(e)}',
            'debug': {
                'exception_type': type(e).__name__,
                'exception_message': str(e),
                'user_id': user.id if user else None,
                'traceback': traceback.format_exc()
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _process_summary_purchase(user, data, summary):
    """
    Logique principale de paiement de résumé — appelable depuis n'importe quelle vue.
    Prend l'objet User, un dict de données et l'objet Summary déjà validé.
    Retourne une DRF Response.
    """
    import traceback
    try:
        phone_number_raw = data.get('phone_number')

        print(f"🚀 Début _process_summary_purchase — user={user.username}, summary={summary.titre}, prix={summary.prix}")

        if not phone_number_raw:
            return Response({'error': 'Numéro de téléphone requis'}, status=status.HTTP_400_BAD_REQUEST)

        # VALIDATION CÔTÉ SERVEUR : numéro du payeur.
        payer_phone = normaliser_numero_paiement(phone_number_raw)
        if not payer_phone:
            return Response(
                {'error': 'Numéro du payeur invalide.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Bénéficiaire : payeur lui-même ou autre étudiant actif (tâche 70).
        try:
            beneficiaire, profil_beneficiaire = resoudre_beneficiaire(
                user, data.get('beneficiary_phone')
            )
        except BeneficiaryError as exc:
            return Response({'error': exc.message}, status=exc.status_code)

        beneficiary_phone = (
            profil_beneficiaire.phone
            if profil_beneficiaire and profil_beneficiaire.phone
            else payer_phone
        )

        # Garde anti-doublon : porte sur le BÉNÉFICIAIRE, jamais sur le payeur.
        duplicate_error = _check_duplicate_summary_purchase(beneficiaire, summary)
        if duplicate_error:
            message = duplicate_error
            if beneficiaire.id != user.id:
                message = 'Le bénéficiaire a déjà acheté ce résumé.'
            return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)

        # Format attendu par FlexPay (243XXXXXXXXX).
        phone_number = f"243{payer_phone[1:]}"
        print(f"📱 Numéro payeur normalisé: {payer_phone} → {phone_number}")

        reference = f"{get_random_string(8)}{phone_number}"
        print(f"🔗 Référence: {reference}")

        # ===== MODE SIMULATION (DEBUG) =====
        if settings.DEBUG:
            print(f"🧪 Mode simulation activé pour résumé {summary.titre}")
            paiement = Purchase.objects.create(
                user=beneficiaire,
                payer=user,
                payer_phone=payer_phone,
                beneficiary_phone=beneficiary_phone,
                summary=summary,
                amount=summary.prix,
                payment_method='mobile_money',
                status='completed',
                transaction_id=reference,
                completed_at=timezone.now(),
            )
            print(f"💳 Achat simulé créé: ID {paiement.id}")
            return Response({
                'success': True,
                'message': 'Paiement simulé avec succès (mode développement)',
                'reference': reference,
                'order_number': f'SIM-{reference[:8]}',
                'amount': str(summary.prix),
                'currency': 'CDF',
                'summary_title': summary.titre,
                'simulated': True,
            })

        # ===== MODE PRODUCTION (FlexPay) =====
        try:
            callback_urls = getattr(settings, 'URL_CALLBACK', ['https://resumecours.gestionhospitaliare.site'])
            callback_url = f"{callback_urls[0]}/api/flexpay-callback/"
        except Exception:
            callback_url = 'https://resumecours.gestionhospitaliare.site/api/flexpay-callback/'

        flexpay_data = {
            'merchant': 'DJANGO',
            'type': '1',
            'phone': phone_number,
            'reference': reference,
            'amount': str(summary.prix),
            'currency': 'CDF',
            'callbackUrl': callback_url,
        }

        print(f"📤 Données FlexPay: {flexpay_data}")

        url, flexpay_token = _flexpay_configuration()
        if not flexpay_token:
            return _erreur_flexpay_non_configure()
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {flexpay_token}',
        }

        try:
            print("🌐 Envoi requête à FlexPay...")
            response = requests.post(url, headers=headers, data=json.dumps(flexpay_data), timeout=30)
            response.raise_for_status()

            jsonRes = response.json()
            print(f"📄 Réponse FlexPay: {jsonRes}")

            if jsonRes.get('code') == '0':
                paiement = Purchase.objects.create(
                    user=beneficiaire,
                    payer=user,
                    payer_phone=payer_phone,
                    beneficiary_phone=beneficiary_phone,
                    summary=summary,
                    amount=summary.prix,
                    payment_method='mobile_money',
                    status='pending',
                    transaction_id=reference,
                )
                print(f"💳 Achat créé en attente: ID {paiement.id}")
                return Response({
                    'success': True,
                    'message': jsonRes.get('message', 'Paiement initié'),
                    'reference': reference,
                    'order_number': jsonRes.get('orderNumber'),
                    'amount': str(summary.prix),
                    'currency': 'CDF',
                    'summary_title': summary.titre,
                })
            else:
                print(f"❌ Rejet FlexPay: {jsonRes}")
                return Response({
                    'success': False,
                    'error': jsonRes.get('message', 'Erreur lors de l\'initiation du paiement'),
                }, status=status.HTTP_400_BAD_REQUEST)

        except requests.RequestException as e:
            print(f"❌ Erreur connexion FlexPay: {e}")
            print(traceback.format_exc())
            return Response({
                'success': False,
                'error': f'Erreur de connexion au service de paiement: {str(e)}',
            }, status=status.HTTP_502_BAD_GATEWAY)

    except Exception as e:
        print(f"💥 Erreur générale dans _process_summary_purchase: {e}")
        print(traceback.format_exc())
        return Response({
            'success': False,
            'error': f'Erreur serveur: {str(e)}',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def initiate_summary_purchase(request):
    """
    Initier l'achat d'un résumé via FlexPay (endpoint direct utilisé par le client Flutter)
    """
    import traceback
    try:
        summary_id = request.data.get('summary_id')
        phone_number = request.data.get('phone_number')

        print(f"🚀 initiate_summary_purchase — user={request.user.username}, summary_id={summary_id}")

        if not summary_id:
            return Response({'error': 'ID du résumé requis'}, status=status.HTTP_400_BAD_REQUEST)

        if not phone_number:
            return Response({'error': 'Numéro de téléphone requis'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            summary = Summary.objects.get(id=summary_id)
            print(f"✅ Résumé trouvé: {summary.titre} — prix={summary.prix}, is_free={summary.is_free}")
        except Summary.DoesNotExist:
            return Response({'error': 'Résumé non trouvé'}, status=status.HTTP_404_NOT_FOUND)

        if summary.is_free or summary.prix <= 0:
            return Response({
                'error': 'Ce résumé est gratuit ou son prix n\'est pas configuré. Aucun paiement requis.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # La garde anti-doublon est déléguée à `_process_summary_purchase`, qui
        # la vérifie sur le BÉNÉFICIAIRE (soi-même ou un autre étudiant).
        return _process_summary_purchase(request.user, request.data, summary)

    except Exception as e:
        print(f"💥 Erreur générale dans initiate_summary_purchase: {e}")
        print(traceback.format_exc())
        return Response({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _activer_abonnement_apres_paiement(purchase):
    """Crée l'abonnement du BÉNÉFICIAIRE après un paiement confirmé.

    À appeler dans une transaction et après verrouillage de la ligne Purchase :
    deux callbacks simultanés sur la même référence ne peuvent pas créer deux
    abonnements.
    """
    if not (purchase.service_id and not purchase.summary_id):
        return None

    existing_active = Abonnement.objects.select_for_update().filter(
        user_id=purchase.user_id,
        service_id=purchase.service_id,
        status='active',
        date_fin__gt=timezone.now(),
    ).exists()
    if existing_active:
        return None

    date_debut = timezone.now()
    return Abonnement.objects.create(
        user_id=purchase.user_id,
        payer_id=purchase.payer_id or purchase.user_id,
        service_id=purchase.service_id,
        date_debut=date_debut,
        date_fin=purchase.service.get_date_fin(date_debut),
        status='active',
        auto_renew=False,
        progress=0,
    )


@csrf_exempt
@require_POST
def flexpay_callback(request):
    """
    Callback FlexPay pour confirmer les paiements
    """
    try:
        print(f"🔔 Callback FlexPay reçu - Méthode: {request.method}")
        print(f"📦 Headers: {dict(request.headers)}")
        
        raw_body = request.body.decode('utf-8')
        print(f"� Body brut reçu: {raw_body}")
        
        # Nettoyer le body si nécessaire
        cleaned_body = raw_body.strip()
        if cleaned_body.startswith('{\\'):
            cleaned_body = cleaned_body.replace('{\\', '{').replace('\\}', '}')
        
        print(f"📄 Body nettoyé: {cleaned_body}")
        
        try:
            data = json.loads(cleaned_body)
        except json.JSONDecodeError as e:
            print(f"❌ Erreur JSON même après nettoyage: {e}")
            # Essayer de parser manuellement si c'est un format spécial
            if 'code' in raw_body and 'reference' in raw_body:
                # Extraction manuelle simple
                import re
                code_match = re.search(r'"code"\s*:\s*"([^"]+)"', raw_body)
                ref_match = re.search(r'"reference"\s*:\s*"([^"]+)"', raw_body)
                
                data = {}
                if code_match:
                    data['code'] = code_match.group(1)
                if ref_match:
                    data['reference'] = ref_match.group(1)
                print(f"� Données extraites manuellement: {data}")
            else:
                raise e
        
        print(f"�📋 Données parsées: {data}")

        code = data.get('code')
        reference = data.get('reference')
        
        print(f"🔍 Code de réponse: {code}")
        print(f"🔍 Référence transaction: {reference}")

        if code == "0":
            print("✅ Paiement réussi - Traitement en cours...")
            # Paiement réussi.
            #
            # Idempotence : la ligne est verrouillée et le statut 'pending'
            # fait office de verrou logique. Deux callbacks simultanés pour la
            # même référence ne peuvent pas créditer deux fois ; un callback
            # répété sur une transaction déjà complétée répond « succès »
            # (le fournisseur ne doit pas réessayer indéfiniment).
            try:
                with transaction.atomic():
                    purchase = (
                        Purchase.objects.select_for_update()
                        .select_related('user', 'service', 'summary')
                        .get(transaction_id=reference, status='pending')
                    )
                    print(f"🎯 Achat trouvé: ID {purchase.id}, Bénéficiaire: {purchase.user.username}")

                    purchase.status = 'completed'
                    purchase.completed_at = timezone.now()
                    purchase.save(update_fields=['status', 'completed_at'])

                    print(f"💰 Achat {purchase.id} marqué comme complété")

                    abonnement = _activer_abonnement_apres_paiement(purchase)
                    if abonnement:
                        print(f"✅ Abonnement créé: ID {abonnement.id}, Bénéficiaire: {abonnement.user.username}")
                    elif purchase.service and not purchase.summary:
                        print("⚠️ Abonnement actif déjà existant, non recréé")
                    elif purchase.summary:
                        print(f"📚 Résumé attribué à {purchase.user.username}: {purchase.summary.titre}")

                response_data = {'msg': 'Paiement confirmé avec succès', 'id': '1'}
                print(f"📤 Réponse envoyée: {response_data}")
                return JsonResponse(response_data)

            except Purchase.DoesNotExist:
                # Callback répété : la transaction est déjà complétée.
                if Purchase.objects.filter(
                    transaction_id=reference, status='completed'
                ).exists():
                    return JsonResponse({'msg': 'Paiement déjà confirmé', 'id': '1'})
                print(f"❌ Achat non trouvé pour la référence: {reference}")
                return JsonResponse({'msg': 'Paiement non trouvé', 'id': '0'})

        else:
            print(f"❌ Paiement échoué - Code: {code}")
            # Paiement échoué : aucune attribution.
            try:
                with transaction.atomic():
                    purchase = (
                        Purchase.objects.select_for_update()
                        .get(transaction_id=reference, status='pending')
                    )
                    purchase.status = 'failed'
                    purchase.save(update_fields=['status'])
                    print(f"💥 Achat {purchase.id} marqué comme échoué")
            except Purchase.DoesNotExist:
                print(f"⚠️ Achat non trouvé (ou déjà traité) pour la référence: {reference}")

            response_data = {'msg': f'Paiement échoué - Code: {code}', 'id': '0'}
            print(f"📤 Réponse échec envoyée: {response_data}")
            return JsonResponse(response_data)

    except Exception as e:
        print(f"❌ Erreur générale lors du traitement du callback: {e}")
        print(f"📄 Body reçu: {request.body}")
        return JsonResponse({'msg': f'Erreur lors du traitement: {str(e)}', 'id': '0'})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_subscription_after_payment(request):
    """
    Créer un abonnement après confirmation de paiement (appelée après callback réussi)
    """
    transaction_id = request.data.get('transaction_id')
    service_id = request.data.get('service_id')

    if not transaction_id or not service_id:
        return Response({'error': 'Transaction ID et Service ID requis'},
                       status=status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic():
            # `user=request.user` : seul le BÉNÉFICIAIRE peut se voir créer
            # l'abonnement. Pour un cadeau, le payeur n'a pas cette ligne à
            # son nom et le callback a déjà créé l'abonnement.
            purchase = (
                Purchase.objects.select_for_update()
                .get(
                    transaction_id=transaction_id,
                    user=request.user,
                    status='completed'
                )
            )
            service = Service.objects.get(id=service_id)

            # Vérifier si l'utilisateur a déjà un abonnement actif
            existing_active = Abonnement.objects.select_for_update().filter(
                user=request.user,
                service=service,
                status='active'
            ).exists()

            if existing_active:
                return Response({'error': 'Vous avez déjà un abonnement actif pour ce service'},
                               status=status.HTTP_400_BAD_REQUEST)

            # Calculer les dates via le modèle (centralisé)
            date_debut = timezone.now()
            date_fin = service.get_date_fin(date_debut)

            # Créer l'abonnement au nom du bénéficiaire, en conservant le payeur.
            abonnement = Abonnement.objects.create(
                user=request.user,
                payer=purchase.payer or purchase.user,
                service=service,
                date_debut=date_debut,
                date_fin=date_fin,
                status='active',
                auto_renew=False,
                progress=0
            )

        serializer = AbonnementSerializer(abonnement)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    except Purchase.DoesNotExist:
        return Response({'error': 'Paiement non trouvé ou non confirmé'},
                       status=status.HTTP_404_NOT_FOUND)
    except Service.DoesNotExist:
        return Response({'error': 'Service non trouvé'},
                       status=status.HTTP_404_NOT_FOUND)
