from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from django.utils import timezone
from datetime import timedelta
from .models import Purchase, Service, Abonnement
from .serializers import PurchaseSerializer, CreatePurchaseSerializer, ServiceSerializer, AbonnementSerializer
from courses.models import Summary

class PurchaseListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'payment_method']
    ordering_fields = ['created_at', 'amount']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return Purchase.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreatePurchaseSerializer
        return PurchaseSerializer
    
    def list(self, request, *args, **kwargs):
        """Simple list method without filters or pagination"""
        purchases = Purchase.objects.filter(user=request.user).order_by('-created_at')
        serializer = PurchaseSerializer(purchases, many=True)
        return Response(serializer.data)


class PurchaseDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PurchaseSerializer
    
    def get_queryset(self):
        return Purchase.objects.filter(user=self.request.user)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def complete_purchase(request, purchase_id):
    """
    Marquer un achat comme complété (simulation de paiement réussi)
    """
    try:
        purchase = Purchase.objects.get(id=purchase_id, user=request.user)
    except Purchase.DoesNotExist:
        return Response({'error': 'Achat non trouvé'}, status=status.HTTP_404_NOT_FOUND)
    
    if purchase.status != 'pending':
        return Response({'error': 'Cet achat ne peut pas être complété'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    # Simuler le traitement du paiement
    purchase.status = 'completed'
    purchase.completed_at = timezone.now()
    purchase.save()
    
    # Ajouter des points à l'utilisateur si le profil existe
    if hasattr(request.user, 'profile'):
        user_profile = request.user.profile
        user_profile.points += 10  # 10 points par achat
        user_profile.save()
    
    return Response(PurchaseSerializer(purchase).data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def simulate_payment(request):
    """
    Simuler un paiement complet (création + finalisation automatique)
    """
    summary_id = request.data.get('summary_id')
    payment_method = request.data.get('payment_method', 'card')
    
    if not summary_id:
        return Response({'error': 'ID du résumé requis'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        summary = Summary.objects.get(id=summary_id)
    except Summary.DoesNotExist:
        return Response({'error': 'Résumé non trouvé'}, status=status.HTTP_404_NOT_FOUND)
    
    # Vérifier si l'utilisateur a déjà acheté ce résumé
    existing_purchase = Purchase.objects.filter(
        user=request.user,
        summary=summary,
        status='completed'
    ).first()
    
    if existing_purchase:
        return Response({'error': 'Vous avez déjà acheté ce résumé'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    # Créer l'achat
    import uuid
    purchase = Purchase.objects.create(
        user=request.user,
        summary=summary,
        amount=summary.prix,
        payment_method=payment_method,
        status='completed',  # Directement complété pour la simulation
        transaction_id=str(uuid.uuid4()),
        completed_at=timezone.now()
    )
    
    # Ajouter des points à l'utilisateur si le profil existe
    if hasattr(request.user, 'profile'):
        user_profile = request.user.profile
        user_profile.points += 10  # 10 points par achat
        user_profile.save()
    
    return Response(PurchaseSerializer(purchase).data, status=status.HTTP_201_CREATED)


# Service Views
class ServiceListCreateView(generics.ListCreateAPIView):
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    # Remove filter backends that might interfere
    # filter_backends = [DjangoFilterBackend, OrderingFilter]
    # filterset_fields = ['type', 'currency']
    # ordering_fields = ['created_at', 'price']
    # ordering = ['-created_at']

    def perform_create(self, serializer):
        # Seuls les admins peuvent créer des services
        if not self.request.user.is_staff:
            raise permissions.PermissionDenied("Seuls les administrateurs peuvent créer des services")
        serializer.save()
    
    def get_queryset(self):
        """Return all active services"""
        return Service.objects.filter(is_active=True)
    
    def list(self, request, *args, **kwargs):
        """Simple list method without filters or pagination"""
        services = Service.objects.filter(is_active=True).order_by('-created_at')
        serializer = ServiceSerializer(services, many=True)
        return Response(serializer.data)


class ServiceDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_update(self, serializer):
        if not self.request.user.is_staff:
            raise permissions.PermissionDenied("Seuls les administrateurs peuvent modifier des services")
        serializer.save()

    def perform_destroy(self, instance):
        if not self.request.user.is_staff:
            raise permissions.PermissionDenied("Seuls les administrateurs peuvent supprimer des services")
        instance.delete()


# Abonnement Views
class AbonnementListCreateView(generics.ListCreateAPIView):
    serializer_class = AbonnementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Abonnement.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Récupérer le service pour obtenir les informations de prix
        service = serializer.validated_data['service']
        user = self.request.user
        
        # Vérifier s'il existe déjà des abonnements pour ce service (actifs ou en attente)
        existing_subscriptions = Abonnement.objects.filter(
            user=user,
            service=service,
            status__in=['active', 'pending']
        ).order_by('-date_fin')
        
        # Calculer les dates selon l'algorithme d'abonnements consécutifs
        if existing_subscriptions.exists():
            # Si des abonnements existent, le nouveau commence à la fin du dernier
            last_subscription = existing_subscriptions.first()
            date_debut = last_subscription.date_fin
            status = 'pending'  # En attente car il commence dans le futur
        else:
            # Si aucun abonnement, commence maintenant ou à la date choisie
            date_debut = serializer.validated_data.get('date_debut', timezone.now())
            status = 'active'
        
        # Calculer la date de fin basée sur la durée du service
        date_fin = date_debut + timedelta(days=service.duree_mois * 30)
        
        # Sauvegarder avec les données calculées
        serializer.save(
            user=user,
            date_debut=date_debut,
            date_fin=date_fin,
            status=status,
            auto_renew=False,
            progress=0
        )
    
    def list(self, request, *args, **kwargs):
        """Simple list method without filters or pagination"""
        abonnements = Abonnement.objects.filter(user=request.user).order_by('-created_at')
        serializer = AbonnementSerializer(abonnements, many=True)
        return Response(serializer.data)


class AbonnementDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AbonnementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Abonnement.objects.filter(user=self.request.user)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def initiate_purchase(request):
    """
    Initier un achat de résumé avec le système de paiement FlexPay
    """
    import traceback
    try:
        summary_id = request.data.get('summary_id')
        phone_number = request.data.get('phone_number')

        print(f"🚀 Début initiate_purchase — user={request.user.username}, summary_id={summary_id}, phone={phone_number}")

        if not summary_id or not phone_number:
            return Response({
                'error': 'summary_id et phone_number sont requis'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Vérifier si le résumé existe
        try:
            summary = Summary.objects.get(id=summary_id)
            print(f"✅ Résumé trouvé: {summary.titre} — prix={summary.prix} — is_free={summary.is_free}")
        except Summary.DoesNotExist:
            return Response({'error': 'Résumé non trouvé'}, status=status.HTTP_404_NOT_FOUND)

        # Un résumé gratuit ou sans prix ne nécessite pas de paiement
        if summary.is_free or summary.prix <= 0:
            return Response({
                'error': 'Ce résumé est gratuit ou son prix n\'est pas configuré. Aucun paiement requis.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Vérifier si l'utilisateur n'a pas déjà acheté ce résumé
        existing_purchase = Purchase.objects.filter(
            user=request.user,
            summary=summary,
            status='completed'
        ).first()

        if existing_purchase:
            return Response({
                'error': 'Vous avez déjà acheté ce résumé',
                'purchase_id': existing_purchase.id
            }, status=status.HTTP_400_BAD_REQUEST)

        # Déléguer au service FlexPay
        from .flexpay_integration import _process_summary_purchase
        return _process_summary_purchase(request.user, request.data, summary)

    except Exception as e:
        print(f"💥 Erreur générale dans initiate_purchase: {e}")
        print(traceback.format_exc())
        return Response({
            'error': f'Erreur serveur: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def initiate_subscription_payment_view(request):
    """
    Initier un paiement d'abonnement avec validation stricte
    """
    try:
        print(f"🚀 Début initiate_subscription_payment_view")
        print(f"📦 Données reçues: {request.data}")
        print(f"👤 Utilisateur: {request.user.username} (ID: {request.user.id})")
        
        service_id = request.data.get('service_id')
        phone_number = request.data.get('phone_number')
        payment_method = request.data.get('payment_method', 'mobile_money')
        
        print(f"🔍 service_id: {service_id}")
        print(f"📱 phone_number: {phone_number}")
        print(f"💳 payment_method: {payment_method}")
        
        if not service_id:
            print("❌ ID du service manquant")
            return Response({
                'error': 'service_id et phone_number sont requis',
                'debug': {'missing_fields': ['service_id'], 'received_data': request.data}
            }, status=status.HTTP_400_BAD_REQUEST)

        if not phone_number:
            print("❌ Numéro de téléphone manquant")
            return Response({
                'error': 'service_id et phone_number sont requis',
                'debug': {'missing_fields': ['phone_number'], 'received_data': request.data}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Vérifier si le service existe
        try:
            service = Service.objects.get(id=service_id)
            print(f"✅ Service trouvé: {service.nom} - Prix: {service.price} - Devise: {service.currency}")
        except Service.DoesNotExist:
            print(f"❌ Service non trouvé pour ID: {service_id}")
            return Response({
                'error': 'Service non trouvé',
                'debug': {'service_id': service_id, 'available_services': list(Service.objects.values_list('id', 'nom'))}
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Note: Permettre le paiement même avec abonnement actif (renouvellement ou achat supplémentaire)
        current_time = timezone.now()
        print(f"🕐 Heure actuelle: {current_time}")
        
        active_subscription = Abonnement.objects.filter(
            user=request.user,
            service=service,
            status='active',
            date_fin__gt=current_time
        ).first()
        
        if active_subscription:
            print(f"ℹ️ Abonnement actif existant: ID {active_subscription.id}, Fin: {active_subscription.date_fin} — autorisation de paiement")
        else:
            print("✅ Aucun abonnement actif trouvé, continuation du processus")
        
        # Formater le numéro de téléphone
        phone_number = str(phone_number).strip().replace("+", "").replace(" ", "")
        print(f"📱 Numéro brut: {phone_number}")
        
        # Si 9 chiffres (ex: 996816806), ajouter 0 devant
        if len(phone_number) == 9 and phone_number.isdigit():
            phone_number = f"0{phone_number}"
            print(f"📱 Numéro formaté avec 0: {phone_number}")
        
        # Si commence par 0, remplacer par 243
        if phone_number.startswith("0"):
            phone_number = f"243{phone_number[1:]}"
            print(f"📱 Numéro formaté avec 243: {phone_number}")

        print(f"📱 Numéro final formaté: {phone_number}")
        
        # Utiliser FlexPay pour initier le paiement
        try:
            print("🔄 Appel à la fonction FlexPay...")
            from .flexpay_integration import _process_subscription_payment
            return _process_subscription_payment(request.user, request.data)
        except Exception as flexpay_error:
            print(f"❌ Erreur lors de l'appel à FlexPay: {flexpay_error}")
            import traceback
            print(f"📚 Traceback FlexPay: {traceback.format_exc()}")
            
            # En cas d'erreur avec FlexPay, retourner une réponse détaillée
            return Response({
                'error': f'Erreur lors de l\'initialisation du paiement: {str(flexpay_error)}',
                'debug': {
                    'flexpay_error': str(flexpay_error),
                    'service_id': service_id,
                    'phone_number': phone_number,
                    'payment_method': payment_method,
                    'service_details': {
                        'id': service.id,
                        'nom': service.nom,
                        'prix': float(service.price),
                        'currency': service.currency
                    }
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        print(f"💥 Erreur générale dans initiate_subscription_payment_view: {e}")
        import traceback
        print(f"📚 Traceback complet: {traceback.format_exc()}")
        
        return Response({
            'error': f'Erreur serveur: {str(e)}',
            'debug': {
                'exception_type': type(e).__name__,
                'exception_message': str(e),
                'user_id': request.user.id if request.user else None,
                'received_data': request.data,
                'traceback': traceback.format_exc() if hasattr(traceback, 'format_exc') else str(e)
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_subscription_status(request):
    """
    Vérifier le statut des abonnements de l'utilisateur
    """
    try:
        current_time = timezone.now()
        subscriptions = Abonnement.objects.filter(user=request.user).order_by('-created_at')
        
        subscription_data = []
        for sub in subscriptions:
            is_active = sub.status == 'active' and sub.date_fin > current_time
            subscription_data.append({
                'id': sub.id,
                'service': sub.service.nom,
                'service_id': sub.service.id,
                'status': sub.status,
                'date_debut': sub.date_debut,
                'date_fin': sub.date_fin,
                'is_active': is_active,
                'days_remaining': (sub.date_fin - current_time).days if is_active else 0
            })
        
        return Response({
            'subscriptions': subscription_data,
            'has_active_subscription': any(sub['is_active'] for sub in subscription_data)
        })
        
    except Exception as e:
        return Response({
            'error': f'Erreur lors de la vérification: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_purchase_status(request, transaction_ref):
    """
    Vérifier le statut d'un achat via sa référence de transaction
    """
    try:
        purchase = Purchase.objects.get(
            transaction_id=transaction_ref,
            user=request.user
        )
        return Response({
            'status': purchase.status,
            'transaction_id': purchase.transaction_id,
            'summary_id': purchase.summary.id if purchase.summary else None,
        })
    except Purchase.DoesNotExist:
        return Response({'error': 'Achat non trouvé pour cette référence'},
                       status=status.HTTP_404_NOT_FOUND)
