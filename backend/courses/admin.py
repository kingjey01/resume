from django.contrib import admin
from .models import *


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['nom', 'list_universites', 'list_filieres', 'list_promotions', 'created_at']
    list_filter = ['universites', 'filieres', 'promotions', 'created_at']
    search_fields = ['nom', 'description', 'universites__nom', 'filieres__nom', 'promotions__nom']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['universites', 'filieres', 'promotions']

    def list_universites(self, obj):
        return ", ".join(u.nom for u in obj.universites.all()) or "-"
    list_universites.short_description = "Universités"

    def list_filieres(self, obj):
        return ", ".join(f.nom for f in obj.filieres.all()) or "-"
    list_filieres.short_description = "Filières"

    def list_promotions(self, obj):
        return ", ".join(p.nom for p in obj.promotions.all()) or "-"
    list_promotions.short_description = "Promotions"

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('universites', 'filieres', 'promotions')


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ['course', 'date', 'professeur', 'created_at']
    list_filter = ['course', 'date', 'created_at']
    search_fields = ['course__nom', 'professeur']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'


@admin.register(Summary)
class SummaryAdmin(admin.ModelAdmin):
    list_display = ['titre', 'course', 'author_type', 'author_user', 'prix', 'is_free', 'created_at']
    list_filter = ['author_type', 'is_free', 'course', 'created_at']
    search_fields = ['titre', 'course__nom', 'author_user__username']
    readonly_fields = ['created_at', 'updated_at']
    # date_hierarchy = 'created_at'  # Désactivé pour éviter l'erreur de timezone
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('course', 'author_user', 'transcription')


@admin.register(Universite)
class UniversiteAdmin(admin.ModelAdmin):
    list_display = ['nom', 'adresse', 'list_filieres', 'created_at']
    search_fields = ['nom', 'adresse']
    readonly_fields = ['created_at']
    filter_horizontal = ['filieres']

    def list_filieres(self, obj):
        return ", ".join(f.nom for f in obj.filieres.all())
    list_filieres.short_description = "Filières"


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ['nom', 'annee', 'created_at']
    list_filter = ['annee', 'created_at']
    search_fields = ['nom']
    readonly_fields = ['created_at']


@admin.register(Filiere)
class FiliereAdmin(admin.ModelAdmin):
    list_display = ['nom', 'description', 'list_promotions', 'created_at']
    search_fields = ['nom', 'description']
    readonly_fields = ['created_at']
    filter_horizontal = ['promotions']

    def list_promotions(self, obj):
        return ", ".join(p.nom for p in obj.promotions.all())
    list_promotions.short_description = "Promotions"

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('promotions')


@admin.register(Transcription)
class TranscriptionAdmin(admin.ModelAdmin):
    list_display = ['session', 'status', 'confidence', 'duree_audio', 'created_at']
    list_filter = ['status', 'langue', 'created_at']
    search_fields = ['texte_transcription', 'session__course__nom', 'session__professeur']
    readonly_fields = ['created_at', 'updated_at']
    # date_hierarchy = 'created_at'  # Désactivé pour éviter l'erreur de timezone
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('session', 'session__course')


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ['titre', 'summary', 'status', 'generated_by_ai', 'created_at']
    list_filter = ['status', 'generated_by_ai', 'created_at']
    search_fields = ['titre', 'description', 'summary__titre']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('summary')


@admin.register(ExerciseQuestion)
class ExerciseQuestionAdmin(admin.ModelAdmin):
    list_display = ['exercise', 'question_text_short', 'correct_answer', 'order', 'created_at']
    list_filter = ['correct_answer', 'exercise__status', 'created_at']
    search_fields = ['question_text', 'exercise__titre']
    readonly_fields = ['created_at']
    ordering = ['exercise', 'order']
    
    def question_text_short(self, obj):
        return obj.question_text[:50] + "..." if len(obj.question_text) > 50 else obj.question_text
    question_text_short.short_description = "Question"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('exercise')


@admin.register(ExerciseAttempt)
class ExerciseAttemptAdmin(admin.ModelAdmin):
    list_display = ['exercise', 'student', 'score', 'completed_at']
    list_filter = ['score', 'completed_at']
    search_fields = ['exercise__titre', 'student__username']
    readonly_fields = ['completed_at', 'score']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('exercise', 'student')


@admin.register(ProfesseurFilieres)
class ProfesseurFilieresAdmin(admin.ModelAdmin):
    list_display = ['professeur', 'filiere', 'created_at']
    list_filter = ['filiere', 'created_at']
    search_fields = ['professeur__user__username', 'professeur__user__first_name', 'filiere__nom']
    readonly_fields = ['professeur', 'filiere', 'created_at']

    # Table unmanaged — pas d'ajout/modification/suppression depuis l'admin
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('professeur', 'professeur__user', 'filiere')


@admin.register(Professeur)
class ProfesseurAdmin(admin.ModelAdmin):
    list_display = ['user', 'telephone', 'specialite', 'universite', 'list_filieres', 'is_active', 'created_at']
    list_filter = ['is_active', 'universite', 'filieres', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'telephone', 'specialite']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['filieres']
    fieldsets = (
        (None, {
            'fields': ('user', 'telephone', 'specialite', 'is_active')
        }),
        ('Affiliation', {
            'fields': ('universite', 'filieres')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def list_filieres(self, obj):
        return ", ".join(f.nom for f in obj.filieres.all())
    list_filieres.short_description = "Filières"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'universite').prefetch_related('filieres')



