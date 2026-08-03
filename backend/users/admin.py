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
    list_display = ['user', 'status', 'created_at', 'processed_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'user__email', 'motivation']
    readonly_fields = ['created_at', 'processed_at']
    actions = ['approve_requests', 'reject_requests']

    def approve_requests(self, request, queryset):
        """Approuve les demandes sélectionnées → l'utilisateur devient CP"""
        from django.utils import timezone
        approved = 0
        for cp_request in queryset.filter(status='pending'):
            try:
                profile = cp_request.user.profile
                profile.groupe = 'CP'
                profile.save()
                cp_request.status = 'approved'
                cp_request.processed_at = timezone.now()
                cp_request.save()
                approved += 1
            except Exception as e:
                self.message_user(request, f"Erreur pour {cp_request.user.username}: {e}", level='error')
        self.message_user(request, f"{approved} demande(s) approuvée(s). L'utilisateur est maintenant CP.")

    approve_requests.short_description = "✅ Approuver les demandes sélectionnées (l'utilisateur devient CP)"

    def reject_requests(self, request, queryset):
        """Refuse les demandes sélectionnées"""
        from django.utils import timezone
        rejected = queryset.filter(status='pending').update(
            status='rejected', processed_at=timezone.now()
        )
        self.message_user(request, f"{rejected} demande(s) refusée(s).")

    reject_requests.short_description = "❌ Refuser les demandes sélectionnées"
