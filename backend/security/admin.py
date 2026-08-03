from django.contrib import admin
from .models import SecurityLog, AppVersion, ResumePricingConfig


@admin.register(SecurityLog)
class SecurityLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action_type', 'ip_address', 'timestamp']
    list_filter = ['action_type', 'timestamp']
    search_fields = ['user__username', 'description', 'ip_address']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'


@admin.register(AppVersion)
class AppVersionAdmin(admin.ModelAdmin):
    list_display = [
        'latest_version', 'minimum_version', 'force_update',
        'maintenance_mode', 'is_active', 'updated_at',
    ]
    list_filter = ['force_update', 'maintenance_mode', 'is_active']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = [
        ('📦 Versions', {
            'fields': [
                'latest_version', 'minimum_version',
                ('android_latest_version', 'ios_latest_version'),
            ],
        }),
        ('🛑 Mode Maintenance', {
            'fields': ['maintenance_mode', 'maintenance_message'],
        }),
        ('📲 Mise à jour forcée', {
            'fields': ['force_update', 'mandatory_update_message'],
        }),
        ('🔗 Stores', {
            'fields': ['play_store_url', 'app_store_url'],
        }),
        ('⚙️ Administration', {
            'fields': ['is_active', 'created_at', 'updated_at'],
        }),
    ]


@admin.register(ResumePricingConfig)
class ResumePricingConfigAdmin(admin.ModelAdmin):
    """
    Administration du prix minimum des résumés.
    Modifier la valeur ici est immédiat : backend + Flutter l'utilisent.
    """
    list_display = ['minimum_resume_price', 'is_active', 'updated_at', 'created_at']
    list_filter = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = [
        ('💰 Configuration du prix', {
            'fields': [
                'minimum_resume_price',
                'is_active',
            ],
            'description':
                'Définit le prix minimum autorisé pour la création de résumés. '
                'Tout prix inférieur sera refusé par le backend.',
        }),
        ('📅 Métadonnées', {
            'fields': ['created_at', 'updated_at'],
        }),
    ]
