"""
Permissions pour les endpoints de statistiques administrateur.

Un utilisateur est considéré administrateur si :
- il est staff ou superuser Django (gère l'admin Django), OU
- son UserProfile.groupe == 'ADMIN' (rôle métier du projet).

Les statistiques ne contiennent que des données agrégées et anonymisées :
aucune donnée personnelle n'est exposée (voir views).
"""
from rest_framework import permissions


class IsAdminStatisticsUser(permissions.BasePermission):
    """
    Autorise uniquement les administrateurs autorisés
    (staff/superuser Django ou profil groupe ADMIN).
    """

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if user.is_staff or user.is_superuser:
            return True
        profile = getattr(user, 'profile', None)
        return profile is not None and profile.groupe == 'ADMIN'
