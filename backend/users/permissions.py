from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission personnalisée pour permettre seulement aux propriétaires d'un objet de le modifier.
    """
    def has_object_permission(self, request, view, obj):
        # Permissions de lecture pour toutes les requêtes
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Permissions d'écriture seulement pour le propriétaire de l'objet
        return obj.user == request.user


class IsCPOrReadOnly(permissions.BasePermission):
    """
    Permission pour les Chefs de Promo (CP) seulement.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        return (request.user.is_authenticated and
                hasattr(request.user, 'profile') and
                request.user.profile.groupe in ['CP', 'ADMIN'])


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission pour les administrateurs seulement.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        return (request.user.is_authenticated and
                hasattr(request.user, 'profile') and
                request.user.profile.groupe == 'ADMIN')
