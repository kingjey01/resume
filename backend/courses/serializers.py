from rest_framework import serializers
from .models import (
    Course, Session, Summary, Transcription, Universite, Promotion, Filiere,
    Service, Abonnement, Professeur
)


class ProfesseurSerializer(serializers.ModelSerializer):
    """Serializer pour les professeurs"""
    user_full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    universite_nom = serializers.CharField(source='universite.nom', read_only=True)
    
    class Meta:
        model = Professeur
        fields = ['id', 'user', 'user_full_name', 'user_username', 'telephone', 
                 'specialite', 'universite', 'universite_nom', 'is_active', 'created_at']


class CourseSerializer(serializers.ModelSerializer):
    # Noms lisibles des M2M (toutes les structures assignées)
    universites_noms = serializers.SerializerMethodField()
    filieres_noms = serializers.SerializerMethodField()
    promotions_noms = serializers.SerializerMethodField()

    # Champs de compatibilité frontend (premier élément M2M)
    universite_nom = serializers.SerializerMethodField()
    filiere_nom = serializers.SerializerMethodField()
    promotion_nom = serializers.SerializerMethodField()
    university = serializers.CharField(read_only=True)

    def get_universites_noms(self, obj):
        return list(obj.universites.values_list('nom', flat=True))

    def get_filieres_noms(self, obj):
        return list(obj.filieres.values_list('nom', flat=True))

    def get_promotions_noms(self, obj):
        return list(obj.promotions.values_list('nom', flat=True))

    def get_universite_nom(self, obj):
        u = obj.universites.first()
        return u.nom if u else None

    def get_filiere_nom(self, obj):
        f = obj.filieres.first()
        return f.nom if f else None

    def get_promotion_nom(self, obj):
        p = obj.promotions.first()
        return p.nom if p else None

    class Meta:
        model = Course
        fields = [
            'id', 'nom', 'filiere', 'university', 'description',
            'universites', 'universites_noms',
            'filieres', 'filieres_noms',
            'promotions', 'promotions_noms',
            'universite_nom', 'filiere_nom', 'promotion_nom',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['university', 'filiere', 'created_at', 'updated_at']


class SessionSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.nom', read_only=True)
    professeur_info = ProfesseurSerializer(source='professeur_fk', read_only=True)
    audio_duration_formatted = serializers.ReadOnlyField()
    is_duration_valid = serializers.ReadOnlyField()
    has_ai_summary = serializers.SerializerMethodField()
    ai_summary_id = serializers.SerializerMethodField()
    
    class Meta:
        model = Session
        fields = ['id', 'course', 'course_name', 'professeur_fk', 'professeur_info', 
                 'date', 'professeur', 'audio_file', 
                 'audio_duration', 'audio_duration_formatted', 'is_duration_valid',
                 'summary_title', 'summary_price',
                 'processing_status', 'error_message', 'submitted_at', 'processed_at',
                 'has_ai_summary', 'ai_summary_id', 'created_at', 'updated_at']
    
    def get_has_ai_summary(self, obj):
        """Vérifie si la session a un résumé généré par IA"""
        return obj.summaries.filter(author_type='ai').exists()

    def get_ai_summary_id(self, obj):
        """Retourne l'ID du résumé généré par IA pour cette session"""
        summary = obj.summaries.filter(author_type='ai').order_by('-created_at').first()
        return summary.id if summary else None


class SessionCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer une session (professeur optionnel)"""
    
    class Meta:
        model = Session
        fields = ['course', 'date', 'professeur', 'professeur_fk', 'audio_file']
        extra_kwargs = {
            'professeur_fk': {'required': False, 'allow_null': True},
            'professeur': {'required': False, 'allow_blank': True},
        }
    
    def validate_professeur_fk(self, value):
        """Vérifie que le professeur est actif (si fourni)"""
        if value and not value.is_active:
            raise serializers.ValidationError("Ce professeur n'est pas actif.")
        return value


class TranscriptionSerializer(serializers.ModelSerializer):
    """Serializer pour les transcriptions audio"""
    session_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Transcription
        fields = ['id', 'session', 'session_info', 'texte_transcription', 'langue', 
                 'duree_audio', 'confidence', 'status', 'error_message', 'created_at']
    
    def get_session_info(self, obj):
        return {
            'id': obj.session.id,
            'course_name': obj.session.course.nom,
            'professor': obj.session.professeur,
            'date': obj.session.date
        }


class SummarySerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.nom', read_only=True)
    filiere_name = serializers.SerializerMethodField()
    author_name = serializers.CharField(source='author_user.username', read_only=True)
    transcription_id = serializers.IntegerField(source='transcription.id', read_only=True, allow_null=True)
    professeur_info = ProfesseurSerializer(source='professeur', read_only=True)
    professor_display = serializers.SerializerMethodField()

    def get_professor_display(self, obj):
        """Retourne le nom du professeur (FK, session.professeur_fk, ou session.professeur texte)"""
        # 1. Professeur direct sur le résumé
        if obj.professeur:
            return obj.professeur.user.get_full_name() or obj.professeur.user.username
        # 2. Professeur FK sur la session liée
        if obj.session and obj.session.professeur_fk:
            return obj.session.professeur_fk.user.get_full_name() or obj.session.professeur_fk.user.username
        # 3. Nom texte du professeur sur la session
        if obj.session and obj.session.professeur:
            return obj.session.professeur
        return ''

    def get_filiere_name(self, obj):
        """Retourne le nom de la première filière M2M si disponible, sinon le champ texte"""
        try:
            if obj.course:
                first_f = obj.course.filieres.first()
                if first_f:
                    return first_f.nom
                return obj.course.filiere or ''
        except Exception:
            pass
        return ''

    class Meta:
        model = Summary
        fields = ['id', 'titre', 'texte_resume', 'professeur', 'professeur_info', 'professor_display',
                 'course', 'course_name', 'filiere_name', 'session',
                 'transcription_id', 'author_type', 'author_user', 'author_name', 'pdf_file', 'prix',
                 'is_free', 'is_validated', 'created_at', 'updated_at']
    
    def to_representation(self, instance):
        """Contrôler l'accès au contenu selon le rôle utilisateur et le statut d'achat"""
        data = super().to_representation(instance)
        request = self.context.get('request')
        
        # Utilisateurs non authentifiés : aperçu très limité
        if not request or not request.user.is_authenticated:
            data['is_purchased'] = False
            if len(data['texte_resume']) > 50:
                data['texte_resume'] = data['texte_resume'][:50] + "..."
            return data
        
        user = request.user
        
        # Résumés gratuits : accès complet pour tous
        if instance.is_free:
            data['is_purchased'] = True  # Les résumés gratuits sont considérés comme "achetés"
            return data
        
        # Vérifier si l'utilisateur a acheté ce résumé
        from payments.models import Purchase
        has_purchased = Purchase.objects.filter(
            user=user,
            summary=instance,
            status='completed'
        ).exists()
        
        # Ajouter le statut d'achat aux données
        data['is_purchased'] = has_purchased
        
        if has_purchased:
            return data  # Accès complet si acheté
        
        # Vérifier le profil utilisateur
        if hasattr(user, 'profile'):
            user_profile = user.profile
            
            # CP et ADMIN : accès complet à tous les résumés
            if user_profile.has_free_access():
                return data
            
            # ETUDIANT : aperçu limité pour les résumés payants non achetés
            if user_profile.groupe == 'ETUDIANT':
                if len(data['texte_resume']) > 150:
                    data['texte_resume'] = data['texte_resume'][:150] + "..."
                return data
        
        # Par défaut : aperçu limité
        if len(data['texte_resume']) > 100:
            data['texte_resume'] = data['texte_resume'][:100] + "..."
        return data


class SummaryCreateSerializer(serializers.ModelSerializer):
    professeur_nom = serializers.CharField(required=False, allow_blank=True, write_only=True,
                                          help_text="Nom du professeur (texte libre)")
    
    class Meta:
        model = Summary
        fields = ['titre', 'texte_resume', 'professeur', 'professeur_nom', 'course', 'session', 'author_type', 
                 'pdf_file', 'prix', 'is_free']
        extra_kwargs = {
            'professeur': {'required': False, 'allow_null': True},
        }
    
    def validate_professeur(self, value):
        """Vérifie que le professeur est actif"""
        if value and not value.is_active:
            raise serializers.ValidationError("Ce professeur n'est pas actif.")
        return value
    
    def validate_texte_resume(self, value):
        """Valider et nettoyer le texte du résumé pour éviter les erreurs d'encodage"""
        if value:
            # Remplacer les emojis et caractères spéciaux problématiques
            import re
            # Supprimer les emojis (caractères Unicode > U+FFFF)
            value = re.sub(r'[^\u0000-\uFFFF]', '', value)
            # Remplacer les caractères problématiques courants
            replacements = {
                '\u2018': "'",  # Apostrophe courbe gauche
                '\u2019': "'",  # Apostrophe courbe droite
                '\u201c': '"',  # Guillemet courbe gauche
                '\u201d': '"',  # Guillemet courbe droite
                '\u2013': '-',  # Tiret demi-cadratin
                '\u2014': '-',  # Tiret cadratin
            }
            for old, new in replacements.items():
                value = value.replace(old, new)
        return value
    
    def validate_titre(self, value):
        """Valider et nettoyer le titre"""
        if value:
            import re
            value = re.sub(r'[^\u0000-\uFFFF]', '', value)
        return value
    
    def create(self, validated_data):
        # Set author_user to current user if author_type is 'cp'
        if validated_data.get('author_type') == 'cp':
            validated_data['author_user'] = self.context['request'].user
        
        # Handle professeur_nom - create or find Professeur if name provided
        professeur_nom = validated_data.pop('professeur_nom', None)
        professeur = validated_data.get('professeur')
        
        if professeur_nom and not professeur:
            # Try to find existing professor by name
            from django.db.models import Q
            professeur = Professeur.objects.filter(
                Q(user__first_name__icontains=professeur_nom) | 
                Q(user__last_name__icontains=professeur_nom) |
                Q(specialite__icontains=professeur_nom)
            ).filter(is_active=True).first()
            
            if not professeur:
                from django.contrib.auth.models import User
                # Create a unique username for the professor
                base_username = 'prof_' + professeur_nom.lower().replace(' ', '_')
                username = base_username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}_{counter}"
                    counter += 1
                
                user = User.objects.create(
                    username=username,
                    first_name=professeur_nom.split()[0] if professeur_nom.split() else professeur_nom,
                    last_name=' '.join(professeur_nom.split()[1:]) if len(professeur_nom.split()) > 1 else ''
                )
                
                # Get the user's university from profile
                request_user = self.context['request'].user
                universite = None
                if hasattr(request_user, 'profile') and request_user.profile.universite:
                    universite = request_user.profile.universite
                
                professeur = Professeur.objects.create(
                    user=user,
                    universite=universite,
                    specialite='Professeur',
                    is_active=True
                )
            
            validated_data['professeur'] = professeur
        
        return super().create(validated_data)


class PromotionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Promotion
        fields = ['id', 'nom', 'annee', 'created_at']


class FiliereSerializer(serializers.ModelSerializer):
    promotions = PromotionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Filiere
        fields = ['id', 'nom', 'description', 'promotions', 'created_at']


class UniversiteSerializer(serializers.ModelSerializer):
    filieres = FiliereSerializer(many=True, read_only=True)
    
    class Meta:
        model = Universite
        fields = ['id', 'nom', 'adresse', 'filieres', 'created_at']


class FiliereWithUniversiteSerializer(serializers.ModelSerializer):
    universites = serializers.SerializerMethodField()
    
    class Meta:
        model = Filiere
        fields = ['id', 'nom', 'description', 'universites', 'created_at']
    
    def get_universites(self, obj):
        return [{
            'id': u.id,
            'nom': u.nom,
            'adresse': u.adresse
        } for u in obj.universites.all()]


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'nom', 'description', 'prix', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class AbonnementSerializer(serializers.ModelSerializer):
    service_nom = serializers.CharField(source='service.nom', read_only=True)
    etudiant_username = serializers.CharField(source='etudiant.username', read_only=True)
    is_active = serializers.ReadOnlyField()
    
    class Meta:
        model = Abonnement
        fields = ['id', 'description', 'service', 'service_nom', 'etudiant', 
                 'etudiant_username', 'date_debut', 'date_fin', 'montant', 
                 'devise', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at', 'etudiant']
    
    def create(self, validated_data):
        # Set etudiant to current user
        validated_data['etudiant'] = self.context['request'].user
        return super().create(validated_data)


class AbonnementCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Abonnement
        fields = ['description', 'service', 'date_debut', 'date_fin', 'montant', 'devise']
    
    def create(self, validated_data):
        validated_data['etudiant'] = self.context['request'].user
        return super().create(validated_data)
