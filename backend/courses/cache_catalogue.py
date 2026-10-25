"""
Cache du catalogue — tâche 60, axe 3.

Principe : les référentiels (universités, filières, promotions) et les listes
de cours sont lus par beaucoup d'utilisateurs et changent rarement. On stocke
leur représentation sérialisée dans Redis, avec :

- une **version globale** (`catalog:version`) incluse dans chaque clé. Un
  signal incrémente cette version dès qu'une donnée partagée change : toutes
  les anciennes clés deviennent inaccessibles et expirent via leur TTL ;
- un **TTL** explicite (filet de sécurité) ;
- un **repli silencieux** : si Redis est indisponible, on renvoie `None` et
  l'appelant recalcule depuis la base. Le site ne tombe jamais à cause du cache.

L'interrupteur `ENABLE_CATALOG_CACHE` permet d'activer le cache sans
redéploiement et de le laisser désactivé dans les tests/avant validation.

Le backend `catalog` a `KEY_PREFIX = "muhtasari"` : la clé Redis réelle sera
`muhtasari:catalog:<version>:...`.
"""
import logging

from django.conf import settings
from django.core.cache import caches

logger = logging.getLogger(__name__)

CATALOG_VERSION_KEY = 'catalog:version'


def _actif():
    return getattr(settings, 'ENABLE_CATALOG_CACHE', False)


def _cache():
    """Cache dédié au catalogue, avec repli si l'alias n'existe pas."""
    try:
        return caches['catalog']
    except Exception:
        return caches['default']


def version_catalogue():
    """Version courante du catalogue.

    En cas d'indisponibilité de Redis, on renvoie 1 : les appels `get/set`
    échoueront de toute façon silencieusement et la base servira la réponse.
    """
    if not _actif():
        return 1

    cache = _cache()
    try:
        version = cache.get(CATALOG_VERSION_KEY)
        if version is None:
            cache.add(CATALOG_VERSION_KEY, 1, timeout=None)
            version = cache.get(CATALOG_VERSION_KEY) or 1
        return version
    except Exception as exc:
        logger.warning('Cache catalogue indisponible (version) : %s', exc)
        return 1


def invalider_catalogue():
    """Invalide TOUTES les clés du catalogue en incrémentant la version."""
    if not _actif():
        return

    cache = _cache()
    try:
        try:
            cache.incr(CATALOG_VERSION_KEY)
        except ValueError:
            # Clé absente (premier passage) : on initialise à la version 2,
            # la version 1 n'ayant jamais été écrite explicitement.
            cache.set(CATALOG_VERSION_KEY, 2, timeout=None)
    except Exception as exc:
        logger.warning('Cache catalogue indisponible (invalidation) : %s', exc)


def cle_catalogue(*parties):
    """Construit une clé versionnée : `catalog:<version>:<partie>...`."""
    morceaux = ['catalog', str(version_catalogue())]
    morceaux.extend(str(partie) for partie in parties)
    return ':'.join(morceaux)


def cache_get_safe(cle):
    """Lit le cache ; `None` si absent, désactivé ou Redis indisponible."""
    if not _actif():
        return None
    try:
        return _cache().get(cle)
    except Exception as exc:
        logger.warning('Cache catalogue indisponible (get %s) : %s', cle, exc)
        return None


def cache_set_safe(cle, valeur, timeout=600):
    """Écrit le cache sans jamais faire échouer la requête."""
    if not _actif():
        return
    try:
        _cache().set(cle, valeur, timeout=timeout)
    except Exception as exc:
        logger.warning('Cache catalogue indisponible (set %s) : %s', cle, exc)
