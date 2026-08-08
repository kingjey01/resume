from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, CPRequest


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profil'


class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'groupe', 'universite', 'promotion', 'filiere', 'points', 'created_at']
    list_filter = ['groupe', 'universite', 'promotion', 'filiere', 'created_at']
    search_fields = ['user__username', 'user__email', 'universite__nom', 'filiere__nom']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(CPRequest)
class CPRequestAdmin(admin.ModelAdmin):
    """
    Administration des demandes de devenir CP.
    Approuver une demande → le profil de l'utilisateur passe en 'CP'.
    """
    list_display = ['user', 'email', 'status', 'created_at', 'processed_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'user__email', 'email', 'motivation']
    readonly_fields = ['created_at', 'processed_at']
    actions = ['approve_requests', 'reject_requests']

    def approve_requests(self, request, queryset):
        """
        Approuve les demandes sélectionnées — UNE seule action pour tout :
        1. Statut de la demande → 'approved'
        2. Rôle de l'utilisateur → 'CP' (automatique, jamais manuel)
        3. cp_onboarding_completed → False (l'onboarding CP se déclenche au login)
        4. Notification individuelle envoyée à l'utilisateur

        Le tout dans une transaction : en cas d'erreur, rien n'est appliqué.
        """
        from django.db import transaction
        from django.utils import timezone

        approved = 0
        errors = 0

        for cp_request in queryset.filter(status='pending'):
            try:
                with transaction.atomic():
                    user = cp_request.user

                    # 1. Statut de la demande
                    cp_request.status = 'approved'
                    cp_request.processed_at = timezone.now()
                    cp_request.save()

                    # 2. Rôle attribué automatiquement (jamais manuellement)
                    profile = user.profile
                    profile.groupe = 'CP'
                    # 3. L'onboarding CP se déclenchera à la prochaine connexion
                    profile.cp_onboarding_completed = False
                    profile.save()

                    # 4. Notification individuelle à l'utilisateur
                    self._notify_approval(user)

                    # 5. Email d'approbation au candidat
                    self._send_status_email(cp_request, approved=True)

                    approved += 1
            except Exception as e:
                errors += 1
                self.message_user(
                    request,
                    f"Erreur pour {cp_request.user.username}: {e}",
                    level='error',
                )

        if approved:
            self.message_user(
                request,
                f"{approved} demande(s) approuvée(s). "
                f"L'utilisateur est maintenant CP et verra l'onboarding à sa prochaine connexion.",
            )
        if errors:
            self.message_user(request, f"{errors} demande(s) en erreur (rien appliqué).", level='warning')

    approve_requests.short_description = "✅ Approuver (rôle CP + onboarding + notification automatiques)"

    def _notify_approval(self, user):
        """Crée et envoie une notification individuelle d'approbation."""
        try:
            from notifications.models import AppNotification, UserNotification

            notif = AppNotification.objects.create(
                title='🎉 Demande CP approuvée',
                body='Félicitations ! Votre demande pour devenir Chef de Promotion (CP) '
                     'a été acceptée. Vous pouvez maintenant créer des cours et publier des résumés.',
                notification_type='system',
                sender=None,
            )
            un = UserNotification.objects.create(
                user=user,
                notification=notif,
            )

            # Envoi push FCM individuel (non bloquant si échoue)
            try:
                from notifications.tasks import send_fcm_notification
                send_fcm_notification.apply_async(
                    kwargs={'user_notification_ids': [un.id]},
                    countdown=2,
                )
            except Exception:
                pass
        except Exception as e:
            # La notification ne doit pas bloquer l'approbation
            import logging
            logging.getLogger(__name__).warning(f"Notification CP approval échouée: {e}")

    def _send_status_email(self, cp_request, approved):
        """
        Planifie l'envoi de l'email d'approbation/refus en arrière-plan (Celery),
        comme pour les notifications push FCM.
        Repli synchrone si la file Celery n'est pas disponible.
        """
        import logging

        logger = logging.getLogger(__name__)
        from .tasks import send_cp_status_email

        try:
            send_cp_status_email.apply_async(
                kwargs={'cp_request_id': cp_request.id, 'approved': approved},
                countdown=2,
            )
            logger.info(f"Email {'approbation' if approved else 'refus'} CP planifié (Celery) pour la demande {cp_request.id}")
        except Exception as e:
            # File Celery indisponible : envoi synchrone en dernier recours
            # pour ne jamais perdre la notification par email.
            logger.warning(f"Celery indisponible, envoi synchrone de l'email CP (demande {cp_request.id}): {e}")
            try:
                send_cp_status_email.run(
                    cp_request_id=cp_request.id,
                    approved=approved,
                )
            except Exception as sync_error:
                logger.warning(f"Échec envoi synchrone email CP (demande {cp_request.id}): {sync_error}")

    def reject_requests(self, request, queryset):
        """Refuse les demandes sélectionnées et notifie par email"""
        from django.db import transaction
        from django.utils import timezone

        rejected = 0
        errors = 0

        for cp_request in queryset.filter(status='pending'):
            try:
                with transaction.atomic():
                    cp_request.status = 'rejected'
                    cp_request.processed_at = timezone.now()
                    cp_request.save()

                    # Email de refus au candidat
                    self._send_status_email(cp_request, approved=False)

                    rejected += 1
            except Exception as e:
                errors += 1
                self.message_user(
                    request,
                    f"Erreur pour {cp_request.user.username}: {e}",
                    level='error',
                )

        if rejected:
            self.message_user(request, f"{rejected} demande(s) refusée(s), notification envoyée.")
        if errors:
            self.message_user(request, f"{errors} demande(s) en erreur (rien appliqué).", level='warning')

    reject_requests.short_description = "❌ Refuser les demandes sélectionnées"
