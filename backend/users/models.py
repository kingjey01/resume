from django.contrib.auth.models import User
from django.db import models
from django.conf import settings
from courses.models import Universite, Promotion, Filiere
from .utils import is_test_phone


class UserProfile(models.Model):
    GROUPE_CHOICES = [
        ('ETUDIANT', 'Étudiant'),
        ('CP', 'Chef de Promotion'),
        ('ADMIN', 'Administrateur'),
        ('Prof', 'Professeur')
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    groupe = models.CharField(max_length=20, choices=GROUPE_CHOICES, default='ETUDIANT')
    # Source de vérité UNIQUE pour détecter le premier accès CP.
    # - False par défaut : tant que False, le CP doit faire l'onboarding.
    # - Mis à True UNIQUEMENT par le backend, dans une transaction,
    #   quand l'onboarding CP (professeur + cours + association) est terminé.
    cp_onboarding_completed = models.BooleanField(
        default=False,
        help_text="Source de vérité : le CP a-t-il terminé son onboarding ?"
    )
    phone = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    
    # Relations vers les nouvelles tables
    universite = models.ForeignKey(Universite, on_delete=models.SET_NULL, blank=True, null=True)
    promotion = models.ForeignKey(Promotion, on_delete=models.SET_NULL, blank=True, null=True)
    filiere = models.ForeignKey(Filiere, on_delete=models.SET_NULL, blank=True, null=True)
    
    points = models.IntegerField(default=0)  # Gamification
    
    # Champs pour la réinitialisation de mot de passe
    reset_code = models.CharField(max_length=6, blank=True, null=True)
    reset_code_expires = models.DateTimeField(blank=True, null=True)
    reset_token = models.CharField(max_length=100, blank=True, null=True)
    reset_token_expires = models.DateTimeField(blank=True, null=True)
    
    # Champs pour l'authentification OTP
    # otp_code contient le HASH du code (jamais le code en clair, TACHES.md).
    # Longueur : hash sha256 hex (64 caractères).
    otp_code = models.CharField(max_length=64, blank=True, null=True)
    otp_expires = models.DateTimeField(blank=True, null=True)
    otp_verified = models.BooleanField(default=False)
    otp_attempts = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_groupe_display()}"
    
    @property
    def is_cp(self):
        return self.groupe == 'CP'
    
    @property
    def is_admin(self):
        return self.groupe == 'ADMIN'
    
    @property
    def is_etudiant(self):
        return self.groupe == 'ETUDIANT'
    
    def can_create_summary(self):
        """Vérifie si l'utilisateur peut créer des résumés"""
        return self.groupe in ['CP', 'ADMIN']
    
    def has_free_access(self):
        """Vérifie si l'utilisateur a accès gratuit aux résumés"""
        return self.groupe in ['CP', 'ADMIN']
    
    def generate_otp(self):
        """Génère un code OTP aléatoire et définit l'expiration.

        Le code CLAIR est retourné (pour l'envoi SMS / le mode test) mais
        seul son HASH est stocké en base (TACHES.md : pas d'OTP en clair).
        """
        import random
        from django.utils import timezone
        from datetime import timedelta
        from .utils import hash_otp

        # Générer un code OTP aléatoire à 4 chiffres
        code = str(random.randint(1000, 9999))
        self.otp_code = hash_otp(code)
        self.otp_expires = timezone.now() + timedelta(minutes=10)
        self.otp_verified = False
        self.otp_attempts = 0
        self.save()
        return code

    def verify_otp(self, code):
        """Vérifie le code OTP (comparaison par hash, usage unique)"""
        import hmac
        from django.utils import timezone
        from .utils import hash_otp

        if not self.otp_code or not self.otp_expires:
            return False

        if timezone.now() > self.otp_expires:
            return False

        if self.otp_attempts >= settings.OTP_MAX_VERIFY_ATTEMPTS:
            return False

        # Accepter le vrai code OTP. Le code de test "1234" n'est accepté que :
        #  - en mode DEBUG (développement), OU
        #  - en mode de test Google Play (OTP_TEST_MODE) pour les numéros
        #    configurés dans OTP_TEST_PHONE_NUMBERS.
        # Jamais pour les utilisateurs réels en production.
        accepts_test_code = code == "1234" and (
            settings.DEBUG or is_test_phone(self.phone)
        )
        if accepts_test_code or hmac.compare_digest(self.otp_code, hash_otp(code)):
            self.otp_verified = True
            self.otp_code = None
            self.otp_expires = None
            self.otp_attempts = 0
            self.save()
            return True
        else:
            self.otp_attempts += 1
            self.save()
            return False
    
    def reset_otp(self):
        """Remet à zéro les données OTP"""
        self.otp_code = None
        self.otp_expires = None
        self.otp_verified = False
        self.otp_attempts = 0
        self.save()

    def has_active_subscription(self):
        """
        Vérifie si l'utilisateur a un abonnement actif pour n'importe quel service.
        L'abonnement est obligatoire pour TOUS les utilisateurs (y compris CP et ADMIN).
        """
        from payments.models import Abonnement
        from django.utils import timezone

        now = timezone.now()
        # Rechercher un abonnement dont la période de validité couvre 'maintenant' et est actif
        return Abonnement.objects.filter(
            user=self.user,
            status='active',
            date_debut__lte=now,
            date_fin__gte=now
        ).exists()

    class Meta:
        verbose_name = "Profil Utilisateur"
        verbose_name_plural = "Profils Utilisateurs"


class CPRequest(models.Model):
    """
    Demande d'un utilisateur pour devenir CP (Chef de Promotion).

    Règles :
    - Un utilisateur nouvellement inscrit est toujours étudiant.
    - Il peut demander à devenir CP via un formulaire.
    - Une seule demande en attente par utilisateur.
    - Statut initial : 'pending' (En attente).
    """
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('approved', 'Approuvée'),
        ('rejected', 'Refusée'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='cp_requests',
        help_text="Utilisateur qui fait la demande"
    )
    email = models.EmailField(
        blank=True,
        help_text="Email du candidat pour les notifications d'approbation/refus"
    )
    motivation = models.TextField(
        blank=True,
        help_text="Motivation du candidat (pourquoi devenir CP)"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending'
    )
    admin_comment = models.TextField(
        blank=True, null=True,
        help_text="Commentaire de l'administrateur (approbation/refus)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Demande CP"
        verbose_name_plural = "Demandes CP"
        ordering = ['-created_at']

    def __str__(self):
        return f"Demande CP - {self.user.username} ({self.status})"

    @property
    def is_pending(self):
        return self.status == 'pending'
