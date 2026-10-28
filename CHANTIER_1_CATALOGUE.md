# Chantier 1 — Catalogue : diagnostic, optimisation et cache

> Document pédagogique rédigé le **28/10/2026**.
>
> Périmètre : catalogue de l’application **Muhtasari+ / RésuméPlus** — liste des cours, catalogue des résumés, référentiels (universités, filières, promotions), diagnostic SQL, pagination et cache Redis.
>
> Stack observée : **Django 4.2.7**, **DRF 3.14**, **Celery 5.3.4**, **Redis 5.0.1**, SQLite en local, **PostgreSQL** en production, Apache + **mod_wsgi** en production, Flutter côté client.

---

## 1. Résumé exécutif

Le catalogue souffrait de deux problèmes majeurs :

1. **N+1 SQL** : chaque cours et chaque résumé déclenchait plusieurs requêtes individuelles.
2. **Absence de pagination côté serveur** : l’API renvoyait toute la table, et Flutter téléchargeait tout avant de filtrer localement.

Après les optimisations :

| Endpoint | Avant | Après | Gain |
|---|---:|---:|---:|
| `GET /api/course-list/` (14 cours) | **146 requêtes** | **9 requêtes** | −94 % |
| `GET /api/summaries/` (10 résumés) | **70 requêtes** | **5 requêtes** | −93 % |
| `GET /api/summaries/gratuits/` (3) | **20 requêtes** | **4 requêtes** | −80 % |
| `GET /api/courses/universites/` (5) | **36 requêtes** | **3 requêtes** | −92 % |
| `GET /api/courses/filieres/` (6) | **7 requêtes** | **2 requêtes** | −71 % |
| `GET /api/courses/universites/{id}/filieres/` | **8 requêtes** | **3 requêtes** | −63 % |
| `GET /api/courses/promotions/{id}/filieres/` | **8 requêtes** | **3 requêtes** | −63 % |

Mesure de production (Silk) sur `course-list` : **1 155 ms → 248 ms**, avec **0 ms en base** sur un HIT de cache.

Tests : **24 tests backend**, **89 tests Flutter**, tous verts.

---

## 2. Architecture et contexte

### 2.1 Les endpoints concernés

| Écran / donnée | Endpoint | Vue |
|---|---|---|
| Accueil — cours | `GET /api/course-list/` | `CourseListCreateView` |
| Catalogue — résumés | `GET /api/summaries/` | `SummaryListCreateView` |
| Résumés gratuits | `GET /api/summaries/gratuits/` | `SummaryGratuitsView` |
| Résumés achetés | `GET /api/summaries/achetes/` | `SummaryAchetesView` |
| Référentiels | `/api/courses/universites/`, `/filieres/`, `/promotions/` | ViewSets |
| Actions | `/universites/{id}/filieres/`, `/promotions/{id}/filieres/`, `/filieres/{id}/promotions/` | actions DRF |

### 2.2 Les modèles

- `Course` : M2M `universites`, `filieres`, `promotions` + FK `created_by`.
- `Summary` : FK `course`, `professeur`, `session`, `transcription`, `author_user`.
- `Purchase` : trace d’achat (`user`, `summary`, `status='completed'`).
- `Universite` / `Filiere` / `Promotion` : relations M2M imbriquées.

### 2.3 Deux environnements différents

- **Local** : SQLite (`resume_backend.settings`), Redis local, données de test générées par `seed_production`.
- **Production** : PostgreSQL (`backend/settings.py` sur le serveur), Redis, Apache + mod_wsgi, Python 3.9.

Le premier piège rencontré : le service systemd `resume_plus.service` du dépôt **n’est pas** ce qui sert la production. Le vhost Apache pointe vers :

```apache
WSGIScriptAlias / /home/jey/resumecours.gestionhospitaliare.site/backend/backend/wsgi.py
python-path=/home/jey/resumecours.gestionhospitaliare.site/backend
```

Il faut copier les fichiers **dans ce dossier**, et redémarrer Apache (`stop`/`start`), pas `resume_plus`.

---

## 3. Axe 1 — Diagnostic et interface HTML

### 3.1 Le choix de l’outil : Silk plutôt que django-debug-toolbar

Le backend est une **API JSON** consommée par Flutter. `django-debug-toolbar` injecte son panneau dans une réponse HTML : sur une réponse JSON, il ne s’affiche pas. Il aurait fallu activer le `BrowsableAPIRenderer` et gérer l’authentification JWT dans le navigateur.

**`django-silk`** enregistre chaque requête (y compris les appels API), les requêtes SQL, leur durée, et expose une interface HTML sur `/silk/`. C’est l’outil adapté.

### 3.2 Configuration retenue

- `ENABLE_SILK` : interrupteur indépendant de `DEBUG` (par défaut `DEBUG` en local, `False` en production).
- `SILKY_AUTHENTICATION`, `SILKY_AUTHORISATION`, `SILKY_PERMISSIONS` : accès réservé aux **superusers**.
- `LOGIN_URL = '/admin/login/'` : sans cela, Silk redirige vers `/accounts/login/` (inexistant) → 404.
- `django-silk` uniquement dans `requirements-dev.txt`, jamais dans `requirements.txt`.

### 3.3 Ce que Silk a montré

Sur `GET /api/courses/course-list/` :

- **14 cours**, **146 requêtes SQL**, **153 ms en base**, **1 155 ms au total**.

Décomposition des 146 requêtes : pour chaque cours, le serializer faisait :
- 3 requêtes M2M pour les noms (`universites_noms`, `filieres_noms`, `promotions_noms`) ;
- 3 `.first()` (`universite_nom`, `filiere_nom`, `promotion_nom`) ;
- 1 `.exists()` pour `has_generic_summary` ;
- 3 requêtes pour les champs M2M natifs de DRF.

≈ **10 requêtes/cours** × 14 = 140, plus l’authentification et la vue = **146**.

Sur `/api/summaries/` : **70 requêtes pour 10 résumés**, notamment à cause de `Purchase.objects.filter(...).exists()` exécuté **par résumé**.

### 3.4 Leçon sur l’instrumentation

Silk a un coût. Mesuré avec `CaptureQueriesContext` :

| Contexte | `course-list` |
|---|---:|
| Silk désactivé | **146 requêtes** |
| Silk activé | **462 requêtes** (les écritures de Silk sont comptées par le contexte de test) |

L’interface Silk, elle, rapporte bien **146**. Il faut donc comparer des mesures prises avec le même outil, et ne pas confondre « requêtes applicatives » et « requêtes totales du processus ».

---

## 4. Axe 2 — Optimisations

### 4.1 Pourquoi commencer par le N+1 avant le cache

Mettre en cache une requête lente ne résout rien : le premier appel (MISS) et chaque invalidation restent lents. On optimise d’abord la requête, **ensuite** on cache le résultat optimisé.

### 4.2 `course-list` : prefetch + annotation

Problème : les champs calculés du `CourseSerializer` interrogeaient la base par cours.

Solution dans `courses/views.py` :

```python
def _courses_optimises():
    return Course.objects.prefetch_related(
        'universites', 'filieres', 'promotions',
    ).annotate(
        a_un_resume_generique=Exists(
            Summary.objects.filter(course=OuterRef('pk'), author_type='ai')
        ),
    )
```

Et dans `CourseSerializer` :

- `[u.nom for u in obj.universites.all()]` lit le cache de prefetch ;
- `next(iter(obj.universites.all()), None)` remplace `.first()` ;
- `get_has_generic_summary` lit l’annotation, avec repli `.exists()`.

**Pourquoi `next(iter(...))` plutôt que `.first()` ?** `.first()` ajoute un `ORDER BY ... LIMIT 1` et peut contourner le cache de `prefetch_related`. `next(iter(...))` itère la liste déjà chargée.

Résultat : **146 → 9 requêtes** ; en production, **1 155 ms → 248 ms**.

### 4.3 `summaries` : select_related + un seul set d’achats

Deux causes :

1. les relations (`course`, `author_user`, `professeur`, `session`, `transcription`, `course.filieres`) étaient chargées par résumé ;
2. `to_representation` faisait `Purchase.exists()` par résumé.

Solution :

```python
def _summaries_optimises(queryset=None):
    queryset = queryset if queryset is not None else Summary.objects.all()
    return queryset.select_related(
        'course', 'author_user', 'professeur', 'professeur__user',
        'professeur__universite', 'session',
        'session__professeur_fk', 'session__professeur_fk__user',
        'transcription',
    ).prefetch_related('course__filieres')
```

Et un mixin qui calcule **une seule fois** les IDs achetés :

```python
class SummaryPurchasedIdsMixin:
    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.user.is_authenticated:
            context['purchased_ids'] = set(
                Purchase.objects.filter(
                    user=self.request.user,
                    status='completed',
                    summary__isnull=False,
                ).values_list('summary_id', flat=True)
            )
        return context
```

Le serializer teste `instance.id in purchased_ids` au lieu de requêter la base pour chaque ligne.

Résultat : **70 → 5 requêtes** pour 10 résumés ; **20 → 4** pour les résumés gratuits.

### 4.4 Référentiels : prefetch des relations imbriquées

- `UniversiteViewSet.queryset = Universite.objects.prefetch_related('filieres__promotions')`
- `FiliereViewSet.queryset = Filiere.objects.prefetch_related('universites')`
- action `PromotionViewSet.filieres` : `promotion.filieres.prefetch_related('promotions')`

Résultat : universités **36 → 3**, filières **7 → 2**, actions **8 → 3**.
Le seul endpoint qui passe de 2 à 3 requêtes (`filieres/{id}/promotions/`) paie le prefetch `universites` du viewset, utile pour la liste : c’est un compromis constant, pas un N+1.

### 4.5 Pagination backend

Deux contraintes :

- ne pas casser l’application existante ;
- ne pas filtrer uniquement la page courante.

`CataloguePagination` est donc **opt-in** :

```python
def paginate_queryset(self, queryset, request, view=None):
    if 'page' not in request.query_params and 'page_size' not in request.query_params:
        return None          # ancienne liste complète
    return super().paginate_queryset(queryset, request, view)
```

- `page_size` par défaut : 50 ; maximum : 100.
- Format : `{count, next, previous, results}`.
- Filtres serveur ajoutés via `SummaryFilter` : `search`, `is_free`, `professeur_nom`, `date_debut`, `date_fin`, `filiere`, `filiere_nom`, `course`, `author_type`.

**Pourquoi les filtres doivent être serveur ?** L’écran Flutter filtrait localement après avoir téléchargé toute la liste. Avec la pagination, un filtre local ne verrait que la page courante et donnerait des résultats faux.

### 4.6 Pagination Flutter

- `SummariesPage` + `ApiService.getSummariesPage` : `page`, `page_size`, `search`, `is_free`, `professeur_nom`, dates, `course`, `filiere`.
- `SummaryFeedNotifier` : un état par onglet, `loadMore`, protection contre les réponses obsolètes via une génération.
- `AllSummariesScreen` : quatre onglets paginés, bouton **« Charger plus »**, recherche avec debounce, filtres serveur.
- `HomeScreen` : ne charge plus que **10 résumés récents** pour le carrousel de 4 cartes.
- `CourseSummariesScreen` / `FiliereSummariesScreen` : pagination serveur `course=<id>` / `filiere=<id>` ou `filiere_nom`, « Charger plus », pull-to-refresh.

**Rétrocompatibilité** : `getSummariesPage` accepte encore une réponse `List` (ancien backend) et la traite comme une page unique. L’app peut donc être déployée avant ou après le backend sans casser.

### 4.7 Tests ajoutés

- `CourseListNoNPlusOneTest` : 20 cours → ≤ 20 requêtes applicatives.
- `SummaryListNoNPlusOneTest` : 20 résumés → ≤ 20 requêtes et `is_purchased` correct.
- `ReferenceDataNoNPlusOneTest` : 5 endpoints de référentiel.
- `CataloguePaginationTest` : pages successives, liste complète sans paramètres, filtres serveur, pagination des cours.
- `CatalogCacheTest` / `ReferenceEndpointsCacheTest` / `CourseListCacheTest` : version, get/set, panne Redis, HIT/MISS, invalidation, isolation des cohortes.

---

## 5. Axe 3 — Cache Redis

### 5.1 Pourquoi Redis

Le cache doit être **partagé entre les processus** Gunicorn/mod_wsgi. `LocMemCache` est propre à un processus : chaque worker aurait sa copie. Redis est centralisé, avec TTL natif.

### 5.2 Ce qui est un bon candidat

| Donnée | Lecture | Écriture | Verdict |
|---|---|---|---|
| Universités / Filières / Promotions | forte | très faible | ✅ excellent |
| Liste des cours d’une cohorte | forte | faible | ✅ très bon |
| Résumés gratuits | forte | faible | ✅ bon |
| Résumés avec `is_purchased` / texte tronqué | forte | faible | ❌ **propre à l’utilisateur** → pas de clé partagée |
| Résumés achetés | forte | faible | ❌ par utilisateur |
| Statistiques temps réel | moyenne | forte | ❌ |

**Règle d’or** : on ne met en cache que ce qui est **identique pour plusieurs utilisateurs**. `is_purchased`, le texte tronqué et le rôle sont propres à l’utilisateur.

### 5.3 Configuration

Un alias Redis **dédié** au catalogue :

```python
CACHE_REDIS_URL = config('CACHE_REDIS_URL', default='redis://127.0.0.1:6379/1')
ENABLE_CATALOG_CACHE = config('ENABLE_CATALOG_CACHE', default=False, cast=bool)

CACHES['catalog'] = {
    'BACKEND': 'django.core.cache.backends.redis.RedisCache',
    'LOCATION': CACHE_REDIS_URL,
    'TIMEOUT': 600,
    'KEY_PREFIX': 'muhtasari',
    'OPTIONS': {'socket_connect_timeout': 0.5},
}
```

- DB Redis **1** pour le cache, DB **0** pour Celery : les deux ne se mélangent plus.
- `ENABLE_CATALOG_CACHE` permet un déploiement progressif et un retour arrière immédiat.
- TTL par défaut 10 min ; 1 h pour les référentiels.

**Bug réel corrigé** : `OPTIONS = {'CONNECTION_POOL_KWARGS': {...}}` est une option de `django-redis`, **pas** du backend natif de Django 4.2. Chaque accès levait une erreur attrapée silencieusement, et le cache/rate limiting retombait sur LocMem. La bonne option est `socket_connect_timeout` directement.

### 5.4 Clés et version d’invalidation

```python
CATALOG_VERSION_KEY = 'catalog:version'

def cle_catalogue(*parties):
    return ':'.join(['catalog', str(version_catalogue())] + [str(p) for p in parties])
```

Exemple de clé Redis réelle :

```
muhtasari:1:catalog:1:courses:admin:list:/api/course-list/
```

- `muhtasari` : `KEY_PREFIX` ;
- `1` : version interne du cache Django ;
- `catalog` : namespace de notre helper ;
- `1` : **notre** version d’invalidation ;
- `courses:admin:list:...` : donnée + scope + query string.

Quand une donnée change, on **incrémente** la version globale. Les anciennes clés deviennent inaccessibles et expirent via leur TTL — pas besoin de `delete_pattern` (non portable et coûteux).

Signaux d’invalidation :

- `post_save` / `post_delete` sur `Universite`, `Filiere`, `Promotion`, `Course`, `Summary` ;
- **`m2m_changed`** sur les relations M2M (un `post_save` ne voit pas `filiere.promotions.add(...)`).

### 5.5 Repli silencieux

`cache_get_safe` / `cache_set_safe` attrapent toute erreur Redis :

- `get` renvoie `None` → la vue recalcule depuis la base ;
- `set` ne fait rien ;
- **jamais de 500** à cause du cache.

### 5.6 Résultats mesurés

| Endpoint | 1er appel (MISS) | 2e appel (HIT) |
|---|---:|---:|
| `/api/courses/universites/` | 3 requêtes | **0 requête** |
| `/api/courses/filieres/` | 2 | **0** |
| `/api/courses/promotions/` | 1 | **0** |
| `/api/course-list/` | 9 | **~5 requêtes d’auth/permission** |

Sur un HIT de `course-list`, les requêtes restantes sont l’authentification JWT, le profil et ses 3 FK : elles ont lieu **avant** le cache et ne peuvent pas être partagées entre utilisateurs. La requête `courses_course` et les prefetch ne sont plus exécutés.

Clés vérifiées en production :

```
muhtasari:1:catalog:version
muhtasari:1:catalog:1:refs:universites:list:/api/courses/universites/
```

### 5.7 Ce qui n’est volontairement pas caché

La liste des résumés contient `is_purchased` et un `texte_resume` tronqué selon l’acheteur. Une clé partagée fuiterait ces informations entre utilisateurs. On la laisse donc hors du cache pour l’instant.

Deux évolutions possibles plus tard :

1. cacher une **base partagée** par cohorte/page, puis superposer `is_purchased` et la troncature par requête ;
2. ajouter un endpoint de **comptage** pour le badge « Résumés » (qui télécharge encore toute la liste).

---

## 6. Bonnes pratiques appliquées

1. **Mesurer avant de modifier** : baseline Silk, puis comparaison après chaque changement.
2. **Une optimisation à la fois** : N+1 cours, puis résumés, puis référentiels, puis pagination, puis cache.
3. **Le backend fait autorité** : filtres, pagination et cache sont côté serveur.
4. **`select_related`** pour les FK, **`prefetch_related`** pour les M2M.
5. **Éviter `.first()` sur un manager préchargé** : `next(iter(...))`.
6. **Une requête pour N lignes**, pas N requêtes : `Exists`/`set` d’IDs plutôt que `.exists()` par ligne.
7. **Pagination opt-in** pour ne pas casser les clients existants.
8. **Filtres serveur** avant de paginer.
9. **Cache uniquement les données partagées** ; jamais `is_purchased` dans une clé commune.
10. **TTL explicite + version d’invalidation** ; le TTL est un filet, pas la stratégie principale.
11. **Séparer le cache du broker Celery** (DB Redis distincte).
12. **Échouer ouvert** : si Redis tombe, servir depuis la base.
13. **Interrupteur de déploiement** (`ENABLE_CATALOG_CACHE`) pour activer/désactiver sans redéploiement.
14. **Tests de non-régression** sur les comptes de requêtes, pas seulement sur le contenu.
15. **Déployer backend puis app** ; l’app tolère un backend non paginé.
16. **Vérifier le chemin WSGI réel** et redémarrer Apache complètement (`stop`/`start`), pas seulement `graceful`.

---

## 7. Pièges rencontrés et leçons

- **`CONNECTION_POOL_KWARGS`** : option de `django-redis`, pas de Django 4.2 → cache silencieusement inutilisé.
- **Silk compte ses propres requêtes** dans `CaptureQueriesContext` ; l’UI Silk et le contexte de test ne donnent pas le même total.
- **Migrations `security` manquantes** (`0002-0004`) : la chaîne `0005` dépendait d’un nœud absent ; impossible de créer la base locale. Récupérées depuis le serveur.
- **Migration `0029` PostgreSQL-only** : `ADD COLUMN IF NOT EXISTS` n’existe pas en SQLite ; rendue compatible par une branche `sqlite`.
- **Déploiement dans le mauvais dossier** : Apache servait `/home/jey/.../backend/backend/wsgi.py`, pas le clone de travail.
- **`apachectl graceful`** ne recharge pas toujours les processus mod_wsgi : arrêt/démarrage complet nécessaire.
- **`X-Catalog-Cache` absent** : c’était le symptôme d’un ancien `courses/views.py`, pas d’un cache désactivé (l’en-tête `MISS` est ajouté même quand le cache est off).
- **Les filtres client-side sont incompatibles avec la pagination** : ils doivent passer par le serveur.
- **Les fakes de test** doivent suivre le nouveau contrat (`{results: [...]}`), sinon les tests cassent alors que le code est bon.
- **Une pagination standard DRF fait un COUNT par page** : acceptable ici ; à remplacer par une pagination sans COUNT si les mesures le justifient.
- **Le COUNT et l’auth restent visibles sur un HIT** : ne pas promettre « 0 requête » pour les endpoints authentifiés ; parler de « 0 requête métier ».

---

## 8. Déploiement en production

### 8.1 Backend

Fichiers concernés par le chantier :

```
backend/courses/pagination.py            (nouveau)
backend/courses/cache_catalogue.py       (nouveau)
backend/courses/cache_signals.py         (nouveau)
backend/courses/apps.py
backend/courses/views.py
backend/courses/serializers.py
backend/resume_backend/settings.py               (local)
backend/resume_backend/settings_production.py    (ou backend/settings.py sur le serveur)
backend/resume_backend/urls.py                   (route Silk, optionnelle)
```

- **Aucune migration** pour la pagination ou le cache.
- Variables `.env` :

```env
CACHE_REDIS_URL=redis://127.0.0.1:6379/1
ENABLE_CATALOG_CACHE=True
ENABLE_SILK=False
```

- Vérifier que le module de settings chargé est bien celui modifié (`backend/wsgi.py` → `DJANGO_SETTINGS_MODULE`).
- Copier dans `/home/jey/resumecours.gestionhospitaliare.site/backend/`, puis :

```bash
python manage.py check
sudo /usr/local/apache/bin/apachectl stop
sudo /usr/local/apache/bin/apachectl start
```

### 8.2 Vérifications

```bash
curl -i https://.../api/courses/universites/   # 1er : MISS, 2e : HIT
curl -i -H "Authorization: Bearer $TOKEN" \
  "https://.../api/summaries/?page=1&page_size=2"
curl -i -H "Authorization: Bearer $TOKEN" \
  "https://.../api/course-list/?page=1&page_size=2"
redis-cli -n 1 keys 'muhtasari:*'
```

### 8.3 Retour arrière

- Cache : `ENABLE_CATALOG_CACHE=False` + redémarrage → comportement normal, sans toucher au code.
- Pagination : les clients qui n’envoient pas `page`/`page_size` reçoivent la liste complète.
- Code : redéployer la version précédente et redémarrer Apache.

---

## 9. Prochaines étapes (sans les exécuter)

### Chantier 2 — IA / Celery

- Sortir les générations longues (résumés, QCM) de la requête HTTP.
- Idempotence des tâches, retries, files dédiées, priorités.
- Suivi des coûts DeepSeek/Deepgram par génération.
- Supervision Celery (Flower/Sentry), alertes sur les tâches bloquées.
- Quotas QCM déjà en place : à relier aux métriques de coût.

### Chantier 3 — Capacité et sécurité

- Endpoint de comptage pour le badge « Résumés » (éviter `getSummaries()` complet).
- Pagination des derniers écrans qui chargent encore tout (validation, achats, exercices).
- Pagination sans COUNT si les mesures le justifient.
- Index PostgreSQL à valider par `EXPLAIN` : `Summary(is_validated, created_at)`, `Summary(course, author_type)`, `Purchase(user, status, summary)`.
- Cache des résumés par cohorte/page avec surcouche `is_purchased`, si les mesures le justifient.
- Verrou anti-« cache stampede » sur les clés très demandées.
- Durcissement : `DEBUG=False`, `CORS_ALLOW_ALL_ORIGINS=False`, secrets hors dépôt, supervision, sauvegardes, tests de charge.
- Révision de la configuration Apache/mod_wsgi (processus, threads, timeouts) et du pooling PostgreSQL.

---

## 10. Fichiers et commits du chantier

| Commit | Contenu |
|---|---|
| `a87df31` | Silk + migrations locales complètes |
| `76dda5d` | N+1 liste des cours |
| `2921d05` | N+1 liste des résumés |
| `0525c40` | N+1 référentiels |
| `2b5023e` | Infrastructure cache catalogue |
| `82a902e` | Cache des référentiels |
| `596c8c5` | Cache de la liste des cours |
| `32e2b84` | Pagination + filtres serveur |
| `18b0c12` | Pagination Flutter des résumés |
| `7e1706f` | Pagination écrans cours/filière |

Branche : `feat/tache60-catalogue-perf` — `main` à jour au moment de la rédaction.

---

## 11. Ce que je dois retenir

1. **Un N+1 ne se voit pas dans le code, il se mesure.** Silk ou `CaptureQueriesContext` transforme une intuition en chiffre.
2. **Le nombre de requêtes est une métrique de conception**, pas un détail : 10 requêtes par ligne suffisent à rendre une page inutilisable à l’échelle.
3. **`select_related` et `prefetch_related` ne sont pas interchangeables** : FK vs M2M.
4. **Une bonne clé de cache contient toujours un scope** (cohorte, version, query string), sinon deux utilisateurs finissent par voir les données de l’autre.
5. **Le cache ne remplace pas l’optimisation** : cache ce qui est déjà rapide.
6. **L’invalidation est plus difficile que le cache lui-même** : version + TTL + signaux M2M.
7. **Les filtres côté client et la pagination sont incompatibles** : dès qu’on pagine, les filtres passent côté serveur.
8. **La compatibilité ascendante se prépare** : pagination opt-in, fallback liste, déploiement backend avant app.
9. **Un déploiement n’est pas un `git push`** : chemin WSGI, module de settings, redémarrage complet, vérification d’un en-tête de diagnostic.
10. **Chaque optimisation mérite un test de non-régression mesurable**, pas seulement un test fonctionnel.
