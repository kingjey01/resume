import random
import string
import json
import requests
from django.conf import settings
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
from courses.models import Summary


def get_random_string(length):
    """Génère une chaîne aléatoire de lettres minuscules"""
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))


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
        phone_number = data.get('phone_number')

        request_user = user

        print(f"🔍 service_id: {service_id}")
        print(f"📱 phone_number: {phone_number}")

        if not service_id:
            print("❌ ID du service manquant")
            return Response({'error': 'ID du service requis'}, status=status.HTTP_400_BAD_REQUEST)

        if not phone_number:
            print("❌ Numéro de téléphone manquant")
            return Response({'error': 'Numéro de téléphone requis'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            service = Service.objects.get(id=service_id, is_active=True)
            print(f"✅ Service trouvé: {service.nom} - Prix: {service.price} - Devise: {service.currency}")
        except Service.DoesNotExist:
            print(f"❌ Service non trouvé pour ID: {service_id}")
            return Response({'error': 'Service non trouvé'}, status=status.HTTP_404_NOT_FOUND)

        # Formater le numéro de téléphone
        phone_number = str(phone_number).strip().replace("+", "").replace(" ", "")
        print(f"📱 Numéro brut: {phone_number}")

        if len(phone_number) == 9 and phone_number.isdigit():
            phone_number = f"0{phone_number}"
            print(f"📱 Numéro formaté avec 0: {phone_number}")

        if phone_number.startswith("0"):
            phone_number = f"243{phone_number[1:]}"
            print(f"📱 Numéro formaté avec 243: {phone_number}")

        # Générer une référence unique
        reference = f"{get_random_string(8)}{phone_number}"
        print(f"🔗 Référence générée: {reference}")

        # ===== MODE SIMULATION (DEBUG) =====
        if settings.DEBUG:
            print(f"🧪 Mode simulation activé pour {service.nom}")
            paiement = Purchase.objects.create(
                user=request_user,
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
                user=request_user,
                service=service,
                status='active'
            ).exists()

            if not existing_active:
                abonnement = Abonnement.objects.create(
                    user=request_user,
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

        url = "https://backend.flexpay.cd/api/rest/v1/paymentService"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJcL2xvZ2luIiwicm9sZXMiOlsiTUVSQ0hBTlQiXSwiZXhwIjoxODE3MDMxOTg3LCJzdWIiOiIyZjgzYjc5NmFhZTg2MTgxNTViMjk4MGYxMGEwNDY1ZiJ9.3bDE4dfkVD8qMrxHgG1UIRVYi3Ey1zEcRRbByq02vpc",
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
                    user=request_user,
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
        phone_number = data.get('phone_number')

        print(f"🚀 Début _process_summary_purchase — user={user.username}, summary={summary.titre}, prix={summary.prix}")

        if not phone_number:
            return Response({'error': 'Numéro de téléphone requis'}, status=status.HTTP_400_BAD_REQUEST)

        # Formater le numéro de téléphone
        phone_number = str(phone_number).strip().replace('+', '').replace(' ', '')
        if len(phone_number) == 9 and phone_number.isdigit():
            phone_number = f'0{phone_number}'
        if phone_number.startswith('0'):
            phone_number = f'243{phone_number[1:]}'

        print(f"📱 Numéro formaté: {phone_number}")

        reference = f"{get_random_string(8)}{phone_number}"
        print(f"🔗 Référence: {reference}")

        # ===== MODE SIMULATION (DEBUG) =====
        if settings.DEBUG:
            print(f"🧪 Mode simulation activé pour résumé {summary.titre}")
            paiement = Purchase.objects.create(
                user=user,
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

        url = 'https://backend.flexpay.cd/api/rest/v1/paymentService'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJcL2xvZ2luIiwicm9sZXMiOlsiTUVSQ0hBTlQiXSwiZXhwIjoxODE3MDMxOTg3LCJzdWIiOiIyZjgzYjc5NmFhZTg2MTgxNTViMjk4MGYxMGEwNDY1ZiJ9.3bDE4dfkVD8qMrxHgG1UIRVYi3Ey1zEcRRbByq02vpc',
        }

        try:
            print("🌐 Envoi requête à FlexPay...")
            response = requests.post(url, headers=headers, data=json.dumps(flexpay_data), timeout=30)
            response.raise_for_status()

            jsonRes = response.json()
            print(f"📄 Réponse FlexPay: {jsonRes}")

            if jsonRes.get('code') == '0':
                paiement = Purchase.objects.create(
                    user=user,
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

        existing_purchase = Purchase.objects.filter(
            user=request.user,
            summary=summary,
            status='completed'
        ).first()

        if existing_purchase:
            return Response({'error': 'Vous avez déjà acheté ce résumé'},
                            status=status.HTTP_400_BAD_REQUEST)

        return _process_summary_purchase(request.user, request.data, summary)

    except Exception as e:
        print(f"💥 Erreur générale dans initiate_summary_purchase: {e}")
        print(traceback.format_exc())
        return Response({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
            # Paiement réussi
            try:
                purchase = Purchase.objects.get(transaction_id=reference, status='pending')
                print(f"🎯 Achat trouvé: ID {purchase.id}, Utilisateur: {purchase.user.username}")
                
                purchase.status = 'completed'
                purchase.completed_at = timezone.now()
                purchase.save()

                print(f"💰 Achat {purchase.id} marqué comme complété à {purchase.completed_at}")

                # Si c'est un paiement d'abonnement (service lié, pas de résumé)
                if purchase.service and not purchase.summary:
                    print(f"� Paiement d'abonnement confirmé pour service: {purchase.service.nom}")

                    existing_active = Abonnement.objects.filter(
                        user=purchase.user,
                        service=purchase.service,
                        status='active',
                        date_fin__gt=timezone.now()
                    ).exists()

                    if not existing_active:
                        date_debut = timezone.now()
                        date_fin = purchase.service.get_date_fin(date_debut)
                        abonnement = Abonnement.objects.create(
                            user=purchase.user,
                            service=purchase.service,
                            date_debut=date_debut,
                            date_fin=date_fin,
                            status='active',
                            auto_renew=False,
                            progress=0,
                        )
                        print(f"✅ Abonnement créé: ID {abonnement.id}, Fin: {date_fin}")
                    else:
                        print("⚠️ Abonnement actif déjà existant, non recréé")
                elif purchase.summary:
                    print(f"📚 Résumé associé: {purchase.summary.titre} — accessible par l'utilisateur")

                response_data = {'msg': 'Paiement confirmé avec succès', 'id': '1'}
                print(f"📤 Réponse envoyée: {response_data}")
                return JsonResponse(response_data)

            except Purchase.DoesNotExist:
                print(f"❌ Achat non trouvé pour la référence: {reference}")
                response_data = {'msg': 'Paiement non trouvé', 'id': '0'}
                return JsonResponse(response_data)

        else:
            print(f"❌ Paiement échoué - Code: {code}")
            # Paiement échoué
            try:
                purchase = Purchase.objects.get(transaction_id=reference, status='pending')
                purchase.status = 'failed'
                purchase.save()
                print(f"💥 Achat {purchase.id} marqué comme échoué")
            except Purchase.DoesNotExist:
                print(f"⚠️ Achat non trouvé pour la référence: {reference}")
                pass

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
        purchase = Purchase.objects.get(
            transaction_id=transaction_id,
            user=request.user,
            status='completed'
        )
        service = Service.objects.get(id=service_id)

        # Vérifier si l'utilisateur a déjà un abonnement actif pour ce service
        existing_active = Abonnement.objects.filter(
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

        # Créer l'abonnement
        abonnement = Abonnement.objects.create(
            user=request.user,
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
