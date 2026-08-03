from django.contrib import admin
from django import forms
from django.contrib.auth.models import User
from .models import UserDevice, AppNotification, UserNotification


class AppNotificationForm(forms.ModelForm):
    """Formulaire personnalisé avec logique de ciblage conditionnelle."""

    class Meta:
        model = AppNotification
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Aide contextuelle pour les champs de ciblage
        self.fields['target_universite'].help_text = (
            "Laissez vide pour cibler TOUTES les universités (uniquement pour les notifications Système)"
        )
        self.fields['target_filiere'].help_text = (
            "Laissez vide pour cibler TOUTES les filières. "
            "Nécessite une université si spécifiée."
        )
        self.fields['target_promotion'].help_text = (
            "Laissez vide pour cibler TOUTES les promotions. "
            "Nécessite université + filière si spécifiée."
        )
        self.fields['notification_type'].help_text = (
            "<b>Système</b> = Notification en masse sans push, créée immédiatement.<br>"
            "<b>Autres</b> = Utilisent les tâches Celery (push automatique)."
        )


@admin.register(UserDevice)
class UserDeviceAdmin(admin.ModelAdmin):
    list_display = ['user', 'device_type', 'is_active', 'created_at', 'updated_at']
    list_filter = ['device_type', 'is_active']
    search_fields = ['user__username', 'user__email', 'fcm_token']
    raw_id_fields = ['user']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AppNotification)
class AppNotificationAdmin(admin.ModelAdmin):
    form = AppNotificationForm
    list_display = ['title', 'notification_type', 'target_universite', 'target_filiere',
                    'target_promotion', 'sender', 'recipient_count', 'created_at']
    list_filter = ['notification_type', 'target_universite', 'target_promotion', 'created_at']
    search_fields = ['title', 'body']
    raw_id_fields = ['sender']
    readonly_fields = ['created_at', 'recipient_count']
    fieldsets = (
        (None, {
            'fields': ('title', 'body', 'notification_type', 'sender')
        }),
        ('Ciblage (uniquement pour Système)', {
            'fields': ('target_universite', 'target_filiere', 'target_promotion'),
            'description': (
                '<b style="color: #417690;">Pour les notifications Système :</b> '
                'Laissez tous les champs vides pour cibler <b>TOUS les utilisateurs</b>.<br>'
                'Sélectionnez une université pour cibler cette université.<br>'
                'Ajoutez filière/promotion pour affiner le ciblage.'
            ),
            'classes': ('collapse',),
        }),
        ('Métadonnées', {
            'fields': ('image_url', 'summary_id', 'course_id', 'created_at', 'recipient_count'),
            'classes': ('collapse',),
        }),
    )

    def recipient_count(self, obj):
        """Affiche le nombre de destinataires pour les notifs système."""
        return obj.user_notifications.count()
    recipient_count.short_description = 'Nombre de destinataires'

    def save_model(self, request, obj, form, change):
        """
        Logique de sauvegarde personnalisée :
        - Type 'system' : Création synchrone des UserNotification, SANS push, SANS Celery
        - Autres types : Sauvegarde normale (Celery s'occupe du push)
        """
        is_new = obj.pk is None

        # Sauvegarder la notification d'abord
        if is_new and not obj.sender:
            obj.sender = request.user
        super().save_model(request, obj, form, change)

        # Si c'est une notification Système nouvellement créée, créer les UserNotification
        if is_new and obj.notification_type == 'system':
            self._create_system_notifications(obj)

    def _create_system_notifications(self, notification):
        """
        Crée les entrées UserNotification pour une notification système.
        Synchrone, sans Celery, sans push.
        """
        from users.models import UserProfile

        # Queryset de base : utilisateurs actifs
        profile_qs = UserProfile.objects.select_related('user').filter(
            user__is_active=True
        )

        # Logique de ciblage
        target_univ = notification.target_universite
        target_fil = notification.target_filiere
        target_promo = notification.target_promotion

        if target_univ:
            profile_qs = profile_qs.filter(universite=target_univ)
        if target_fil:
            profile_qs = profile_qs.filter(filiere=target_fil)
        if target_promo:
            profile_qs = profile_qs.filter(promotion=target_promo)

        # Créer les UserNotification en bulk
        count = 0
        for profile in profile_qs:
            UserNotification.objects.get_or_create(
                user=profile.user,
                notification=notification,
                defaults={'delivered': True}  # Marqué comme livré (pas de push)
            )
            count += 1

        # Logger l'action
        import logging
        logger = logging.getLogger(__name__)
        cible = "tous les utilisateurs"
        if target_univ:
            cible = f"univ: {target_univ.nom}"
            if target_fil:
                cible += f", fil: {target_fil.nom}"
                if target_promo:
                    cible += f", promo: {target_promo.nom}"
        logger.info(f'[ADMIN] Notification système #{notification.id} créée pour {count} utilisateurs ({cible})')

    def response_add(self, request, obj, post_url_continue=None):
        """Message de confirmation personnalisé après création."""
        from django.contrib import messages
        if obj.notification_type == 'system':
            count = obj.user_notifications.count()
            messages.success(
                request,
                f'Notification système créée avec succès pour {count} utilisateur(s). '
                'Aucun push envoyé (notification en base uniquement).'
            )
        return super().response_add(request, obj, post_url_continue)


@admin.register(UserNotification)
class UserNotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification', 'is_read', 'read_at', 'created_at']
    list_filter = ['is_read']
    search_fields = ['user__username', 'notification__title']
    raw_id_fields = ['user', 'notification']
    readonly_fields = ['created_at']
