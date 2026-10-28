"""Pagination du catalogue (tâche 60, axe 2).

La pagination est **opt-in** : elle ne s'active que si le client envoie
`page` ou `page_size`. Sans ces paramètres, la réponse reste la liste
complète, comme avant — les versions actuelles de l'application continuent
donc de fonctionner pendant la migration côté Flutter.

Format paginé : `{count, next, previous, results}` (standard DRF).
"""
from rest_framework.pagination import PageNumberPagination


class CataloguePagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100

    def paginate_queryset(self, queryset, request, view=None):
        # Rétrocompatibilité : pas de `page`/`page_size` → liste complète.
        if (
            'page' not in request.query_params
            and 'page_size' not in request.query_params
        ):
            return None
        return super().paginate_queryset(queryset, request, view)
