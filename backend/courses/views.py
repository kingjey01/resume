from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.http import HttpResponse, Http404, FileResponse
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.utils.encoding import smart_str
import os
import logging
import mimetypes

logger = logging.getLogger(__name__)
from django.contrib.auth.models import User
from .models import (
    Course, Session, Summary, Universite, Promotion, Filiere,
    Service, Abonnement, Professeur, Dispense
)
from payments.models import Purchase
from .serializers import (
    CourseSerializer, SessionSerializer, SessionCreateSerializer, SummarySerializer, 
    SummaryCreateSerializer, UniversiteSerializer, PromotionSerializer, 
    FiliereSerializer, ServiceSerializer, AbonnementSerializer, 
    AbonnementCreateSerializer, FiliereWithUniversiteSerializer,
    ProfesseurSerializer
)
from .permissions import (IsOwnerOrReadOnly, CanCreateSummary, CanAccessSummary,
                         IsAdminOrReadOnly, HasUniversityAccess, CanModifyObject)


# ─── Helper : prix minimum dynamique depuis la base ──────────────────

def get_minimum_resume_price():
    """
    Retourne le prix minimum configuré dans ResumePricingConfig.
    Si aucune config active → valeur par défaut 3000.
    Cette fonction est la source unique de vérité pour le seuil de prix.
    """
    try:
        from security.models import ResumePricingConfig
        config = ResumePricingConfig.objects.get(is_active=True)
        return float(config.minimum_resume_price)
    except Exception:
        return 3000.00


class CourseListCreateView(generics.ListCreateAPIView):
    serializer_class = CourseSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['filieres', 'universites', 'promotions']
    search_fields = ['nom', 'description']
    ordering_fields = ['nom', 'created_at']
    ordering = ['-created_at']
    permission_classes = [permissions.IsAuthenticated, HasUniversityAccess]
    
    def get_queryset(self):
        """Filtrer les cours selon l'université, promotion et filière de l'utilisateur"""
        if not self.request.user.is_authenticated:
            return Course.objects.none()
        
        if not hasattr(self.request.user, 'profile'):
            return Course.objects.none()
        
        profile = self.request.user.profile
        
        # Admin voit tous les cours
        if profile.is_admin:
            return Course.objects.all()
        
        # Filtrage strict par université, promotion et filière
        if not profile.universite or not profile.promotion or not profile.filiere:
            return Course.objects.none()
        
        return Course.objects.filter(
            universites=profile.universite,
            promotions=profile.promotion,
            filieres=profile.filiere
        ).distinct()
    def perform_create(self, serializer):
        """Assigner automatiquement l'université, promotion et filière lors de la création"""
        profile = self.request.user.profile
        course = serializer.save(
            university=profile.universite.nom if profile.universite else '',
            filiere=profile.filiere.nom if profile.filiere else ''
        )
        if profile.universite:
            course.universites.add(profile.universite)
        if profile.promotion:
            course.promotions.add(profile.promotion)
        if profile.filiere:
            course.filieres.add(profile.filiere)

        # === Mode ONBOARDING uniquement : auto-créer une Dispense si un professeur existe ===
        # Le flag is_onboarding est envoyé par le frontend pendant le parcours de première connexion.
        # Depuis le menu "+" → Créer, is_onboarding est absent/false → aucune Dispense créée.
        is_onboarding = self.request.data.get('is_onboarding', False) in (True, 'true', 'True', 1, '1')
        if is_onboarding and profile.universite and profile.filiere and profile.promotion:
            professeur = Professeur.objects.filter(
                universite=profile.universite,
                filieres=profile.filiere
            ).first()
            if professeur:
                Dispense.objects.get_or_create(
                    professeur=professeur,
                    cours=course,
                    promotion=profile.promotion,
                    defaults={
                        'universite': profile.universite,
                        'filiere': profile.filiere,
                    }
                )
                logger.info(f"🔗 [Onboarding] Dispense auto-créée: Professeur={professeur.id}, Cours={course.id}")



                
class CourseDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated, HasUniversityAccess, CanModifyObject]
    
    def get_queryset(self):
        """Filtrer les cours selon l'université, promotion et filière de l'utilisateur"""
        if not self.request.user.is_authenticated:
            return Course.objects.none()
        
        if not hasattr(self.request.user, 'profile'):
            return Course.objects.none()
        
        profile = self.request.user.profile
        
        # Admin voit tous les cours
        if profile.is_admin:
            return Course.objects.all()
        
        # Filtrage strict
        if not profile.universite or not profile.promotion or not profile.filiere:
            return Course.objects.none()
        
        return Course.objects.filter(
            universites=profile.universite,
            promotions=profile.promotion,
            filieres=profile.filiere
        ).distinct()


class SessionListCreateView(generics.ListCreateAPIView):
    serializer_class = SessionSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['course']
    search_fields = ['professeur']
    ordering_fields = ['date', 'created_at']
    ordering = ['-date']
    permission_classes = [permissions.IsAuthenticated, HasUniversityAccess]
    
    def get_queryset(self):
        """Filtrer les sessions selon l'université, promotion et filière via le cours"""
        if not self.request.user.is_authenticated:
            return Session.objects.none()
        
        if not hasattr(self.request.user, 'profile'):
            return Session.objects.none()
        
        profile = self.request.user.profile
        
        if profile.is_admin:
            return Session.objects.all()
        
        if not profile.universite or not profile.promotion or not profile.filiere:
            return Session.objects.none()
        
        return Session.objects.filter(
            course__universites=profile.universite,
            course__promotions=profile.promotion,
            course__filieres=profile.filiere
        ).distinct()


class SessionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SessionSerializer
    permission_classes = [permissions.IsAuthenticated, HasUniversityAccess, CanModifyObject]
    
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Session.objects.none()
        
        if not hasattr(self.request.user, 'profile'):
            return Session.objects.none()
        
        profile = self.request.user.profile
        
        if profile.is_admin:
            return Session.objects.all()
        
        if not profile.universite or not profile.promotion or not profile.filiere:
            return Session.objects.none()
        
        return Session.objects.filter(
            course__universites=profile.universite,
            course__promotions=profile.promotion,
            course__filieres=profile.filiere
        ).distinct()


class SummaryListCreateView(generics.ListCreateAPIView):
    queryset = Summary.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['course', 'author_type', 'is_free']
    search_fields = ['titre', 'texte_resume']
    ordering_fields = ['titre', 'prix', 'created_at']
    ordering = ['-created_at']
    permission_classes = [permissions.IsAuthenticated, CanCreateSummary]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return SummaryCreateSerializer
        return SummarySerializer
    
    def get_queryset(self):
        """Filtrer les résumés selon l'université, promotion et filière via le cours"""
        if not self.request.user.is_authenticated:
            return Summary.objects.filter(is_free=True)
        
        if not hasattr(self.request.user, 'profile'):
            return Summary.objects.none()
        
        profile = self.request.user.profile
        
        # Admin voit tous les résumés
        if profile.is_admin:
            return Summary.objects.all()
        
        # CP voit les résumés de son université/promotion/filière
        # if profile.is_cp:
        #     if not profile.universite or not profile.promotion or not profile.filiere:
        #         return Summary.objects.none()
            
        #     return Summary.objects.filter(
        #         course__universites=profile.universite,
        #         course__promotions=profile.promotion,
        #         course__filieres=profile.filiere,
        #         is_validated=True
        #     ).distinct()

        # Étudiant voit uniquement les résumés validés de son université/promotion/filière
        if not profile.universite or not profile.promotion or not profile.filiere:
            return Summary.objects.none()

        return Summary.objects.filter(
            course__universites=profile.universite,
            course__promotions=profile.promotion,
            course__filieres=profile.filiere,
            is_validated=True
        ).distinct()


class SummaryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SummarySerializer
    permission_classes = [permissions.IsAuthenticated, HasUniversityAccess, CanAccessSummary]
    
    def get_queryset(self):
        """Filtrer les résumés selon l'université, promotion et filière via le cours"""
        if not self.request.user.is_authenticated:
            return Summary.objects.none()
        
        if not hasattr(self.request.user, 'profile'):
            return Summary.objects.none()
        
        profile = self.request.user.profile
        
        if profile.is_admin:
            return Summary.objects.all()
        
        if not profile.universite or not profile.promotion or not profile.filiere:
            return Summary.objects.none()
        
        return Summary.objects.filter(
            course__universites=profile.universite,
            course__promotions=profile.promotion,
            course__filieres=profile.filiere
        ).distinct()


class SummaryAchetesView(generics.ListAPIView):
    """Endpoint pour voir les résumés achetés par l'étudiant (statut completed uniquement)"""
    serializer_class = SummarySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['course', 'author_type']
    search_fields = ['titre', 'texte_resume']
    ordering_fields = ['titre', 'prix', 'created_at']
    ordering = ['-created_at']
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Retourner uniquement les résumés avec achats completed pour l'utilisateur"""
        user = self.request.user
        
        # Récupérer les IDs des résumés achetés avec statut 'completed' (exclure abonnements)
        purchased_summary_ids = Purchase.objects.filter(
            user=user,
            status='completed',
            summary__isnull=False
        ).values_list('summary_id', flat=True)
        
        # Retourner uniquement ces résumés
        return Summary.objects.filter(id__in=purchased_summary_ids)


class SummaryGratuitsView(generics.ListAPIView):
    """Endpoint pour voir tous les résumés gratuits"""
    queryset = Summary.objects.filter(is_free=True)
    serializer_class = SummarySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['course', 'author_type']
    search_fields = ['titre', 'texte_resume']
    ordering_fields = ['titre', 'created_at']
    ordering = ['-created_at']
    permission_classes = [permissions.IsAuthenticated]


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def generate_summary_from_audio(request):
    """
    Endpoint pour générer un résumé à partir d'un fichier audio
    """
    if 'audio_file' not in request.FILES:
        return Response({'error': 'Fichier audio requis'}, status=status.HTTP_400_BAD_REQUEST)
    
    audio_file = request.FILES['audio_file']
    course_id = request.data.get('course_id')
    
    if not course_id:
        return Response({'error': 'ID du cours requis'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return Response({'error': 'Cours non trouvé'}, status=status.HTTP_404_NOT_FOUND)
    
    # TODO: Intégrer ici l'API d'IA pour la transcription et génération de résumé
    # Pour l'instant, on retourne un résumé fictif
    
    # Créer une session avec le fichier audio
    session = Session.objects.create(
        course=course,
        date=request.data.get('date', '2024-01-01'),
        professeur=request.data.get('professeur', 'Professeur IA'),
        audio_file=audio_file
    )
    
    # Générer un résumé IA fictif
    summary_text = f"Résumé généré automatiquement pour le cours {course.nom}. " \
                   f"Ce résumé a été créé à partir de l'enregistrement audio de la séance."
    
    summary = Summary.objects.create(
        titre=f"Résumé IA - {course.nom}",
        texte_resume=summary_text,
        course=course,
        session=session,
        author_type='ai',
        is_free=True
    )
    
    return Response(SummarySerializer(summary).data, status=status.HTTP_201_CREATED)


# CRUD Views pour Universites
class UniversiteViewSet(viewsets.ModelViewSet):
    queryset = Universite.objects.all()
    serializer_class = UniversiteSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['nom', 'adresse']
    ordering_fields = ['nom', 'created_at']
    ordering = ['nom']
    permission_classes = [permissions.AllowAny]
    
    @action(detail=True, methods=['get'])
    def filieres(self, request, pk=None):
        """Récupère toutes les filières d'une université"""
        universite = self.get_object()
        filieres = universite.filieres.all()
        serializer = FiliereSerializer(filieres, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_filiere(self, request, pk=None):
        """Ajoute une filière à une université"""
        universite = self.get_object()
        filiere_id = request.data.get('filiere_id')
        if not filiere_id:
            return Response(
                {"error": "Le paramètre 'filiere_id' est requis"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            filiere = Filiere.objects.get(id=filiere_id)
            universite.filieres.add(filiere)
            return Response({"status": "Filière ajoutée avec succès"}, status=status.HTTP_201_CREATED)
        except Filiere.DoesNotExist:
            return Response(
                {"error": "Filière non trouvée"},
                status=status.HTTP_404_NOT_FOUND
            )


# CRUD Views pour Filieres
class FiliereViewSet(viewsets.ModelViewSet):
    queryset = Filiere.objects.all()
    serializer_class = FiliereWithUniversiteSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['nom', 'description']
    ordering_fields = ['nom', 'created_at']
    ordering = ['nom']
    permission_classes = [permissions.AllowAny]
    
    @action(detail=True, methods=['get'])
    def promotions(self, request, pk=None):
        """Récupère toutes les promotions d'une filière"""
        filiere = self.get_object()
        promotions = filiere.promotions.all()
        serializer = PromotionSerializer(promotions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_promotion(self, request, pk=None):
        """Ajoute une promotion à une filière"""
        filiere = self.get_object()
        promotion_id = request.data.get('promotion_id')
        if not promotion_id:
            return Response(
                {"error": "Le paramètre 'promotion_id' est requis"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            promotion = Promotion.objects.get(id=promotion_id)
            filiere.promotions.add(promotion)
            return Response({"status": "Promotion ajoutée avec succès"}, status=status.HTTP_201_CREATED)
        except Promotion.DoesNotExist:
            return Response(
                {"error": "Promotion non trouvée"},
                status=status.HTTP_404_NOT_FOUND
            )


# CRUD Views pour Promotions
class PromotionViewSet(viewsets.ModelViewSet):
    queryset = Promotion.objects.all()
    serializer_class = PromotionSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['nom']
    filterset_fields = ['annee']
    ordering_fields = ['nom', 'annee', 'created_at']
    ordering = ['nom']
    permission_classes = [permissions.AllowAny]
    
    @action(detail=True, methods=['get'])
    def filieres(self, request, pk=None):
        """Récupère toutes les filières associées à une promotion"""
        promotion = self.get_object()
        filieres = promotion.filieres.all()
        serializer = FiliereSerializer(filieres, many=True)
        return Response(serializer.data)


# CRUD Views pour Services
class ServiceListCreateView(generics.ListCreateAPIView):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['nom', 'description']
    ordering_fields = ['nom', 'prix', 'created_at']
    ordering = ['nom']
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """Seuls les admins peuvent créer/modifier/supprimer des services"""
        if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]


class ServiceDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """Seuls les admins peuvent modifier/supprimer des services"""
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]


# CRUD Views pour Abonnements
class AbonnementListCreateView(generics.ListCreateAPIView):
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['service', 'devise']
    search_fields = ['description', 'service__nom']
    ordering_fields = ['date_debut', 'date_fin', 'created_at']
    ordering = ['-created_at']
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Retourner seulement les abonnements de l'utilisateur connecté"""
        return Abonnement.objects.filter(etudiant=self.request.user)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AbonnementCreateSerializer
        return AbonnementSerializer


class AbonnementDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AbonnementSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Retourner seulement les abonnements de l'utilisateur connecté"""
        return Abonnement.objects.filter(etudiant=self.request.user)



@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, CanCreateSummary])
def upload_audio_session(request):
    """
    Upload d'un enregistrement audio - Stockage uniquement (pas de transcription)
    Sauvegarde le fichier audio et crée une session avec statut EN_ATTENTE.
    La transcription et le résumé seront déclenchés manuellement via process_audio_session.
    """
    try:
        # Récupérer les données
        course_id = request.data.get('course_id')
        professeur_id = request.data.get('professeur_id')
        summary_title = request.data.get('summary_title', '')
        summary_price = request.data.get('summary_price', '0')
        client_audio_duration = request.data.get('audio_duration', '0')
        audio_file = request.FILES.get('audio_file')
        
        if not course_id:
            return Response(
                {'error': 'course_id est requis'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not summary_title:
            return Response(
                {'error': 'summary_title (titre du résumé) est requis'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Valider le prix via la config dynamique
        try:
            price = float(summary_price)
            if price < 0:
                raise ValueError("Le prix ne peut pas être négatif")
            min_price = get_minimum_resume_price()
            if price < min_price:
                return Response({
                    'error': f'Le prix minimum autorisé pour un résumé est de {int(min_price)} FC.'
                }, status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, TypeError):
            return Response(
                {'error': 'summary_price doit être un nombre valide >= 0'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not audio_file:
            return Response(
                {'error': 'Fichier audio requis'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Vérifier que le cours existe
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response(
                {'error': 'Cours introuvable'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Créer la session avec l'enregistrement (statut = pending / EN_ATTENTE)
        from django.utils import timezone
        
        # Auto-résoudre le professeur via Dispense si non fourni (Objectif 7)
        professeur_nom = request.data.get('professeur_nom', '')
        resolved_professeur_fk = professeur_id
        resolved_professeur_text = professeur_nom
        
        if not professeur_id:
            profile = request.user.profile
            if profile.universite and profile.filiere and profile.promotion:
                dispense = Dispense.objects.filter(
                    cours=course,
                    universite=profile.universite,
                    filiere=profile.filiere,
                    promotion=profile.promotion
                ).select_related('professeur__user').first()
                if dispense:
                    resolved_professeur_fk = dispense.professeur.id
                    resolved_professeur_text = (
                        dispense.professeur.user.get_full_name()
                        or dispense.professeur.user.username
                    )
                    logger.info(f"🎓 Professeur auto-résolu via Dispense: {resolved_professeur_text}")
        
        session_data = {
            'course': course.id,
            'date': timezone.now(),
            'professeur': resolved_professeur_text if resolved_professeur_text else '',
            'audio_file': audio_file
        }
        if resolved_professeur_fk:
            session_data['professeur_fk'] = resolved_professeur_fk
        
        serializer = SessionCreateSerializer(data=session_data, context={'request': request})
        if serializer.is_valid():
            session = serializer.save()
            
            # ========================================
            # Calculer la durée réelle de l'audio
            # ========================================
            MAX_AUDIO_DURATION_SECONDS = 10800  # 3 heures
            
            # 1) Durée envoyée par le client (enregistrement ou file picker)
            client_duration_value = 0.0
            try:
                client_duration_value = float(client_audio_duration)
            except (ValueError, TypeError):
                pass

            logger.info(
                f"🎵 [Upload] Durée client: brute='{client_audio_duration}', "
                f"convertie={client_duration_value:.2f}s ({client_duration_value/60:.2f}min)"
            )

            # 2) Lire la durée via mutagen (source la plus fiable)
            server_duration_value = 0.0
            try:
                if session.audio_file and hasattr(session.audio_file, 'path'):
                    import os
                    file_path = session.audio_file.path
                    if os.path.exists(file_path):
                        from mutagen import File as MutagenFile
                        audio_info = MutagenFile(file_path)
                        if audio_info and audio_info.info:
                            server_duration_value = float(audio_info.info.length)
                            logger.info(
                                f"🎵 [Upload] Durée serveur (mutagen): "
                                f"{server_duration_value:.2f}s ({server_duration_value/60:.2f}min)"
                            )
            except Exception as e:
                logger.warning(f"⚠️ Impossible de lire la durée audio via mutagen: {e}")

            # 3) Priorité: mutagen > client
            if server_duration_value > 0:
                audio_duration = server_duration_value
                duration_source = 'mutagen'
            elif client_duration_value > 0:
                audio_duration = client_duration_value
                duration_source = 'client'
            else:
                audio_duration = 0.0
                duration_source = 'inconnu'
            
            logger.info(
                f"🎵 [Upload] Session {session.id} - Durée finale: {audio_duration:.2f}s "
                f"({audio_duration/60:.2f}min) [source: {duration_source}] "
                f"| Limite: {MAX_AUDIO_DURATION_SECONDS}s ({MAX_AUDIO_DURATION_SECONDS//60}min)"
            )
            
            # 4) Validation immédiate de la durée (rejet avant Celery si > limite)
            if audio_duration > MAX_AUDIO_DURATION_SECONDS:
                logger.warning(
                    f"⚠️ [Upload] Session {session.id} rejetée: "
                    f"{audio_duration:.2f}s > {MAX_AUDIO_DURATION_SECONDS}s"
                )
                session.audio_duration = audio_duration
                session.processing_status = 'failed'
                session.error_message = (
                    f'Durée audio trop longue: {int(audio_duration//3600)}h{int((audio_duration%3600)//60):02d}m '
                    f'({int(audio_duration//60)} minutes / {int(audio_duration)}s). '
                    f'Maximum autorisé: 3 heures (180 minutes). [source: {duration_source}]'
                )
                session.save()
                return Response({
                    'success': False,
                    'error': session.error_message
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Sauvegarder le titre, le prix et la durée sur la session
            session.summary_title = summary_title
            session.summary_price = price
            session.audio_duration = audio_duration
            session.processing_status = 'pending'
            session.save()
            
            logger.info(
                f"✅ Session {session.id} créée avec statut EN_ATTENTE | "
                f"audio_duration={session.audio_duration}s ({session.audio_duration/60:.2f}min) "
                f"[source: {duration_source}]"
            )
            
            # 🚀 Lancer la transcription via Celery APRÈS commit de la transaction
            # Ceci évite la race condition où Celery lit audio_duration=0 (valeur par défaut)
            # avant que la durée réelle ne soit sauvegardée en base
            from django.db import transaction
            session_id_for_celery = session.id
            user_id_for_celery = request.user.id
            
            def trigger_celery_task():
                try:
                    from .tasks import process_audio_session_task
                    process_audio_session_task.delay(session_id_for_celery, user_id_for_celery)
                    logger.info(f"🚀 Tâche Celery lancée pour session {session_id_for_celery} (après commit)")
                except Exception as celery_err:
                    logger.warning(f"⚠️ Celery indisponible, traitement manuel requis: {celery_err}")
            
            transaction.on_commit(trigger_celery_task)
            
            return Response({
                'success': True,
                'message': 'Session audio enregistrée avec succès. La transcription et le résumé sont en cours de génération automatiquement.',
                'session': {
                    'id': session.id,
                    'course_name': session.course.nom,
                    'date': session.date,
                    'professeur': session.professeur,
                    'processing_status': session.processing_status,
                    'audio_duration': session.audio_duration,
                    'audio_duration_formatted': session.audio_duration_formatted,
                    'audio_file': session.audio_file.url if session.audio_file else None
                }
            }, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de l\'upload: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_audio_sessions(request):
    """
    🔥 AMÉLIORÉ: Récupère les sessions audio avec informations détaillées
    """
    try:
        # Récupérer les sessions avec fichiers audio
        sessions = Session.objects.filter(
            audio_file__isnull=False
        ).select_related('course').prefetch_related('summaries').order_by('-created_at')
        
        # Enrichir les données avec les informations audio
        from .audio_processing import audio_processor
        
        sessions_data = []
        for session in sessions:
            # Sérialiser la session de base
            session_serializer = SessionSerializer(session, context={'request': request})
            session_data = session_serializer.data
            
            # Ajouter les informations audio détaillées
            audio_info = audio_processor.get_audio_info(session.id)
            session_data['audio_info'] = audio_info
            
            # Ajouter les résumés liés à cette session
            related_summaries = session.summaries.all()
            session_data['related_summaries'] = [
                {
                    'id': summary.id,
                    'titre': summary.titre,
                    'author_type': summary.author_type,
                    'is_ai_generated': summary.author_type == 'ai',
                    'created_at': summary.created_at
                }
                for summary in related_summaries
            ]
            
            sessions_data.append(session_data)
        
        return Response({
            'success': True,
            'count': len(sessions_data),
            'sessions': sessions_data
        })
        
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la récupération: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def process_audio_session(request, session_id):
    """
    🔥 NOUVEAU: Traite manuellement une session audio pour générer un résumé
    Gère les statuts de traitement et permet de relancer les sessions en échec
    Filtré par université/promotion/filière de l'utilisateur
    """
    from django.utils import timezone
    
    try:
        profile = request.user.profile
        
        # Filtrage strict par université/promotion/filière via le cours
        if profile.is_admin:
            session = Session.objects.get(id=session_id)
        else:
            session = Session.objects.filter(
                id=session_id,
                course__universites=profile.universite,
                course__promotions=profile.promotion,
                course__filieres=profile.filiere
            ).distinct().get()
        # Vérifier la durée de l'audio (max 3 heures = 10800 secondes)
        MAX_AUDIO_DURATION_SECONDS = 10800
        raw_duration = session.audio_duration or 0
        duration_seconds = float(raw_duration)
        duration_minutes = duration_seconds / 60.0
        logger.info(
            f"🎵 [Process] Session {session_id} - durée brute: {raw_duration}, "
            f"secondes: {duration_seconds:.2f}s, minutes: {duration_minutes:.2f}min, "
            f"limite: {MAX_AUDIO_DURATION_SECONDS}s ({MAX_AUDIO_DURATION_SECONDS // 60}min)"
        )

        if duration_seconds > MAX_AUDIO_DURATION_SECONDS:
            session.processing_status = 'failed'
            session.error_message = (
                f'Durée audio trop longue: {int(duration_seconds//3600)}h{int((duration_seconds%3600)//60):02d}m '
                f'({duration_minutes:.1f} minutes / {duration_seconds:.0f}s). '
                f'Maximum autorisé: 3 heures (180 minutes).'
            )
            session.save()
            logger.warning(
                f"⚠️ [Process] Session {session_id} rejetée: "
                f"{duration_seconds:.2f}s > {MAX_AUDIO_DURATION_SECONDS}s"
            )
            return Response({
                'success': False,
                'error': session.error_message
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Mettre à jour le statut en "pending"
        session.processing_status = 'pending'
        session.submitted_at = timezone.now()
        session.error_message = None
        session.save()
        
        logger.info(
            f"🎵 [Process] Session {session_id} lancée en arrière-plan | "
            f"audio_duration={duration_seconds:.2f}s ({duration_minutes:.1f}min)"
        )
        
        # 🚀 Lancer via Celery en arrière-plan (APRÈS commit)
        from django.db import transaction
        session_id_for_celery = session.id
        user_id_for_celery = request.user.id
        
        def trigger_celery_process():
            try:
                from .tasks import process_audio_session_task
                process_audio_session_task.delay(session_id_for_celery, user_id_for_celery)
                logger.info(f"🚀 [Process] Tâche Celery lancée pour session {session_id_for_celery}")
            except Exception as celery_err:
                logger.warning(f"⚠️ [Process] Celery indisponible: {celery_err}")
        
        transaction.on_commit(trigger_celery_process)
        
        return Response({
            'success': True,
            'message': 'Traitement lancé en arrière-plan. La transcription et le résumé seront générés automatiquement.',
            'session_id': session.id,
            'processing_status': 'pending'
        })
            
    except Session.DoesNotExist:
        return Response(
            {'error': 'Session non trouvée'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        # En cas d'erreur, mettre à jour le statut
        try:
            session = Session.objects.get(id=session_id)
            session.processing_status = 'failed'
            session.error_message = f'Erreur serveur: {str(e)}'
            session.save()
        except:
            pass
        
        return Response(
            {'error': f'Erreur lors du traitement: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def retry_failed_session(request, session_id):
    """
    🔥 Relance le traitement d'une session en échec via Celery (arrière-plan).
    Le traitement est asynchrone pour éviter le timeout HTTP sur les longs audios.
    Filtré par université/promotion/filière de l'utilisateur.
    """
    from django.utils import timezone
    from django.db import transaction
    
    try:
        profile = request.user.profile
        
        # Filtrage strict par université/promotion/filière via le cours
        if profile.is_admin:
            session = Session.objects.get(id=session_id)
        else:
            session = Session.objects.filter(
                id=session_id,
                course__universites=profile.universite,
                course__promotions=profile.promotion,
                course__filieres=profile.filiere
            ).distinct().get()

        # Vérifier que la session est en échec ou en statut intermédiaire (transcrit mais résumé échoué)
        if session.processing_status not in ('failed', 'transcribed'):
            return Response({
                'success': False,
                'error': f'Cette session n\'est pas en échec (statut actuel: {session.processing_status})'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        previous_status = session.processing_status
        
        # 🔧 Corriger la durée si elle semble incorrecte (0 ou non définie)
        # Ceci répare les sessions uploadées avec l'ancien code qui avait un bug de durée
        import os
        duration_fixed = False
        if session.audio_file and (not session.audio_duration or session.audio_duration <= 0):
            try:
                file_path = session.audio_file.path if hasattr(session.audio_file, 'path') else None
                if file_path and os.path.exists(file_path):
                    from mutagen import File as MutagenFile
                    audio_info = MutagenFile(file_path)
                    if audio_info and audio_info.info:
                        session.audio_duration = float(audio_info.info.length)
                        duration_fixed = True
                        logger.info(
                            f"🔧 [Retry] Durée corrigée via mutagen: {session.audio_duration:.2f}s "
                            f"({session.audio_duration/60:.1f}min)"
                        )
            except Exception as e:
                logger.warning(f"⚠️ [Retry] Impossible de re-lire la durée: {e}")
        
        # Réinitialiser le statut pour relancer
        session.processing_status = 'pending'
        session.error_message = None
        session.submitted_at = timezone.now()
        session.save()
        
        logger.info(
            f"🔄 [Retry] Session {session_id} réinitialisée (était: {previous_status}) | "
            f"audio_duration={session.audio_duration}s ({session.audio_duration/60:.1f}min)"
            f"{' [durée corrigée]' if duration_fixed else ''}"
        )
        
        # 🚀 Lancer via Celery en arrière-plan (APRÈS commit)
        # Si la transcription existait déjà → relancer juste le résumé
        # Sinon → relancer tout le pipeline
        session_id_for_celery = session.id
        user_id_for_celery = request.user.id
        was_transcribed = previous_status == 'transcribed'
        
        def trigger_celery_retry():
            try:
                if was_transcribed:
                    # Transcription déjà OK → relancer uniquement le résumé
                    from .tasks import generate_summary_task
                    generate_summary_task.delay(session_id_for_celery, user_id_for_celery)
                    logger.info(f"🚀 [Retry] Tâche résumé seul lancée pour session {session_id_for_celery}")
                else:
                    # Échec complet → relancer tout le pipeline
                    from .tasks import process_audio_session_task
                    process_audio_session_task.delay(session_id_for_celery, user_id_for_celery)
                    logger.info(f"🚀 [Retry] Tâche complète lancée pour session {session_id_for_celery}")
            except Exception as celery_err:
                logger.warning(f"⚠️ [Retry] Celery indisponible: {celery_err}")
        
        transaction.on_commit(trigger_celery_retry)
        
        retry_type = 'résumé uniquement' if was_transcribed else 'transcription + résumé'
        return Response({
            'success': True,
            'message': f'Session relancée en arrière-plan ({retry_type}). Le traitement est en cours.',
            'session_id': session.id,
            'processing_status': 'pending',
            'retry_type': 'summary_only' if was_transcribed else 'full'
        })
            
    except Session.DoesNotExist:
        return Response(
            {'error': 'Session non trouvée'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        try:
            session = Session.objects.get(id=session_id)
            session.processing_status = 'failed'
            session.error_message = f'Erreur lors de la relance: {str(e)}'
            session.save()
        except:
            pass
        
        return Response(
            {'error': f'Erreur lors de la relance: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_sessions_queue(request):
    """
    🔥 NOUVEAU: Récupère la file d'attente des sessions avec leurs statuts
    Filtré par université/promotion/filière de l'utilisateur
    """
    try:
        profile = request.user.profile
        
        # Filtrage strict par université/promotion/filière via le cours
        base_queryset = Session.objects.filter(
            audio_file__isnull=False,
            course__universites=profile.universite,
            course__promotions=profile.promotion,
            course__filieres=profile.filiere
        ).exclude(audio_file='').distinct()
        
        # Admin peut voir toutes les sessions
        if profile.is_admin:
            base_queryset = Session.objects.filter(audio_file__isnull=False).exclude(audio_file='')
        
        # Filtrer par statut si spécifié
        status_filter = request.query_params.get('status', None)
        
        queryset = base_queryset
        
        if status_filter:
            queryset = queryset.filter(processing_status=status_filter)
        
        # Ordonner par date de création décroissante
        queryset = queryset.order_by('-created_at')
        
        from .serializers import SessionSerializer
        serializer = SessionSerializer(queryset, many=True)
        
        # Statistiques (filtrées aussi)
        stats = {
            'total': base_queryset.count(),
            'pending': base_queryset.filter(processing_status='pending').count(),
            'processing': base_queryset.filter(processing_status='processing').count(),
            'transcribed': base_queryset.filter(processing_status='transcribed').count(),
            'summarized': base_queryset.filter(processing_status='summarized').count(),
            'failed': base_queryset.filter(processing_status='failed').count(),
        }
        
        return Response({
            'success': True,
            'sessions': serializer.data,
            'stats': stats
        })
        
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la récupération: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_audio_file(request, session_id):
    """
    🔥 AMÉLIORÉ: Sert le fichier audio pour lecture dans l'app
    Filtré par université/promotion/filière de l'utilisateur
    """
    try:
        profile = request.user.profile
        
        # Filtrage strict par université/promotion/filière via le cours
        if profile.is_admin:
            session = Session.objects.get(id=session_id)
        else:
            session = Session.objects.filter(
                id=session_id,
                course__universites=profile.universite,
                course__promotions=profile.promotion,
                course__filieres=profile.filiere
            ).distinct().get()
        if not session.audio_file:
            return Response(
                {'error': 'Aucun fichier audio pour cette session'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Vérifier si le fichier existe physiquement
        file_exists = False
        file_size = 0
        try:
            if hasattr(session.audio_file, 'path'):
                file_exists = os.path.exists(session.audio_file.path)
                if file_exists:
                    file_size = os.path.getsize(session.audio_file.path)
            elif hasattr(session.audio_file, 'size'):
                file_size = session.audio_file.size
                file_exists = file_size > 0
        except:
            pass
        
        # Construire l'URL absolue
        audio_url = request.build_absolute_uri(session.audio_file.url)
        
        # Retourner les informations complètes
        return Response({
            'success': True,
            'audio_url': audio_url,
            'direct_url': session.audio_file.url,
            'file_info': {
                'name': session.audio_file.name,
                'size': file_size,
                'size_mb': round(file_size / (1024 * 1024), 2) if file_size else 0,
                'exists': file_exists,
                'course': session.course.nom,
                'professor': session.professeur,
                'date': session.date,
                'session_id': session_id
            },
            'playback_info': {
                'mime_type': mimetypes.guess_type(session.audio_file.name)[0] or 'audio/wav',
                'supports_streaming': True,
                'cors_enabled': True
            }
        })
        
    except Session.DoesNotExist:
        return Response(
            {'error': 'Session non trouvée'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Erreur: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def serve_audio_file(request, session_id):
    """
    🔥 NOUVEAU: Sert directement le fichier audio (sans authentification pour les tests)
    """
    try:
        session = Session.objects.get(id=session_id)
        
        if not session.audio_file:
            raise Http404("Fichier audio non trouvé")
        
        # Servir le fichier directement
        try:
            if hasattr(session.audio_file, 'path') and os.path.exists(session.audio_file.path):
                response = FileResponse(
                    open(session.audio_file.path, 'rb'),
                    content_type=mimetypes.guess_type(session.audio_file.name)[0] or 'audio/wav'
                )
                response['Content-Disposition'] = f'inline; filename="{os.path.basename(session.audio_file.name)}"'
                response['Accept-Ranges'] = 'bytes'
                response['Access-Control-Allow-Origin'] = '*'
                return response
            else:
                raise Http404("Fichier physique non trouvé")
                
        except Exception as e:
            return HttpResponse(
                f"Erreur lors de la lecture du fichier: {str(e)}", 
                status=500
            )
        
    except Session.DoesNotExist:
        raise Http404("Session non trouvée")
    except Exception as e:
        return HttpResponse(f"Erreur: {str(e)}", status=500)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_audio_processing_stats(request):
    """
    🔥 NOUVEAU: Statistiques de traitement audio
    """
    try:
        from .audio_processing import audio_processor
        stats = audio_processor.get_processing_stats()
        
        return Response({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la récupération des statistiques: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def batch_process_audio_sessions(request):
    """
    🔥 NOUVEAU: Traite plusieurs sessions audio en lot
    """
    try:
        session_ids = request.data.get('session_ids', [])
        
        if not session_ids:
            return Response(
                {'error': 'Aucun ID de session fourni'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from .audio_processing import audio_processor
        results = audio_processor.batch_process_sessions(session_ids)
        
        return Response({
            'success': True,
            'processed_count': len(results),
            'results': results
        })
        
    except Exception as e:
        return Response(
            {'error': f'Erreur lors du traitement en lot: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def auto_process_pending_sessions(request):
    """
    🔥 NOUVEAU: Traite automatiquement toutes les sessions en attente
    """
    try:
        from .audio_processing import audio_processor
        result = audio_processor.auto_process_pending_sessions()
        
        if result['success']:
            return Response({
                'success': True,
                'message': f'{result["processed_count"]} sessions traitées automatiquement',
                'processed_count': result['processed_count'],
                'results': result['results']
            })
        else:
            return Response(
                {'error': result['error']}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    except Exception as e:
        return Response(
            {'error': f'Erreur lors du traitement automatique: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def cleanup_old_audio_files(request):
    """
    🔥 NOUVEAU: Nettoie les anciens fichiers audio
    """
    try:
        days_old = request.data.get('days_old', 30)
        
        from .audio_processing import audio_processor
        result = audio_processor.cleanup_old_audio_files(days_old)
        
        if result['success']:
            return Response({
                'success': True,
                'message': result['message'],
                'cleaned_count': result['cleaned_count']
            })
        else:
            return Response(
                {'error': result['error']}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    except Exception as e:
        return Response(
            {'error': f'Erreur lors du nettoyage: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class ProfesseurListView(generics.ListAPIView):
    """
    🔥 NOUVEAU: Endpoint pour lister les professeurs actifs
    Filtrage par université et filière de l'utilisateur connecté
    """
    serializer_class = ProfesseurSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['universite', 'filieres', 'is_active']
    search_fields = ['user__first_name', 'user__last_name', 'specialite']
    ordering_fields = ['user__last_name', 'created_at']
    ordering = ['user__last_name']
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filtrer les professeurs par université/filière de l'utilisateur"""
        try:
            user = self.request.user
            queryset = Professeur.objects.filter(is_active=True)

            if not (hasattr(user, 'profile') and user.profile):
                logger.info("🔍 Aucun profil trouvé, retour de liste vide")
                return Professeur.objects.none()

            profile = user.profile

            # Filtrer par université
            if profile.universite:
                queryset = queryset.filter(universite=profile.universite)
                logger.info(f"🔍 Professeurs filtrés par université: {profile.universite}")
            else:
                logger.info("🔍 Aucune université dans le profil, retour de liste vide")
                return Professeur.objects.none()

            # Filtrer par filière si disponible
            if profile.filiere:
                queryset = queryset.filter(filieres=profile.filiere)
                logger.info(f"🔍 Professeurs filtrés par filière: {profile.filiere}")

            return queryset.select_related('user', 'universite').prefetch_related('filieres').distinct()
        except Exception as e:
            logger.error(f"❌ Erreur dans ProfesseurListView.get_queryset: {e}")
            return Professeur.objects.none()


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def validate_summary_view(request, summary_id):
    """
    Valide ou invalide un résumé (accessible uniquement aux CP et Admin)
    """
    try:
        # Vérifier les permissions
        if not hasattr(request.user, 'profile') or not request.user.profile.can_create_summary():
            return Response({
                'error': 'Permission refusée. Seuls les CP et Admin peuvent valider les résumés.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        summary = get_object_or_404(Summary, id=summary_id)
        is_validated = request.data.get('is_validated', False)
        
        # Mettre à jour le statut de validation
        was_validated = summary.is_validated
        summary.is_validated = is_validated
        summary.save()
        
        action = "validé" if is_validated else "invalidé"
        logger.info(f"Résumé {summary_id} {action} par {request.user.username}")

        # Envoyer une notification push aux étudiants ciblés lors de la validation
        if is_validated and not was_validated:
            try:
                from notifications.tasks import create_and_send_notification
                course = summary.course
                create_and_send_notification.apply_async(kwargs={
                    'title': '📚 Nouveau résumé disponible',
                    'body': f'Le résumé « {summary.titre} » du cours {course.nom} est maintenant disponible.',
                    'notification_type': 'summary_validated',
                    'universite_id': course.universites.values_list('id', flat=True).first(),
                    'filiere_id': course.filieres.values_list('id', flat=True).first(),
                    'promotion_id': course.promotions.values_list('id', flat=True).first(),
                    'summary_id': summary.id,
                    'course_id': course.id,
                }, countdown=3)
                logger.info(f"🔔 Notification planifiée pour le résumé {summary_id}")
            except Exception as notif_err:
                logger.warning(f"⚠️ Notification non envoyée (non bloquant): {notif_err}")
        
        return Response({
            'message': f'Résumé {action} avec succès',
            'summary_id': summary.id,
            'is_validated': summary.is_validated,
            'title': summary.titre
        }, status=status.HTTP_200_OK)
        
    except Summary.DoesNotExist:
        return Response({
            'error': 'Résumé introuvable'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Erreur validation résumé: {str(e)}")
        return Response({
            'error': 'Erreur interne du serveur'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def edit_summary_view(request, summary_id):
    """
    Modifie un résumé (accessible uniquement aux CP et Admin)
    """
    try:
        # Vérifier les permissions
        if not hasattr(request.user, 'profile') or not request.user.profile.can_create_summary():
            return Response({
                'error': 'Permission refusée. Seuls les CP et Admin peuvent modifier les résumés.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        summary = get_object_or_404(Summary, id=summary_id)
        
        # Mettre à jour les champs modifiables
        if 'titre' in request.data:
            summary.titre = request.data['titre']
        
        if 'texte_resume' in request.data:
            summary.texte_resume = request.data['texte_resume']
        
        if 'prix' in request.data:
            try:
                price = float(request.data['prix'])
                if price < 0:
                    return Response({
                        'error': 'Le prix ne peut pas être négatif'
                    }, status=status.HTTP_400_BAD_REQUEST)
                min_price = get_minimum_resume_price()
                if price < min_price:
                    return Response({
                        'error': f'Le prix minimum autorisé pour un résumé est de {int(min_price)} FC.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                summary.prix = price
            except (ValueError, TypeError):
                return Response({
                    'error': 'Le prix doit être un nombre valide'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Aucun résumé ne peut être gratuit - forcer is_free à False
        summary.is_free = False
        
        # Si c'est une modification manuelle par un CP, marquer comme validé
        if summary.author_type == 'cp':
            summary.is_validated = True
        
        summary.save()
        
        logger.info(f"Résumé {summary_id} modifié par {request.user.username}")
        
        return Response({
            'message': 'Résumé modifié avec succès',
            'summary': {
                'id': summary.id,
                'titre': summary.titre,
                'texte_resume': summary.texte_resume,
                'prix': float(summary.prix),
                'is_free': summary.is_free,
                'is_validated': summary.is_validated,
                'author_type': summary.author_type
            }
        }, status=status.HTTP_200_OK)
        
    except Summary.DoesNotExist:
        return Response({
            'error': 'Résumé introuvable'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Erreur modification résumé: {str(e)}")
        return Response({
            'error': 'Erreur interne du serveur'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_summaries_for_validation_view(request):
    """
    Récupère la liste des résumés à valider (pour les CP et Admin)
    """
    try:
        # Vérifier les permissions
        if not hasattr(request.user, 'profile') or not request.user.profile.can_create_summary():
            return Response({
                'error': 'Permission refusée. Seuls les CP et Admin peuvent accéder à cette fonctionnalité.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Récupérer les paramètres de recherche
        search_query = request.query_params.get('search', '').strip()
        
        # Récupérer les résumés: CP voit les résumés de sa université/filière/promotion, ADMIN voit tout
        summaries = Summary.objects.select_related('course', 'author_user', 'professeur', 'professeur__user').all().order_by('-created_at')
        
        profile = request.user.profile
        groupe = profile.groupe.upper() if hasattr(request.user, 'profile') else ''
        
        from django.db.models import Q
        
        if groupe == 'CP':
            summaries = summaries.filter(
                Q(author_user=request.user) |
                Q(
                    course__universites=profile.universite,
                    course__promotions=profile.promotion,
                    course__filieres=profile.filiere
                )
            ).distinct()
            
        # Appliquer la recherche si présente
        if search_query:
            summaries = summaries.filter(
                Q(titre__icontains=search_query) |
                Q(course__nom__icontains=search_query) |
                Q(professeur__user__first_name__icontains=search_query) |
                Q(professeur__user__last_name__icontains=search_query) |
                Q(professeur__specialite__icontains=search_query)
            ).distinct()
        
        summaries_data = []
        for summary in summaries:
            summaries_data.append({
                'id': summary.id,
                'titre': summary.titre,
                'texte_resume': summary.texte_resume,
                'course_name': summary.course.nom,
                'author_type': summary.author_type,
                'author_name': summary.author_user.get_full_name() if summary.author_user else 'Inconnu',
                'is_validated': summary.is_validated,
                'created_at': summary.created_at.isoformat(),
                'updated_at': summary.updated_at.isoformat(),
                'prix': float(summary.prix),
                'is_free': summary.is_free
            })
        
        return Response({
            'summaries': summaries_data,
            'total_count': len(summaries_data),
            'validated_count': sum(1 for s in summaries_data if s['is_validated']),
            'pending_count': sum(1 for s in summaries_data if not s['is_validated'])
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur récupération résumés validation: {str(e)}")
        return Response({
            'error': 'Erreur interne du serveur'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================
# ONBOARDING — Parcours de première utilisation (Objectif 1)
# ============================================================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def onboarding_status_view(request):
    """
    Vérifie si l'utilisateur CP a déjà des données.
    Retourne les étapes complétées pour le parcours de première utilisation.
    """
    try:
        user = request.user
        if not hasattr(user, 'profile'):
            return Response({'error': 'Profil non trouvé'}, status=404)

        profile = user.profile

        has_professeur = Professeur.objects.filter(
            universite=profile.universite
        ).exists() if profile.universite else False

        has_course = Course.objects.filter(
            universites=profile.universite,
            filieres=profile.filiere,
            promotions=profile.promotion
        ).exists() if (profile.universite and profile.filiere and profile.promotion) else False

        has_session = Session.objects.filter(
            course__universites=profile.universite,
            course__filieres=profile.filiere,
            course__promotions=profile.promotion
        ).exists() if (profile.universite and profile.filiere and profile.promotion) else False

        has_summary = Summary.objects.filter(
            course__universites=profile.universite,
            course__filieres=profile.filiere,
            course__promotions=profile.promotion
        ).exists() if (profile.universite and profile.filiere and profile.promotion) else False

        all_completed = has_professeur and has_course and has_session and has_summary

        return Response({
            'is_first_use': not (has_professeur or has_course or has_session or has_summary),
            'steps': {
                'has_professeur': has_professeur,
                'has_course': has_course,
                'has_session': has_session,
                'has_summary': has_summary,
            },
            'all_completed': all_completed,
            'groupe': profile.groupe,
        })

    except Exception as e:
        logger.error(f"Erreur onboarding_status: {e}")
        return Response({'error': str(e)}, status=500)


# ============================================================
# PROFESSEUR — Création simplifiée (Objectif 2)
# ============================================================

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_professeur_simple_view(request):
    """
    Création simplifiée d'un professeur.

    Deux modes de fonctionnement :
    - Mode ONBOARDING (is_onboarding=True) : crée automatiquement une Dispense
      si un cours existe déjà. Utilisé pendant le parcours de première connexion.
    - Mode GESTION (is_onboarding=False ou absent) : crée UNIQUEMENT le professeur.
      Aucune association Dispense créée. Utilisé depuis le menu "+" → Créer.

    L'utilisateur renseigne uniquement : nom_complet, telephone, specialite.
    Le backend crée automatiquement le User Django et le Professeur,
    en associant l'université de l'utilisateur connecté.
    """
    try:
        user = request.user
        if not hasattr(user, 'profile') or not user.profile.universite:
            return Response({
                'error': 'Votre profil ne contient pas d\'université. Contactez un administrateur.'
            }, status=400)

        profile = user.profile
        nom_complet = request.data.get('nom_complet', '').strip()
        telephone = request.data.get('telephone', '').strip()
        specialite = request.data.get('specialite', '').strip()
        is_onboarding = request.data.get('is_onboarding', False) in (True, 'true', 'True', 1, '1')

        if not nom_complet:
            return Response({'error': 'Le nom complet est requis.'}, status=400)

        import re
        base_username = re.sub(r'[^a-zA-Z0-9]', '', nom_complet.lower())[:20]
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        prof_user = User.objects.create(
            username=username,
            first_name=nom_complet.split()[0] if ' ' in nom_complet else nom_complet,
            last_name=' '.join(nom_complet.split()[1:]) if ' ' in nom_complet else '',
            email=f"{username}@resumeplus.local",
            is_active=True,
        )
        prof_user.set_password(User.objects.make_random_password())
        prof_user.save()

        from users.models import UserProfile
        UserProfile.objects.get_or_create(
            user=prof_user,
            defaults={
                'groupe': 'Prof',
                'phone': telephone,
                'universite': profile.universite,
                'filiere': profile.filiere,
                'promotion': profile.promotion,
            }
        )

        professeur = Professeur.objects.create(
            user=prof_user,
            telephone=telephone,
            specialite=specialite,
            universite=profile.universite,
        )

        if profile.filiere:
            professeur.filieres.add(profile.filiere)

        # === Mode ONBOARDING : auto-créer une Dispense si un cours existe déjà ===
        if is_onboarding and profile.universite and profile.filiere and profile.promotion:
            cours = Course.objects.filter(
                universites=profile.universite,
                filieres=profile.filiere,
                promotions=profile.promotion
            ).first()
            if cours:
                Dispense.objects.get_or_create(
                    professeur=professeur,
                    cours=cours,
                    promotion=profile.promotion,
                    defaults={
                        'universite': profile.universite,
                        'filiere': profile.filiere,
                    }
                )
                logger.info(f"🔗 [Onboarding] Dispense auto-créée: Professeur={professeur.id}, Cours={cours.id}")

        serializer = ProfesseurSerializer(professeur)
        return Response({
            'message': 'Professeur créé avec succès.',
            'professeur': serializer.data,
        }, status=201)

    except Exception as e:
        logger.error(f"Erreur création professeur simplifié: {e}")
        return Response({'error': str(e)}, status=500)




# ============================================================
# DISPENSE — Création automatique (Objectif 5)
# ============================================================

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_dispense_view(request):
    """
    Crée une dispense (liaison professeur-cours).
    Utilisé après la création du premier professeur et du premier cours.
    """
    try:
        user = request.user
        if not hasattr(user, 'profile'):
            return Response({'error': 'Profil non trouvé'}, status=404)

        profile = user.profile
        professeur_id = request.data.get('professeur_id')
        cours_id = request.data.get('cours_id')

        if not professeur_id or not cours_id:
            return Response({'error': 'professeur_id et cours_id sont requis.'}, status=400)

        professeur = get_object_or_404(Professeur, id=professeur_id)
        cours = get_object_or_404(Course, id=cours_id)

        if not profile.universite or not profile.filiere or not profile.promotion:
            return Response({'error': 'Profil incomplet (université/filière/promotion).'}, status=400)

        dispense, created = Dispense.objects.get_or_create(
            professeur=professeur,
            cours=cours,
            promotion=profile.promotion,
            defaults={
                'universite': profile.universite,
                'filiere': profile.filiere,
            }
        )

        if created:
            logger.info(f"Dispense créée: {dispense}")
            return Response({
                'message': 'Dispense créée avec succès.',
                'dispense_id': dispense.id,
                'created': True,
            }, status=201)
        else:
            return Response({
                'message': 'Cette dispense existe déjà.',
                'dispense_id': dispense.id,
                'created': False,
            })

    except Exception as e:
        logger.error(f"Erreur création dispense: {e}")
        return Response({'error': str(e)}, status=500)


# ============================================================
# PROFESSEUR — Suppression (CRUD Écran Création)
# ============================================================

@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_professeur_view(request, professeur_id):
    """Supprime un professeur appartenant à l'université de l'utilisateur connecté."""
    try:
        profile = request.user.profile
        if not profile.universite:
            return Response({'error': 'Profil incomplet'}, status=400)
        professeur = get_object_or_404(Professeur, id=professeur_id, universite=profile.universite)
        professeur.delete()
        return Response({'message': 'Professeur supprimé.'}, status=200)
    except Exception as e:
        logger.error(f"Erreur suppression professeur: {e}")
        return Response({'error': str(e)}, status=500)


# ============================================================
# DISPENSE — Liste + Suppression (CRUD Écran Association)
# ============================================================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def list_dispenses_view(request):
    """Liste les dispenses du contexte académique de l'utilisateur connecté."""
    try:
        profile = request.user.profile
        if not profile.universite or not profile.filiere or not profile.promotion:
            return Response([], status=200)
        dispenses = Dispense.objects.filter(
            universite=profile.universite,
            filiere=profile.filiere,
            promotion=profile.promotion,
        ).select_related('professeur__user', 'cours').order_by('-created_at')
        data = [
            {
                'id': d.id,
                'professeur_id': d.professeur.id,
                'professeur_name': d.professeur.user.get_full_name() or d.professeur.user.username,
                'professeur_specialite': d.professeur.specialite or '',
                'cours_id': d.cours.id,
                'cours_nom': d.cours.nom,
                'cours_filiere': d.cours.filiere,
            }
            for d in dispenses
        ]
        return Response(data, status=200)
    except Exception as e:
        logger.error(f"Erreur liste dispenses: {e}")
        return Response({'error': str(e)}, status=500)


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_dispense_view(request, dispense_id):
    """Supprime une dispense appartenant au contexte académique de l'utilisateur."""
    try:
        profile = request.user.profile
        if not profile.universite or not profile.filiere or not profile.promotion:
            return Response({'error': 'Profil incomplet'}, status=400)
        dispense = get_object_or_404(
            Dispense, id=dispense_id,
            universite=profile.universite,
            filiere=profile.filiere,
            promotion=profile.promotion,
        )
        dispense.delete()
        return Response({'message': 'Association supprimée.'}, status=200)
    except Exception as e:
        logger.error(f"Erreur suppression dispense: {e}")
        return Response({'error': str(e)}, status=500)


# ============================================================
# RESOLVE PROFESSOR — Récupération automatique (Objectif 7)
# ============================================================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def resolve_professor_view(request):
    """
    Recherche automatique du professeur associé à un cours
    via la table Dispense, en fonction du contexte académique de l'utilisateur.
    """
    course_id = request.query_params.get('course_id')
    if not course_id:
        return Response({'error': 'course_id requis'}, status=400)

    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return Response({'error': 'Cours introuvable'}, status=404)

    profile = request.user.profile
    if not profile.universite or not profile.filiere or not profile.promotion:
        return Response({'found': False, 'professor': None})

    dispense = Dispense.objects.filter(
        cours=course,
        universite=profile.universite,
        filiere=profile.filiere,
        promotion=profile.promotion
    ).select_related('professeur__user').first()

    if dispense:
        prof = dispense.professeur
        return Response({
            'found': True,
            'professor': {
                'id': prof.id,
                'name': prof.user.get_full_name() or prof.user.username,
                'professeur_fk': prof.id,
            }
        })
    return Response({'found': False, 'professor': None})