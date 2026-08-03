import logging
from django.db import models
from django.contrib.auth.models import User
from courses.models import Universite, Filiere, Promotion

logger = logging.getLogger(__name__)


class UserDevice(models.Model):
    """Stores FCM tokens per device per user for push notifications."""
    DEVICE_TYPES = [
        ('android', 'Android'),
        ('ios', 'iOS'),
        ('web', 'Web'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')
    fcm_token = models.TextField(unique=True)
    device_type = models.CharField(max_length=10, choices=DEVICE_TYPES, default='android')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Appareil Utilisateur'
        verbose_name_plural = 'Appareils Utilisateurs'
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username} — {self.device_type} ({self.fcm_token[:20]}…)"


class AppNotification(models.Model):
    """A notification record that can be targeted to specific groups."""
    TYPE_CHOICES = [
        ('new_summary', 'Nouveau résumé'),
        ('summary_validated', 'Résumé validé'),
        ('summary_created', 'Résumé créé (CP)'),
        ('new_exercise', 'Nouvel exercice'),
        ('system', 'Système'),
        ('promo', 'Promotion'),
        ('payment', 'Paiement'),
        ('general', 'Général'),
    ]

    title = models.CharField(max_length=255)
    body = models.TextField()
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default='general')

    # Targeting — null means "all" for that field
    target_universite = models.ForeignKey(
        Universite, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='notifications'
    )
    target_filiere = models.ForeignKey(
        Filiere, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='notifications'
    )
    target_promotion = models.ForeignKey(
        Promotion, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='notifications'
    )

    # Optional related objects
    summary_id = models.IntegerField(null=True, blank=True)
    course_id = models.IntegerField(null=True, blank=True)

    sender = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='sent_notifications'
    )

    image_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.notification_type}] {self.title}"


class UserNotification(models.Model):
    """Junction table tracking per-user read/unread status for each notification."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_notifications')
    notification = models.ForeignKey(
        AppNotification, on_delete=models.CASCADE, related_name='user_notifications'
    )
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    delivered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notification Utilisateur'
        verbose_name_plural = 'Notifications Utilisateurs'
        unique_together = ('user', 'notification')
        ordering = ['-created_at']

    def __str__(self):
        status = 'lue' if self.is_read else 'non lue'
        return f"{self.user.username} — {self.notification.title[:40]} ({status})"
