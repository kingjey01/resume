from django.contrib import admin
from .models import Purchase, Service, Abonnement


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ['user', 'summary', 'amount', 'payment_method', 'status', 'created_at']
    list_filter = ['payment_method', 'status', 'created_at']
    search_fields = ['user__username', 'summary__titre', 'transaction_id']
    readonly_fields = ['created_at', 'completed_at']
    date_hierarchy = 'created_at'


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['nom', 'type', 'price', 'currency', 'duree_mois', 'is_active', 'created_at']
    list_filter = ['type', 'currency', 'is_active', 'created_at']
    search_fields = ['nom', 'description']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    list_editable = ['is_active']


@admin.register(Abonnement)
class AbonnementAdmin(admin.ModelAdmin):
    list_display = ['user', 'service', 'status', 'date_debut', 'date_fin', 'auto_renew', 'progress']
    list_filter = ['status', 'auto_renew', 'date_debut', 'date_fin']
    search_fields = ['user__username', 'service__nom']
    readonly_fields = ['created_at']
    date_hierarchy = 'date_debut'
    list_editable = ['status', 'auto_renew', 'progress']
