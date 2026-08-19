from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission personnalisée pour permettre seulement aux propriétaires d'un objet de le modifier.
    """

    def has_object_permission(self, request, view, obj):
        # Permissions de lecture pour toutes les requêtes.
        # Nous autorisons toujours les requêtes GET, HEAD ou OPTIONS.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Permissions d'écriture seulement pour le propriétaire de l'objet.
        return obj.author_user == request.user


class CanCreateSummary(permissions.BasePermission):
    """
    Permission pour créer des résumés - seulement CP et ADMIN
    """
    
    def has_permission(self, request, view):
        if request.method == 'POST':
            if not request.user.is_authenticated:
                return False
            
            # Vérifier si l'utilisateur a un profil
            if not hasattr(request.user, 'profile'):
                return False
                
            # Seuls CP et ADMIN peuvent créer des résumés
            return request.user.profile.can_create_summary()
        
        return True


class CanAccessSummary(permissions.BasePermission):
    """
    Permission pour accéder aux résumés selon le rôle
    """
    
    def has_permission(self, request, view):
        """Permission pour les vues de liste"""
        if not request.user.is_authenticated:
            return False
            
        if not hasattr(request.user, 'profile'):
            return False
            
        # Tous les utilisateurs authentifiés avec profil peuvent voir la liste
        return True
    
    def has_object_permission(self, request, view, obj):
        """Permission pour les objets individuels"""
        if not request.user.is_authenticated:
            return False
            
        if not hasattr(request.user, 'profile'):
            return False
            
        user_profile = request.user.profile
        
        # CP et ADMIN ont accès gratuit à tous les résumés
        if user_profile.has_free_access():
            return True
            
        # ETUDIANT peut voir les résumés gratuits ou ceux qu'il a achetés
        if obj.is_free:
            return True

        # Vérifier si l'étudiant a acheté ce résumé
        from payments.models import Purchase
        has_purchased = Purchase.objects.filter(
            user=request.user,
            summary=obj,
            status='completed'
        ).exists()
        return has_purchased


def user_can_access_summary(user, summary):
    """
    Même logique que CanAccessSummary.has_object_permission :
    accès gratuit (CP/ADMIN) OU résumé gratuit OU achat 'completed'.
    Réutilisé par les endpoints QCM pour interdire le lancement d'un
    QCM sur un résumé non acheté (tache_bug_etudiant.md, point 2).
    """
    if not user or not user.is_authenticated:
        return False
    if not hasattr(user, 'profile'):
        return False
    # CP et ADMIN ont accès gratuit à tous les résumés
    if user.profile.has_free_access():
        return True
    if summary.is_free:
        return True
    # Étudiant : uniquement si le résumé a été acheté (paiement 'completed')
    from payments.models import Purchase
    return Purchase.objects.filter(
        user=user,
        summary=summary,
        status='completed'
    ).exists()


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission pour les opérations d'administration
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
            
        if not request.user.is_authenticated:
            return False
            
        if not hasattr(request.user, 'profile'):
            return False
            
        return request.user.profile.is_admin


class CanAssignRole(permissions.BasePermission):
    """
    Permission pour assigner des rôles - seulement ADMIN
    """
    
    def has_permission(self, request, view):
        if request.method == 'POST' and 'groupe' in request.data:
            requested_role = request.data.get('groupe')
            
            # Seul un admin peut assigner le rôle CP
            if requested_role == 'CP':
                if not request.user.is_authenticated:
                    return False
                if not hasattr(request.user, 'profile'):
                    return False
                return request.user.profile.is_admin
                
        return True


class HasUniversityAccess(permissions.BasePermission):
    """
    Permission stricte basée sur Université → Promotion → Filière
    Contrôle l'accès aux cours, résumés et sessions
    """
    
    def has_permission(self, request, view):
        """Vérification au niveau de la vue"""
        if not request.user.is_authenticated:
            return False
            
        if not hasattr(request.user, 'profile'):
            return False
        
        profile = request.user.profile
        
        # Vérifier que l'utilisateur a bien une université, promotion et filière
        if not profile.universite or not profile.promotion or not profile.filiere:
            return False
            
        return True
    
    def has_object_permission(self, request, view, obj):
        """Vérification au niveau de l'objet"""
        if not request.user.is_authenticated:
            return False

        if not hasattr(request.user, 'profile'):
            return False

        profile = request.user.profile

        # Pour les objets Course (M2M)
        if hasattr(obj, 'universites') and hasattr(obj, 'promotions') and hasattr(obj, 'filieres'):
            return (
                obj.universites.filter(id=profile.universite_id).exists() and
                obj.promotions.filter(id=profile.promotion_id).exists() and
                obj.filieres.filter(id=profile.filiere_id).exists()
            )

        # Pour les objets Summary ou Session (via course M2M)
        if hasattr(obj, 'course'):
            course = obj.course
            return (
                course.universites.filter(id=profile.universite_id).exists() and
                course.promotions.filter(id=profile.promotion_id).exists() and
                course.filieres.filter(id=profile.filiere_id).exists()
            )

        return False


class CanModifyObject(permissions.BasePermission):
    """
    Permission pour modifier un objet - seulement le créateur ou admin
    """
    
    def has_object_permission(self, request, view, obj):
        # Lecture autorisée si l'utilisateur a accès (géré par HasUniversityAccess)
        if request.method in permissions.SAFE_METHODS:
            return True
        
        if not request.user.is_authenticated:
            return False
            
        if not hasattr(request.user, 'profile'):
            return False
        
        # Admin peut tout modifier
        if request.user.profile.is_admin:
            return True
        
        # Le créateur peut modifier son propre contenu
        if hasattr(obj, 'author_user') and obj.author_user == request.user:
            return True
            
        return False


class HasActiveSubscription(permissions.BasePermission):
    """
    Permission pour exiger un abonnement actif au service Exercices.
    Vérifie spécifiquement l'abonnement exercice, pas n'importe quel abonnement.
    """
    message = "Votre abonnement a expiré. Veuillez renouveler votre abonnement pour accéder à cette fonctionnalité."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if not hasattr(request.user, 'profile'):
            return False

        from payments.models import Service, Abonnement
        from django.utils import timezone

        now = timezone.now()

        # 1) Essayer le service QCM/Exercices nommé (compatibilité)
        exercise_service = Service.objects.filter(
            nom__icontains="qcm", is_active=True
        ).first()

        if exercise_service:
            has_qcm_sub = Abonnement.objects.filter(
                user=request.user,
                service=exercise_service,
                status='active',
                date_debut__lte=now,
                date_fin__gte=now
            ).exists()
            if has_qcm_sub:
                return True

        # 2) Fallback : TOUT abonnement actif donne accès aux exercices
        return Abonnement.objects.filter(
            user=request.user,
            status='active',
            date_debut__lte=now,
            date_fin__gte=now
        ).exists()
