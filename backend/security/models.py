from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator


class SecurityLog(models.Model):
    ACTION_TYPES = [
        ('screenshot_attempt', "Tentative de capture d'écran"),
        ('copy_attempt', 'Tentative de copie'),
        ('export_attempt', "Tentative d'export"),
        ('suspicious_activity', 'Activité suspecte'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='security_logs')
    action_type = models.CharField(max_length=30, choices=ACTION_TYPES)
    description = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_action_type_display()} - {self.timestamp}"

    class Meta:
        verbose_name = "Log de Sécurité"
        verbose_name_plural = "Logs de Sécurité"
        ordering = ['-timestamp']


class AppVersion(models.Model):
    """
    Gestion centralisée des versions de l'application mobile.
    """
    version_validator = RegexValidator(
        regex=r'^\d+\.\d+\.\d+$',
        message='Format attendu : X.Y.Z (ex: 1.5.0)',
    )

    latest_version = models.CharField(
        max_length=20, validators=[version_validator],
        default='1.0.0', verbose_name="Dernière version",
        help_text="Dernière version publiée (globale, ex: 1.5.0)",
    )
    minimum_version = models.CharField(
        max_length=20, validators=[version_validator],
        default='1.0.0', verbose_name="Version minimale",
        help_text="Version minimale autorisée. En dessous → mise à jour obligatoire.",
    )
    android_latest_version = models.CharField(
        max_length=20, validators=[version_validator],
        null=True, blank=True, verbose_name="Version Android",
    )
    ios_latest_version = models.CharField(
        max_length=20, validators=[version_validator],
        null=True, blank=True, verbose_name="Version iOS",
    )
    maintenance_mode = models.BooleanField(
        default=False, verbose_name="Mode maintenance",
    )
    maintenance_message = models.TextField(
        null=True, blank=True, verbose_name="Message de maintenance",
        default="L'application est actuellement en maintenance. Veuillez réessayer plus tard.",
    )
    play_store_url = models.URLField(
        max_length=500,
        default='https://play.google.com/store/apps/details?id=com.resumeplus.app',
        verbose_name="URL Play Store",
    )
    app_store_url = models.URLField(
        max_length=500,
        default='https://apps.apple.com/app/idXXXXXXXX',
        verbose_name="URL App Store",
    )
    force_update = models.BooleanField(
        default=False, verbose_name="Forcer la mise à jour",
    )
    mandatory_update_message = models.TextField(
        null=True, blank=True, verbose_name="Message MAJ obligatoire",
        default="Une nouvelle version de Résumé Plus est requise pour continuer.",
    )
    is_active = models.BooleanField(
        default=True, verbose_name="Actif",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Mis à jour le")

    class Meta:
        verbose_name = "Version de l'application"
        verbose_name_plural = "Versions de l'application"
        ordering = ['-created_at']

    def __str__(self):
        return f"v{self.latest_version} (min: v{self.minimum_version})"


class ResumePricingConfig(models.Model):
    """
    Configuration dynamique du prix minimum des résumés.

    Un seul enregistrement actif à la fois.
    L'administrateur modifie le seuil dans l'admin Django.
    Sans déploiement, le nouveau seuil est appliqué immédiatement
    côté backend ET côté Flutter (via l'API).
    """
    minimum_resume_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=3000.00,
        verbose_name="Prix minimum (CDF)",
        help_text="Seuil en Francs Congolais. En dessous, la création du résumé est refusée.",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif",
        help_text="Seule la configuration active est utilisée pour la validation.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuration des prix"
        verbose_name_plural = "Configurations des prix"
        ordering = ['-created_at']

    def __str__(self):
        return f"Prix min: {self.minimum_resume_price} CDF (actif: {self.is_active})"
