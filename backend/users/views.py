from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer, RefreshTokenSerializer,
    CPRequestSerializer,
)
from .models import UserProfile, CPRequest
from courses.permissions import CanAssignRole
import logging
import traceback
import secrets

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register_view(request):
    """
    Endpoint d'inscription - Accessible sans authentification
    """
    serializer = RegisterSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    """
    Endpoint de connexion - Accessible sans authentification
    """
    logger.info(f"Tentative de connexion - Données reçues: {request.data}")
    
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        response_data = {
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': access_token,
        }
        
        logger.info(f"Connexion réussie pour l'utilisateur: {user.email}")
        logger.debug(f"Token généré: {access_token[:15]}...")
        print("====token====")
        print(user)
        print(refresh)
        print(access_token)
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    logger.warning(f"Échec de la connexion - Erreurs: {serializer.errors}")
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def profile_view(request):
    """
    Endpoint pour récupérer le profil de l'utilisateur connecté
    """
    try:
        # Vérification de l'utilisateur (JWTAuthentication est géré par DRF)
        if not request.user or not request.user.is_authenticated:
            return Response(
                {"detail": "Erreur d'authentification"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Récupération du profil
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    except Exception as e:
        logger.error(f"Erreur lors de la récupération du profil: {str(e)}", exc_info=True)

        # Réponse d'erreur générique, avec détails uniquement en mode debug
        error_detail = {
            "detail": "Erreur lors de la récupération du profil",
            "type": type(e).__name__
        }

        if settings.DEBUG:
            error_detail["error"] = str(e)
            error_detail["traceback"] = traceback.format_exc()

        return Response(
            error_detail,
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def test_auth(request):
    """
    Endpoint de test d'authentification
    """
    return Response({
        'message': 'Authentification réussie!',
        'user_id': request.user.id,
        'email': request.user.email,
        'is_authenticated': request.user.is_authenticated
    })


@api_view(['PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def update_profile_view(request):
    """
    Endpoint pour mettre à jour le profil de l'utilisateur connecté
    Supporte l'upload de photo de profil
    """
    user = request.user
    profile = user.profile
    
    # Update user fields
    user_fields = ['first_name', 'last_name', 'email']
    for field in user_fields:
        if field in request.data:
            setattr(user, field, request.data[field])
    user.save()
    
    # Update profile fields with ID support
    if 'universite_id' in request.data:
        try:
            from courses.models import Universite
            profile.universite = Universite.objects.get(id=request.data['universite_id'])
        except Universite.DoesNotExist:
            pass
    elif 'universite' in request.data:
        profile.universite_id = request.data['universite']
    
    if 'promotion_id' in request.data:
        try:
            from courses.models import Promotion
            profile.promotion = Promotion.objects.get(id=request.data['promotion_id'])
        except Promotion.DoesNotExist:
            pass
    elif 'promotion' in request.data:
        profile.promotion_id = request.data['promotion']
    
    if 'filiere_id' in request.data:
        try:
            from courses.models import Filiere
            profile.filiere = Filiere.objects.get(id=request.data['filiere_id'])
        except Filiere.DoesNotExist:
            pass
    elif 'filiere' in request.data:
        profile.filiere_id = request.data['filiere']
    
    if 'phone' in request.data:
        profile.phone = request.data['phone']
    
    # Handle profile picture upload
    if 'profile_picture' in request.FILES:
        profile.profile_picture = request.FILES['profile_picture']
        logger.info(f"Photo de profil mise à jour pour {user.username}")
    
    profile.save()
    
    return Response(UserSerializer(user).data)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def refresh_token_view(request):
    """
    Rafraîchir un token d'accès avec un refresh token
    """
    serializer = RefreshTokenSerializer(data=request.data)
    
    if serializer.is_valid():
        try:
            refresh_token = RefreshToken(serializer.validated_data['refresh'])
            
            # Vérifier si le token est valide
            refresh_token.verify()
            
            # Créer une nouvelle paire de tokens
            user = User.objects.get(id=refresh_token['user_id'])
            new_refresh = RefreshToken.for_user(user)
            new_access = new_refresh.access_token
            
            # Définir les en-têtes de réponse pour le nouveau token
            response = Response({
                'access': str(new_access),
                'refresh': str(new_refresh)
            })
            
            # Ajouter les en-têtes personnalisés
            response['X-New-Access-Token'] = str(new_access)
            response['X-New-Refresh-Token'] = str(new_refresh)
            
            return response
            
        except Exception as e:
            logger.error(f"Erreur lors du rafraîchissement du token: {str(e)}")
            return Response(
                {'detail': 'Token invalide ou expiré.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_info_view(request):
    """
    Endpoint pour récupérer les informations de l'utilisateur connecté
    Utilisé par l'app mobile pour vérifier l'authentification
    """
    try:
        logger.info(f"Récupération des infos utilisateur pour: {request.user.email}")
        
        # Vérifier que l'utilisateur est bien authentifié
        if not request.user or not request.user.is_authenticated:
            return Response(
                {"detail": "Non authentifié"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Sérialiser les données utilisateur
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des infos utilisateur: {str(e)}")
        return Response(
            {"detail": "Erreur serveur"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """
    Déconnexion de l'utilisateur et invalidation du refresh token
    """
    try:
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            # Si aucun token n'est fourni, on se contente de répondre OK
            # car l'utilisateur est déjà authentifié
            return Response(status=status.HTTP_205_RESET_CONTENT)
            
        try:
            token = RefreshToken(refresh_token)
            # Vérifier si le token est valide
            token.verify()
            # Si on arrive ici, le token est valide, on peut le révoquer
            token.blacklist()
        except Exception as token_error:
            # Si le token est invalide, on le considère comme déjà révoqué
            logger.warning(f"Token invalide ou déjà révoqué: {str(token_error)}")
        
        return Response(status=status.HTTP_205_RESET_CONTENT)
        
    except Exception as e:
        logger.error(f"Erreur lors de la déconnexion: {str(e)}")
        # En cas d'erreur, on retourne quand même un code de succès
        # car l'utilisateur est déconnecté côté client de toute façon
        return Response(status=status.HTTP_205_RESET_CONTENT)


# ========================================
# RÉCUPÉRATION DE MOT DE PASSE (Forgot Password)
# ========================================

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def forgot_password_view(request):
    """
    Endpoint pour demander la réinitialisation du mot de passe.
    Envoie un email avec un code de vérification.
    """
    logger.info(f"🔍 FORGOT_PASSWORD - Début de la requête")
    logger.info(f"🔍 FORGOT_PASSWORD - Data reçue: {request.data}")
    
    email = request.data.get('email', '').strip().lower()
    logger.info(f"🔍 FORGOT_PASSWORD - Email extrait: '{email}'")
    
    if not email:
        logger.warning(f"🔍 FORGOT_PASSWORD - Email vide!")
        return Response(
            {'error': 'L\'adresse email est requise.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = User.objects.get(email=email)
        logger.info(f"🔍 FORGOT_PASSWORD - Utilisateur trouvé: {user.username} (ID: {user.id})")
    except User.DoesNotExist:
        logger.warning(f"🔍 FORGOT_PASSWORD - Aucun utilisateur avec email: {email}")
        # Pour des raisons de sécurité, on ne révèle pas si l'email existe ou non
        return Response({
            'message': 'Si cette adresse email existe dans notre système, vous recevrez un code de réinitialisation.'
        }, status=status.HTTP_200_OK)
    
    # Générer un code de vérification à 6 chiffres
    reset_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    logger.info(f"🔍 FORGOT_PASSWORD - Code généré: {reset_code}")
    
    # Stocker le code dans le profil utilisateur (avec expiration)
    try:
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.reset_code = reset_code
        profile.reset_code_expires = timezone.now() + timezone.timedelta(minutes=15)
        profile.save()
        logger.info(f"🔍 FORGOT_PASSWORD - Code sauvegardé dans le profil (created: {created})")
    except Exception as e:
        logger.error(f"🔍 FORGOT_PASSWORD - Erreur sauvegarde profil: {e}")
        import traceback
        logger.error(f"🔍 FORGOT_PASSWORD - Traceback: {traceback.format_exc()}")
        return Response(
            {'error': 'Erreur interne. Veuillez réessayer.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # Envoyer l'email
    try:
        subject = 'Réinitialisation de votre mot de passe - ResumeCours'
        message = f"""
Bonjour {user.first_name or user.username},

Vous avez demandé la réinitialisation de votre mot de passe.

Votre code de vérification est : {reset_code}

Ce code expire dans 15 minutes.

Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.

Cordialement,
L'équipe ResumeCours
        """
        
        logger.info(f"🔍 FORGOT_PASSWORD - Tentative d'envoi email à {email}")
        logger.info(f"🔍 FORGOT_PASSWORD - FROM: {settings.DEFAULT_FROM_EMAIL}")
        logger.info(f"🔍 FORGOT_PASSWORD - EMAIL_HOST: {settings.EMAIL_HOST}")
        logger.info(f"🔍 FORGOT_PASSWORD - EMAIL_PORT: {settings.EMAIL_PORT}")
        logger.info(f"🔍 FORGOT_PASSWORD - EMAIL_TIMEOUT: {getattr(settings, 'EMAIL_TIMEOUT', 'Non défini')}")
        
        # Tentative d'envoi avec timeout et retry
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        
        logger.info(f"🔍 FORGOT_PASSWORD - ✅ Email envoyé avec succès à {email}")
        
    except Exception as e:
        logger.error(f"🔍 FORGOT_PASSWORD - ❌ Erreur envoi email: {e}")
        import traceback
        logger.error(f"🔍 FORGOT_PASSWORD - Traceback: {traceback.format_exc()}")
        
        # En cas d'erreur SMTP, retourner quand même succès pour sécurité
        # Mais avec un message différent
        logger.warning(f"🔍 FORGOT_PASSWORD - Erreur SMTP mais retour succès pour sécurité")
        return Response({
            'message': 'Si cette adresse email existe dans notre système, vous recevrez un code de réinitialisation.',
            'success': True,
            'warning': 'Problème technique avec l\'envoi d\'email. Contactez le support si vous ne recevez pas le code.'
        }, status=status.HTTP_200_OK)
    
    logger.info(f"🔍 FORGOT_PASSWORD - Réponse OK envoyée")
    return Response({
        'message': 'Si cette adresse email existe dans notre système, vous recevrez un code de réinitialisation.',
        'success': True
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verify_reset_code_view(request):
    """
    Vérifie le code de réinitialisation envoyé par email.
    """
    email = request.data.get('email', '').strip().lower()
    code = request.data.get('code', '').strip()
    
    if not email or not code:
        return Response(
            {'error': 'Email et code sont requis.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = User.objects.get(email=email)
        profile = user.profile
    except (User.DoesNotExist, UserProfile.DoesNotExist):
        return Response(
            {'error': 'Code invalide ou expiré.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Vérifier le code et son expiration
    if profile.reset_code != code:
        return Response(
            {'error': 'Code invalide.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if profile.reset_code_expires and profile.reset_code_expires < timezone.now():
        return Response(
            {'error': 'Code expiré. Veuillez demander un nouveau code.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Générer un token temporaire pour la réinitialisation
    reset_token = secrets.token_urlsafe(32)
    profile.reset_token = reset_token
    profile.reset_token_expires = timezone.now() + timezone.timedelta(minutes=10)
    profile.save()
    
    return Response({
        'message': 'Code vérifié avec succès.',
        'reset_token': reset_token
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def reset_password_view(request):
    """
    Réinitialise le mot de passe avec le token de réinitialisation.
    """
    email = request.data.get('email', '').strip().lower()
    reset_token = request.data.get('reset_token', '').strip()
    new_password = request.data.get('new_password', '')
    confirm_password = request.data.get('confirm_password', '')
    
    if not all([email, reset_token, new_password, confirm_password]):
        return Response(
            {'error': 'Tous les champs sont requis.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if new_password != confirm_password:
        return Response(
            {'error': 'Les mots de passe ne correspondent pas.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if len(new_password) < 6:
        return Response(
            {'error': 'Le mot de passe doit contenir au moins 6 caractères.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = User.objects.get(email=email)
        profile = user.profile
    except (User.DoesNotExist, UserProfile.DoesNotExist):
        return Response(
            {'error': 'Token invalide ou expiré.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Vérifier le token et son expiration
    if profile.reset_token != reset_token:
        return Response(
            {'error': 'Token invalide.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if profile.reset_token_expires and profile.reset_token_expires < timezone.now():
        return Response(
            {'error': 'Token expiré. Veuillez recommencer la procédure.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Réinitialiser le mot de passe
    user.set_password(new_password)
    user.save()
    
    # Nettoyer les tokens de réinitialisation
    profile.reset_code = None
    profile.reset_code_expires = None
    profile.reset_token = None
    profile.reset_token_expires = None
    profile.save()
    
    logger.info(f"Mot de passe réinitialisé pour {email}")
    
    return Response({
        'message': 'Mot de passe réinitialisé avec succès. Vous pouvez maintenant vous connecter.'
    }, status=status.HTTP_200_OK)


# ========================================
# MODIFICATION DE MOT DE PASSE (Settings)
# ========================================

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password_view(request):
    """
    Permet à l'utilisateur connecté de modifier son mot de passe.
    Requiert le mot de passe actuel pour confirmation.
    """
    current_password = request.data.get('current_password', '')
    new_password = request.data.get('new_password', '')
    confirm_password = request.data.get('confirm_password', '')
    
    if not all([current_password, new_password, confirm_password]):
        return Response(
            {'error': 'Tous les champs sont requis.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = request.user
    
    # Vérifier le mot de passe actuel
    if not user.check_password(current_password):
        return Response(
            {'error': 'Mot de passe actuel incorrect.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Vérifier que les nouveaux mots de passe correspondent
    if new_password != confirm_password:
        return Response(
            {'error': 'Les nouveaux mots de passe ne correspondent pas.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Vérifier la longueur minimale
    if len(new_password) < 6:
        return Response(
            {'error': 'Le nouveau mot de passe doit contenir au moins 6 caractères.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Vérifier que le nouveau mot de passe est différent de l'ancien
    if current_password == new_password:
        return Response(
            {'error': 'Le nouveau mot de passe doit être différent de l\'ancien.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Modifier le mot de passe
    user.set_password(new_password)
    user.save()
    
    logger.info(f"Mot de passe modifié pour l'utilisateur {user.email}")
    
    return Response({
        'message': 'Mot de passe modifié avec succès.'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def request_otp_view(request):
    """
    Demande d'envoi d'un code OTP par SMS
    """
    from .utils import normalize_phone, is_test_phone

    phone = request.data.get('phone')

    if not phone:
        return Response(
            {'error': 'Numéro de téléphone requis'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Normaliser le numéro de téléphone
    # Gère les formats: +243XXX, 243XXX, 0XXX, ou XXX (9 chiffres)
    phone = normalize_phone(phone)

    try:
        # Chercher l'utilisateur par numéro de téléphone
        try:
            profile = UserProfile.objects.get(phone=phone)
            user = profile.user
            user_exists = True
        except UserProfile.DoesNotExist:
            # Créer un utilisateur temporaire pour ce numéro
            from django.contrib.auth.models import User
            import uuid
            
            # Générer un username temporaire unique
            temp_username = f"temp_{phone.replace('+', '').replace(' ', '')}"
            
            # Créer l'utilisateur temporaire
            user = User.objects.create_user(
                username=temp_username,
                email=f"{temp_username}@temp.resume-plus.com",
                password=str(uuid.uuid4())  # Mot de passe temporaire aléatoire
            )
            
            # Créer le profil associé
            profile = UserProfile.objects.create(
                user=user,
                phone=phone,
                groupe='ETUDIANT'  # Par défaut
            )
            user_exists = False
        
        # Générer le code OTP
        otp_code = profile.generate_otp()

        logger.info(f"Code OTP généré pour {phone}: {otp_code} (Utilisateur {'existant' if user_exists else 'nouveau'})")

        # ── Mode de test Google Play : pas de SMS, OTP fixe "1234" accepté ──
        # Le flux API reste identique (même réponse, même code généré).
        # Pour les numéros de test, on renvoie le code OTP généré dans la réponse
        # → le frontend peut le soumettre AUTOMATIQUEMENT sans que le testeur
        # ait besoin de le lire dans les logs serveur.
        if is_test_phone(phone):
            print(f"=== [TEST MODE] Numéro de test {phone} — SMS NON envoyé ===")
            print(f"Code OTP généré (affiché pour les tests): {otp_code}")
            print(f"Code OTP fixe accepté : 1234")
            print(f"========================================================")
            return Response({
                'message': 'Code OTP envoyé par SMS',
                'phone': phone,
                'user_exists': user_exists,
                'otp_code': otp_code,
                'test_mode': True,
            }, status=status.HTTP_200_OK)

        # Envoi réel du SMS via Keccel API
        sms_sent = False
        try:
            import requests as http_requests
            import json as json_lib
            
            sms_url = settings.SMS_URL
            sms_token = settings.KECCEL_SMS_TOKEN
            
            # Nettoyer le numéro : retirer le '+' (Keccel exige le format sans +)
            clean_phone = phone.lstrip('+').strip()
            
            sms_data = {
                "campaignId": 1,
                "routeId": 1,
                "sender": "TIKAPOINT",
                "mode": "text",
                "message": "Bonjour #name#, Votre code OTP est : #otp# (valable 10 minutes).",
                "contacts": [
                    {"mobile": clean_phone, "parameters": {"name": clean_phone, "otp": otp_code}},
                ],
            }
            
            sms_headers = {
                "Authorization": f"Bearer {sms_token}",
                "Content-Type": "application/json"
            }
            
            sms_response = http_requests.post(
                sms_url,
                data=json_lib.dumps(sms_data),
                headers=sms_headers,
                timeout=15
            )
            
            if sms_response.status_code in [200, 201]:
                sms_sent = True
                logger.info(f"[OK] SMS OTP envoye avec succes a {phone}")
            else:
                logger.warning(f"[ECHEC] Envoi SMS Keccel (status={sms_response.status_code}): {sms_response.text}")
                
        except Exception as sms_error:
            logger.error(f"[ERREUR] Envoi SMS Keccel: {str(sms_error)}")
        
        # Log console (fallback / debug)
        if not sms_sent:
            print(f"=== FALLBACK SMS (non envoyé) ===")
            print(f"Destinataire: {phone}")
            print(f"Message: Votre code OTP est : {otp_code}")
            print(f"Code valide pendant 10 minutes")
            print(f"=================================")
        
        return Response({
            'message': 'Code OTP envoyé par SMS',
            'phone': phone,
            'user_exists': user_exists,
        }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Erreur lors de la génération OTP: {str(e)}")
        return Response(
            {'error': 'Erreur interne du serveur'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verify_otp_view(request):
    """
    Vérification du code OTP et connexion automatique
    """
    from .utils import normalize_phone

    phone = request.data.get('phone')
    otp_code = request.data.get('otp_code')

    if not phone or not otp_code:
        return Response(
            {'error': 'Numéro de téléphone et code OTP requis'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Normaliser le numéro de téléphone
    # Gère les formats: +243XXX, 243XXX, 0XXX, ou XXX (9 chiffres)
    phone = normalize_phone(phone)

    try:
        # Chercher l'utilisateur par numéro de téléphone
        profile = UserProfile.objects.get(phone=phone)
        user = profile.user
        
        # Vérifier le code OTP
        if profile.verify_otp(otp_code):
            # Générer les tokens JWT
            refresh = RefreshToken.for_user(user)

            # Vérifier si le profil est complet (uniquement ces 3 champs obligatoires)
            has_universite = profile.universite is not None
            has_promotion = profile.promotion is not None
            has_filiere = profile.filiere is not None

            profile_complete = has_universite and has_promotion and has_filiere

            # Log détaillé pour debug
            logger.info(f"🔍 [OTP] Vérification profil pour {phone}:")
            logger.info(f"🔍 [OTP]   - Université: {has_universite} (ID: {profile.universite_id})")
            logger.info(f"🔍 [OTP]   - Promotion: {has_promotion} (ID: {profile.promotion_id})")
            logger.info(f"🔍 [OTP]   - Filière: {has_filiere} (ID: {profile.filiere_id})")
            logger.info(f"🔍 [OTP]   → Profil complet: {profile_complete}")

            return Response({
                'message': 'Connexion réussie',
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'profile_complete': profile_complete,
                'role': profile.groupe,
                'cp_onboarding_completed': profile.cp_onboarding_completed,
            }, status=status.HTTP_200_OK)
        else:
            # Vérifier si trop de tentatives
            if profile.otp_attempts >= 3:
                profile.reset_otp()
                return Response(
                    {'error': 'Trop de tentatives. Demandez un nouveau code.'},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
            
            return Response(
                {'error': 'Code OTP invalide ou expiré'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except UserProfile.DoesNotExist:
        return Response(
            {'error': 'Aucun compte associé à ce numéro de téléphone'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Erreur lors de la vérification OTP: {str(e)}")
        return Response(
            {'error': 'Erreur interne du serveur'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def complete_profile_view(request):
    """
    Compléter le profil utilisateur avec les informations obligatoires
    """
    try:
        user = request.user
        profile = user.profile
        
        # Logs de debug pour diagnostiquer
        logger.info(f"Profile completion attempt - User: {user.username} (ID: {user.id})")
        logger.info(f"Request headers: {dict(request.headers)}")
        logger.info(f"Request data: {request.data}")
        
        # Récupérer les données du formulaire
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        universite_id = request.data.get('universite_id')
        promotion_id = request.data.get('promotion_id')
        filiere_id = request.data.get('filiere_id')
        
        # Validation des champs obligatoires
        if not all([first_name, last_name, universite_id, promotion_id, filiere_id]):
            return Response({
                'error': 'Tous les champs sont obligatoires',
                'required_fields': ['first_name', 'last_name', 'universite_id', 'promotion_id', 'filiere_id']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Vérifier que les entités existent
        from courses.models import Universite, Promotion, Filiere
        
        try:
            universite = Universite.objects.get(id=universite_id)
            promotion = Promotion.objects.get(id=promotion_id)
            filiere = Filiere.objects.get(id=filiere_id)
        except (Universite.DoesNotExist, Promotion.DoesNotExist, Filiere.DoesNotExist):
            return Response({
                'error': 'Université, promotion ou filière invalide'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Mettre à jour les informations utilisateur
        user.first_name = first_name.strip()
        user.last_name = last_name.strip()
        user.save()
        
        # Mettre à jour le profil
        profile.universite = universite
        profile.promotion = promotion
        profile.filiere = filiere
        profile.save()
        
        # Générer un nouveau username basé sur le nom complet
        new_username = f"{first_name.lower()}.{last_name.lower()}.{universite.nom[:3].lower()}"
        
        # S'assurer que le username est unique
        base_username = new_username
        counter = 1
        while User.objects.filter(username=new_username).exclude(id=user.id).exists():
            new_username = f"{base_username}{counter}"
            counter += 1
        
        user.username = new_username
        user.save()
        
        logger.info(f"Profil complété pour {user.username} ({profile.phone})")
        
        return Response({
            'message': 'Profil complété avec succès',
            'user': UserSerializer(user).data,
            'profile_complete': True
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la complétion du profil: {str(e)}")
        return Response({
            'error': 'Erreur interne du serveur'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def request_delete_otp_view(request):
    """
    Envoyer un code OTP au numéro de téléphone de l'utilisateur pour confirmer la suppression de son compte
    """
    from .utils import is_test_phone

    try:
        profile = UserProfile.objects.get(user=request.user)
        phone = profile.phone

        if not phone:
            return Response({'error': 'Aucun numéro de téléphone associé à votre compte'}, status=status.HTTP_400_BAD_REQUEST)

        otp_code = profile.generate_otp()
        logger.info(f"Code OTP de suppression généré pour {phone}: {otp_code}")

        # ── Mode de test Google Play : pas de SMS, OTP fixe "1234" accepté ──
        if is_test_phone(phone):
            print(f"=== [TEST MODE] Suppression de compte — SMS NON envoyé à {phone} ===")
            print(f"Code OTP généré (affiché pour les tests): {otp_code}")
            print(f"Code OTP fixe accepté : 1234")
            print(f"================================================================")
            masked_phone = phone[:4] + '***' + phone[-3:] if len(phone) >= 7 else phone
            return Response({
                'message': f'Code OTP envoyé au {masked_phone}',
                'phone_masked': masked_phone,
                'otp_code': otp_code,
                'test_mode': True,
            }, status=status.HTTP_200_OK)

        # Envoi réel du SMS via Keccel API
        sms_sent = False
        try:
            import requests as http_requests
            import json as json_lib
            sms_url = settings.SMS_URL
            sms_token = settings.KECCEL_SMS_TOKEN
            clean_phone = phone.lstrip('+').strip()
            sms_data = {
                "campaignId": 1,
                "routeId": 1,
                "sender": "TIKAPOINT",
                "mode": "text",
                "message": "Bonjour #name#, Votre code de suppression de compte est : #otp# (valable 10 minutes).",
                "contacts": [
                    {"mobile": clean_phone, "parameters": {"name": clean_phone, "otp": otp_code}},
                ],
            }
            sms_response = http_requests.post(
                sms_url,
                data=json_lib.dumps(sms_data),
                headers={"Authorization": f"Bearer {sms_token}", "Content-Type": "application/json"},
                timeout=15,
            )
            if sms_response.status_code in [200, 201]:
                sms_sent = True
                logger.info(f"[OK] SMS OTP suppression envoyé à {phone}")
            else:
                logger.warning(f"[ECHEC] Envoi SMS (status={sms_response.status_code}): {sms_response.text}")
        except Exception as sms_error:
            logger.warning(f"Erreur envoi SMS: {sms_error}")

        if not sms_sent:
            print(f"=== FALLBACK SMS suppression (non envoyé) ===")
            print(f"Destinataire: {phone}")
            print(f"Code OTP suppression: {otp_code}")
            print(f"=================================")

        # Masquer le numéro de téléphone partiellement
        masked_phone = phone[:4] + '***' + phone[-3:] if len(phone) >= 7 else phone

        return Response({
            'message': f'Code OTP envoyé au {masked_phone}',
            'phone_masked': masked_phone,
        }, status=status.HTTP_200_OK)

    except UserProfile.DoesNotExist:
        return Response({'error': 'Profil introuvable'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Erreur request_delete_otp: {str(e)}")
        return Response({'error': 'Erreur interne du serveur'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_account_view(request):
    """
    Supprimer le compte de l'utilisateur après vérification du code OTP
    """
    try:
        otp_code = request.data.get('otp_code')
        reason = request.data.get('reason', 'Non spécifié')

        if not otp_code:
            return Response({'error': 'Code OTP requis'}, status=status.HTTP_400_BAD_REQUEST)

        profile = UserProfile.objects.get(user=request.user)

        if not profile.verify_otp(str(otp_code)):
            if profile.otp_attempts >= 3:
                profile.reset_otp()
                return Response({'error': 'Trop de tentatives. Demandez un nouveau code.'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
            return Response({'error': 'Code OTP invalide ou expiré'}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        username = user.username
        logger.info(f"Suppression de compte confirmée pour {username} - Raison: {reason}")

        # Supprimer l'utilisateur (cascade vers le profil et ses données personnelles).
        # Son contenu publié (résumés, sessions, exercices) survit grâce aux FKs en SET_NULL,
        # ce qui préserve les achats des étudiants qui ont payé pour ce contenu.
        user.delete()

        return Response({'message': 'Compte supprimé avec succès'}, status=status.HTTP_200_OK)

    except UserProfile.DoesNotExist:
        return Response({'error': 'Profil introuvable'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Erreur delete_account: {str(e)}")
        return Response({'error': 'Erreur interne du serveur'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ═══════════════════════════════════════════════════════════════════
# DEMANDE POUR DEVENIR CP
# ═══════════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_cp_request_view(request):
    """
    Crée une demande pour devenir CP.

    Règles :
    - Un utilisateur déjà CP ou ADMIN ne peut pas demander.
    - Une seule demande en attente par utilisateur.
    - Si une demande en attente existe, retourne un message.
    """
    try:
        user = request.user

        if not hasattr(user, 'profile'):
            return Response({'error': 'Profil non trouvé'}, status=status.HTTP_404_NOT_FOUND)

        profile = user.profile

        # Un CP ou ADMIN ne demande pas
        if profile.groupe in ['CP', 'ADMIN']:
            return Response({
                'error': 'Vous êtes déjà CP ou administrateur.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Vérifier qu'une demande en attente n'existe pas déjà
        pending = CPRequest.objects.filter(user=user, status='pending').first()
        if pending:
            return Response({
                'error': 'Vous avez déjà une demande en attente de traitement.',
                'request': CPRequestSerializer(pending).data,
                'already_pending': True,
            }, status=status.HTTP_200_OK)

        # Créer la demande
        motivation = request.data.get('motivation', '').strip()
        # Email du candidat : celui fourni dans le formulaire, sinon l'email du compte
        email = (request.data.get('email') or '').strip() or user.email
        cp_request = CPRequest.objects.create(
            user=user,
            email=email,
            motivation=motivation,
            status='pending',
        )

        logger.info(f"📝 Nouvelle demande CP de {user.username} (ID: {cp_request.id})")

        # Notifier l'administration par email (arrière-plan Celery, pas de push)
        try:
            from .tasks import notify_admin_new_cp_request
            try:
                notify_admin_new_cp_request.apply_async(
                    kwargs={'cp_request_id': cp_request.id},
                    countdown=2,
                )
            except Exception as celery_error:
                # File Celery indisponible : envoi synchrone en dernier recours
                try:
                    notify_admin_new_cp_request.run(cp_request_id=cp_request.id)
                except Exception as sync_error:
                    logger.warning(f"Échec notification admin (demande {cp_request.id}): {sync_error}")
        except Exception as import_error:
            logger.warning(f"Notification admin non planifiée (demande {cp_request.id}): {import_error}")

        return Response({
            'message': 'Votre demande pour devenir CP a été envoyée. Elle sera traitée par un administrateur.',
            'request': CPRequestSerializer(cp_request).data,
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Erreur création demande CP: {str(e)}")
        return Response({'error': 'Erreur interne du serveur'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_cp_request_view(request):
    """
    Récupère le statut de la demande CP de l'utilisateur connecté.
    Retourne la dernière demande (quelle que soit son statut).
    """
    try:
        cp_request = CPRequest.objects.filter(user=request.user).first()

        if not cp_request:
            return Response({
                'has_request': False,
                'request': None,
            }, status=status.HTTP_200_OK)

        return Response({
            'has_request': True,
            'request': CPRequestSerializer(cp_request).data,
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Erreur récupération demande CP: {str(e)}")
        return Response({'error': 'Erreur interne du serveur'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
