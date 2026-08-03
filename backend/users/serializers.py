from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.exceptions import TokenError
from .models import UserProfile, CPRequest
from courses.models import Universite, Promotion, Filiere


class UserProfileSerializer(serializers.ModelSerializer):
    universite = serializers.PrimaryKeyRelatedField(queryset=Universite.objects.all(), required=False, allow_null=True)
    promotion = serializers.PrimaryKeyRelatedField(queryset=Promotion.objects.all(), required=False, allow_null=True)
    filiere = serializers.PrimaryKeyRelatedField(queryset=Filiere.objects.all(), required=False, allow_null=True)
    has_active_subscription = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['groupe', 'phone', 'profile_picture', 'universite', 'promotion', 'filiere', 'points', 'has_active_subscription']


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    groupe = serializers.ChoiceField(choices=UserProfile.GROUPE_CHOICES, default='ETUDIANT')
    phone = serializers.CharField(required=False, allow_blank=True)
    universite = serializers.PrimaryKeyRelatedField(queryset=Universite.objects.all(), required=False, allow_null=True)
    promotion = serializers.PrimaryKeyRelatedField(queryset=Promotion.objects.all(), required=False, allow_null=True)
    filiere = serializers.PrimaryKeyRelatedField(queryset=Filiere.objects.all(), required=False, allow_null=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'first_name', 'last_name', 
                 'groupe', 'phone', 'universite', 'promotion', 'filiere']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas.")
        return attrs
    
    def create(self, validated_data):
        # Remove password_confirm and profile fields
        validated_data.pop('password_confirm')
        groupe = validated_data.pop('groupe', 'ETUDIANT')
        phone = validated_data.pop('phone', '')
        universite = validated_data.pop('universite', None)
        promotion = validated_data.pop('promotion', None)
        filiere = validated_data.pop('filiere', None)
        
        # Create user
        user = User.objects.create_user(**validated_data)
        
        # Create profile
        UserProfile.objects.create(
            user=user,
            groupe=groupe,
            phone=phone,
            universite=universite,
            promotion=promotion,
            filiere=filiere
        )
        
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(
                request=self.context.get('request'),
                username=username,
                password=password
            )
            if not user:
                msg = 'Impossible de se connecter avec les identifiants fournis.'
                raise serializers.ValidationError({'non_field_errors': [msg]}, code='authorization')
        else:
            msg = 'Les champs "username" et "password" sont requis.'
            raise serializers.ValidationError({'non_field_errors': [msg]}, code='authorization')
            
        attrs['user'] = user
        return attrs


class RefreshTokenSerializer(serializers.Serializer):
    """
    Sérialiseur pour valider les tokens de rafraîchissement
    """
    refresh = serializers.CharField()
    access = serializers.CharField(read_only=True)

    def validate(self, attrs):
        refresh = attrs.get('refresh')
        
        if not refresh:
            raise serializers.ValidationError(
                {'refresh': 'Ce champ est requis.'},
                code='required'
            )
            
        try:
            # Valider le token de rafraîchissement
            token = RefreshToken(refresh)
            
            # Vérifier que le token n'est pas dans la liste noire
            from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
            
            if hasattr(token, 'check_blacklist') and token.check_blacklist():
                raise serializers.ValidationError(
                    {'refresh': 'Ce token a été révoqué.'},
                    code='token_blacklisted'
                )
                
            # Ajouter le nouveau token d'accès à la réponse
            attrs['access'] = str(token.access_token)
            
        except TokenError as e:
            raise serializers.ValidationError(
                {'refresh': 'Token invalide ou expiré.'},
                code='token_invalid'
            )

        return attrs


class CPRequestSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les demandes de devenir CP.
    """
    username = serializers.CharField(source='user.username', read_only=True)
    user_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = CPRequest
        fields = [
            'id', 'username', 'user_name', 'motivation',
            'status', 'status_display', 'admin_comment',
            'created_at', 'processed_at',
        ]
        read_only_fields = ['id', 'username', 'user_name', 'status', 'status_display',
                            'admin_comment', 'created_at', 'processed_at']

    def get_user_name(self, obj):
        user = obj.user
        full = user.get_full_name()
        return full if full else user.username
