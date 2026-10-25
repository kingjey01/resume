"""
Invalidation du cache catalogue — tâche 60, axe 3.

Toute écriture sur une donnée partagée doit rendre les anciennes clés
inaccessibles. On incrémente la version globale du catalogue :

- `post_save` / `post_delete` sur les modèles du catalogue ;
- `m2m_changed` sur les relations many-to-many : un `post_save` ne se
  déclenche PAS quand on ajoute/retire une filière ou une promotion.

`invalider_catalogue()` vérifie `ENABLE_CATALOG_CACHE` et ne fait rien quand
le cache est désactivé (tests, avant validation, Redis indisponible).
"""
from django.db.models.signals import m2m_changed, post_delete, post_save

from .cache_catalogue import invalider_catalogue
from .models import Course, Filiere, Promotion, Summary, Universite


def _invalider(sender, **kwargs):
    invalider_catalogue()


for _modele in (Universite, Filiere, Promotion, Course, Summary):
    post_save.connect(
        _invalider,
        sender=_modele,
        dispatch_uid=f'catalog_save_{_modele.__name__}',
    )
    post_delete.connect(
        _invalider,
        sender=_modele,
        dispatch_uid=f'catalog_delete_{_modele.__name__}',
    )


def _invalider_m2m(sender, action, **kwargs):
    # Les actions pre_* arrivent avant la modification : on attend les post_*.
    if action in ('post_add', 'post_remove', 'post_clear'):
        invalider_catalogue()


for _relation in (
    Universite.filieres.through,
    Filiere.promotions.through,
    Course.universites.through,
    Course.filieres.through,
    Course.promotions.through,
):
    m2m_changed.connect(
        _invalider_m2m,
        sender=_relation,
        dispatch_uid=f'catalog_m2m_{_relation.__name__}',
    )
