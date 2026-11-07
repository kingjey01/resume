# Audit SQL / N+1 / cache — avant le chantier 2

> **Mise à jour du 29/10/2026** : après validation, les **corrections P0 audio**, les **corrections P1/P2**, l'**adaptation Flutter** et la **P3 (dispenses)** ont été appliquées. Résultats : file audio **73 → 6**, audio détaillé **73 → 4**, sessions ViewSet **66 → 7** ; tentatives personnalisées **7 → 2** ; notifications **4 → 3**. La validation, les deux historiques de tentatives et les dispenses utilisent désormais la pagination serveur côté application. Voir les sections de corrections en fin de document.
>
> Le reste du document est l’**audit initial**, réalisé avant toute modification.
> Mesures réalisées le 29/10/2026 sur la base locale (SQLite), avec `CaptureQueriesContext`, Silk désactivé, et des volumes de test :
> 10 résumés, 4 professeurs, 5 dispenses, 5 tentatives classiques, 5 tentatives personnalisées, 20 notifications, 10 sessions audio.
>
> Les nombres de requêtes ci-dessous comptent le SQL **applicatif** (authentification, permissions et requêtes métier), hors instrumentations Silk et hors `SAVEPOINT` du client de test.

## Synthèse

| Interface | Endpoint | Requêtes SQL mesurées | Verdict |
|---|---|---:|---|
| Professeurs | `/api/courses/professeurs/` | **6** (4 profs) | ✅ pas de N+1 |
| Associations | `/api/courses/dispenses/` | **6** (5 dispenses) | ✅ pas de N+1 |
| Validation CP | `/api/summaries/validation/` | **4** (10 résumés) | ✅ pas de N+1, ⚠️ pas de pagination |
| Tentatives classiques | `/api/exercises/attempts/` | **2** (5 tentatives) | ✅ pas de N+1 |
| Tentatives personnalisées | `/api/courses/personalized-exercises/attempts/` | **7** (5 tentatives) | ❌ 1 requête `COUNT` par tentative |
| Notifications | `/api/notifications/` | **4** (20 notifs) | ✅ paginé, ⚠️ 2 COUNT + index |
| Notifications non lues | `/api/notifications/unread-count/` | **2** | ⚠️ index `(user, is_read)` |
| File d’attente audio | `/api/courses/sessions/audio/queue/` | **73** (10 sessions) | ❌ N+1 massif, interrogé toutes les 5 s |
| Sessions audio détaillées | `/api/courses/sessions/audio/` | **73** (10 sessions) | ❌ N+1 + `ffprobe` par session + isolation |
| Sessions (ViewSet) | `/api/courses/sessions/` | **66** (10 sessions) | ❌ N+1 du `SessionSerializer` |

Les interfaces « professeurs », « associations », « validation » et « tentatives classiques » sont déjà saines côté N+1. Les deux vrais chantiers sont **les tentatives personnalisées** et **toute la chaîne audio**.

---

## 1. Création de professeurs

### Ce qui existe déjà

- [ProfesseurListView](resume/backend/courses/views.py#L1868) :
  `select_related('user', 'universite').prefetch_related('filieres').distinct()`.
- [ProfesseurSerializer](resume/backend/courses/serializers.py) :
  `user_full_name`, `user_username`, `universite_nom` sont couverts par le `select_related` ; `filieres` par le prefetch.
- La création [create_professeur_simple_view](resume/backend/courses/views.py#L2451) crée `User`, `UserProfile`, `Professeur` (et éventuellement `Dispense` en onboarding), puis l’app recharge la liste.

### Preuve mesurée

`GET /api/courses/professeurs/` : **6 requêtes** pour 4 professeurs, indépendant du nombre de professeurs (auth + profil + 3 FK de permission + liste + prefetch).

### Problèmes / recommandations

- Aucun N+1 sur la liste.
- La boucle `while User.objects.filter(username=...).exists()` dans la création fait une requête par candidat ; en cas de collision de nom, plusieurs requêtes. Risque faible, mais une contrainte unique + `IntegrityError` serait plus robuste.
- Après création, l’écran recharge la liste ; cette liste est déjà optimisée. Rien d’urgent.

**Correction recommandée :** aucune correction bloquante. Optionnel : simplifier la génération d’username et sérialiser l’objet créé avec les relations déjà chargées.

---

## 2. Association des professeurs (Dispense)

### Ce qui existe déjà

- [list_dispenses_view](resume/backend/courses/views.py#L2637) :
  `select_related('professeur__user', 'cours')`, puis sérialisation manuelle.
- `ProfesseurListView` est également utilisé par l’écran d’association.

### Preuve mesurée

`GET /api/courses/dispenses/` : **6 requêtes** pour 5 dispenses, constant.

### Problèmes / recommandations

- Aucun N+1 : `professeur.user`, `cours` et `cours.filiere` sont couverts par le `select_related` ou l’objet.
- Pas de pagination ; si le nombre d’associations devient élevé, ajouter `page`/`page_size`.
- `get_or_create`/`Dispense` n’ont pas de N+1.

**Correction recommandée :** aucune correction bloquante. Pagination seulement si le volume l’exige.

---

## 3. Validation des résumés (CP)

### Ce qui existe déjà

- [get_summaries_for_validation_view](resume/backend/courses/views.py#L2157) :
  `select_related('course', 'author_user', 'professeur', 'professeur__user')`.
- Une **seule** requête `Purchase.objects.filter(summary_id__in=[...])` pour calculer `has_purchases` de toute la liste.
- Le filtre `search` est déjà serveur (`titre`, `course.nom`, prénom/nom du professeur, spécialité).
- L’écran Flutter [validation_screen.dart](resume/lib/features/validation/screens/validation_screen.dart) envoie la recherche au serveur, mais filtre **localement** `all/validated/pending`.

### Preuve mesurée

`GET /api/summaries/validation/` : **4 requêtes** pour 10 résumés, indépendant du nombre de résumés (auth/profil + liste + achats + permissions).

### Problèmes / recommandations

- **Pas de pagination** : la vue fait `list(summaries)` et renvoie tous les résumés avec le `texte_resume` complet. Sur un volume élevé, la réponse devient lourde.
- **Pas de cache** : c’est volontaire et correct ici. La liste dépend du CP, de ses résumés et de leurs statuts ; une clé partagée serait fausse, et une clé par CP devrait être invalidée à chaque validation/création. Le gain ne justifie pas la complexité.
- Les compteurs `validated_count`/`pending_count` sont calculés en Python (pas de requêtes supplémentaires) ; ils sont corrects.
- Le filtre `all/validated/pending` est encore client-side : avec pagination, il devra devenir un paramètre serveur (`is_validated=true/false`).

**Corrections recommandées :**
1. Ajouter `page`/`page_size` à `/summaries/validation/` et un filtre serveur `is_validated`.
2. Adapter l’écran Flutter à la pagination et déplacer le filtre d’onglet côté serveur.
3. Ne pas ajouter de cache partagé. Un TTL par CP serait possible mais doit être invalidé sur toute validation/suppression ; à ne faire que si les mesures le justifient.

---

## 4. Exercices — « Mes tentatives »

### 4.1 Tentatives classiques

- [get_exercise_attempts_view](resume/backend/courses/exercise_views.py#L379) :
  `select_related('exercise', 'exercise__summary')`.
- Mesure : `GET /api/exercises/attempts/` → **2 requêtes** pour 5 tentatives.
- Aucun N+1 ; pas de pagination.

### 4.2 Tentatives personnalisées

- [get_personalized_attempts_view](resume/backend/courses/personalized_exercise_views.py#L524) :
  `select_related('personalized_exercise', 'personalized_exercise__summary')`.
- Mais la boucle appelle `attempt.personalized_exercise.questions_count`, qui est une **propriété** :
  ```python
  @property
  def questions_count(self):
      return self.questions.count()
  ```
  → **un `SELECT COUNT(*)` par tentative**.
- Mesure : `GET /api/courses/personalized-exercises/attempts/` → **7 requêtes** pour 5 tentatives (1 auth + 1 liste + 5 COUNT).
- L’écran Flutter [exercises_screen.dart](resume/lib/features/exercises/screens/exercises_screen.dart) charge les deux endpoints, fusionne et trie toutes les tentatives côté Dart ; sans pagination, le coût augmente avec l’historique.

**Corrections recommandées :**
1. Annoter le queryset avec `Count('personalized_exercise__questions')` et exposer cette valeur dans la réponse au lieu de la propriété.
2. Paginer les deux endpoints de tentatives (`page`/`page_size`) et adapter l’écran Flutter (ou au minimum limiter le volume).
3. Pour le détail d’une tentative, conserver le `build_results()` existant (une seule tentative).

---

## 5. Notifications

### Ce qui existe déjà

- [list_notifications](resume/backend/notifications/views.py#L105) :
  - pagination `page`/`page_size` (20 par défaut, 50 max) ;
  - `select_related('notification', 'notification__target_universite', 'notification__target_filiere', 'notification__target_promotion')` ;
  - filtres `search`, `type` (multi-types), `unread_only`.
- [UserNotificationSerializer](resume/backend/notifications/serializers.py) imbrique `AppNotificationSerializer`, couvert par le `select_related`.
- L’écran Flutter [notifications_screen.dart](resume/lib/features/notifications/screens/notifications_screen.dart) utilise `loadMore` ; la liste est donc déjà paginée côté client.

### Preuve mesurée

- `GET /api/notifications/` : **4 requêtes** pour 20 notifications (auth + liste + `total` + `unread_count`).
- `GET /api/notifications/unread-count/` : **2 requêtes**.

### Problèmes / recommandations

- **Deux COUNT par appel de liste** : `total = qs.count()` et `unread_count = UserNotification.objects.filter(...).count()`. Le second est aussi exposé par l’endpoint dédié, lui-même appelé par le polling de l’application. Le badge et la liste peuvent donc interroger deux fois la même information.
- `UserNotification` n’a pas d’index composite `(user, is_read)` ; les deux COUNT filtrent sur ces colonnes. Le `unique_together (user, notification)` donne un index sur `user` mais pas sur `is_read`.
- Aucun N+1 sur le contenu.

**Corrections recommandées :**
1. Ajouter un index `(user, is_read)` (ou `(user, is_read, created_at)`) sur `UserNotification`.
2. Éviter le double appel liste + unread-count : soit le polling ne demande que le compteur, soit l’écran réutilise `unread_count` déjà présent dans la réponse de liste.
3. Le COUNT de `total` est acceptable ; si nécessaire, une pagination sans COUNT (comme pour le catalogue) peut être envisagée.

---

## 6. File d’attente audio et sessions

C’est le point le plus problématique de l’audit.

### 6.1 `GET /api/courses/sessions/audio/queue/`

- [get_sessions_queue](resume/backend/courses/views.py#L1514) sérialise `SessionSerializer(queryset, many=True)` **sans `select_related` ni `prefetch_related`**.
- [SessionSerializer](resume/backend/courses/serializers.py#L88) déclenche, par session :
  - `course_name` → requête `course` ;
  - `professeur_info` → `professeur_fk` + `user` + `universite` ;
  - `has_ai_summary` → `summaries.filter(author_type='ai').exists()` ;
  - `ai_summary_id` → `summaries.filter(...).first()`.
- La vue exécute en plus **6 COUNT** : total + pending + processing + transcribed + summarized + failed.
- L’écran Flutter [audio_sessions_screen.dart](resume/lib/features/upload/screens/audio_sessions_screen.dart#L528) appelle cet endpoint **toutes les 5 secondes** (`Timer.periodic`), même quand l’écran n’est pas visible.

**Mesure : 73 requêtes pour 10 sessions.**

### 6.2 `GET /api/courses/sessions/audio/`

- [get_audio_sessions](resume/backend/courses/views.py#L1181) fait déjà `select_related('course').prefetch_related('summaries')`, mais :
  - `SessionSerializer` ajoute `professeur_fk`/`user`/`universite` et les deux requêtes `summaries.filter(...)` par session ;
  - `audio_processor.get_audio_info(session.id)` refait un `Session.objects.get(id=...)` **et** `session.course.nom` par session ([audio_processing.py](resume/backend/courses/audio_processing.py#L29)) ;
  - `_get_audio_duration` lance **`ffprobe` par session** (sous-processus), pas seulement du SQL.
- L’endpoint ne filtre pas par université/promotion/filière : tout utilisateur authentifié peut lister **toutes** les sessions audio et obtenir leurs URLs. C’est aussi un problème d’isolation des données.

**Mesure : 73 requêtes pour 10 sessions** (+ `ffprobe` par session).

### 6.3 `GET /api/courses/sessions/` (ViewSet)

- [SessionListCreateView](resume/backend/courses/views.py#L361) retourne `Session.objects.all()` sans `select_related`/`prefetch_related` ; `SessionSerializer` produit le même N+1.

**Mesure : 66 requêtes pour 10 sessions.**

### Corrections recommandées

1. **Requêtes** : ajouter aux trois querysets :
   ```python
   .select_related('course', 'professeur_fk__user', 'professeur_fk__universite')
   .prefetch_related('summaries')
   ```
2. **Serializer** : remplacer les `.filter(...).exists()` / `.first()` par la liste préchargée (`obj.summaries.all()`) ou par des annotations `Exists`/`Subquery`. Attention : un `.filter()` sur un manager préchargé peut relancer une requête ; utiliser `to_attr` ou une annotation.
3. **`get_audio_info`** : lui passer la `Session` déjà chargée (nouvelle méthode) au lieu de refaire `Session.objects.get` + `course.nom` ; ne pas exécuter `ffprobe` pour chaque ligne de la file. Utiliser `audio_duration` déjà stocké, ou calculer la durée à la demande.
4. **Statistiques** : remplacer les 6 COUNT par un seul `aggregate` conditionnel (`Count('id', filter=Q(processing_status='pending'))`, etc.).
5. **Isolation** : appliquer à `get_audio_sessions` le même filtrage université/promotion/filière que `get_sessions_queue` (ou une permission équivalente).
6. **Polling** : ne pas interroger la file complète toutes les 5 s. Utiliser l’endpoint de statistiques/léger, augmenter l’intervalle, et arrêter le timer quand l’écran n’est pas visible.
7. **Pagination** : ajouter `page`/`page_size` à la queue et aux sessions, et adapter Flutter.
8. **Index** : vérifier `Session(processing_status, created_at)` et les filtres de la file ; les COUNT de statuts en profiteront.

---

## Priorisation proposée

| Priorité | Correction | Justification |
|---|---|---|
| **P0** | N+1 de la file audio + `get_audio_info` + serializer | 73 requêtes / 10 sessions, répétées toutes les 5 s |
| **P0** | Isolation de `get_audio_sessions` | Fuite potentielle de sessions/audio entre cohortes |
| **P1** | `questions_count` des tentatives personnalisées | +1 requête par tentative, croissance linéaire |
| **P1** | Pagination validation + tentatives + file audio | Volume et taille des réponses |
| **P2** | Index `UserNotification(user, is_read)` et réduction des COUNT | Coût des badges/polling |
| **P2** | Agrégation des 6 COUNT de la file | 6 requêtes → 1 |
| **P3** | Pagination/optimisation des dispenses | Volume actuellement faible |

---

## Ce qui est déjà bon

- `ProfesseurListView` : `select_related` + `prefetch`.
- `list_dispenses_view` : `select_related`.
- `get_summaries_for_validation_view` : `select_related` + un seul `Purchase` pour `has_purchases`.
- `get_exercise_attempts_view` : `select_related`.
- `list_notifications` : pagination + `select_related`.
- Les optimisations du catalogue (cours, résumés, référentiels, pagination, cache Redis) ne s’appliquent **pas** automatiquement à ces interfaces ; c’est pourquoi cet audit était nécessaire.

---

## Corrections P0 appliquées — audio

| Endpoint | Avant | Après P0 |
|---|---:|---:|
| `/api/courses/sessions/audio/queue/` (10 sessions) | 73 | **6** |
| `/api/courses/sessions/audio/` (10 sessions) | 73 | **4** |
| `/api/courses/sessions/` (10 sessions) | 66 | **7** |

Ce qui a été corrigé :

- `SessionSerializer` : `has_ai_summary` / `ai_summary_id` lisent le prefetch
  `summaries` au lieu d’un `.filter().exists()` / `.first()` par session.
- `_sessions_optimisees()` : `select_related('course',
  'professeur_fk__user', 'professeur_fk__universite')` +
  `prefetch_related('summaries')` sur la queue, l’audio détaillé, le ViewSet
  et le détail.
- `get_audio_info_for_session(session)` : plus de `Session.objects.get` ni de
  `ffprobe` par ligne ; la durée vient de `audio_duration`. L’ancien
  `get_audio_info(session_id)` conserve le `ffprobe` pour les appels unitaires.
- `get_sessions_queue` : les 6 COUNT sont remplacés par **un seul `aggregate`**
  conditionnel.
- `get_audio_sessions` : applique la **même isolation par cohorte** que la
  queue (admin = tout, CP/étudiant = son université/promotion/filière).
- Flutter `audio_sessions_screen.dart` : polling **10 s** au lieu de 5 s, et
  timer arrêté quand l’application passe en arrière-plan (reprise au retour).

Tests ajoutés : `AudioSessionsNoNPlusOneTest` — 3 tests (queue, détail,
isolation par cohorte). Les tests P0 passent.

**Reste à corriger (P1/P2) :** `questions_count` des tentatives personnalisées,
pagination de la validation et des tentatives, index `UserNotification`,
réduction des COUNT des notifications.

## Corrections P1/P2 appliquées — tentatives, validation, notifications

### Mesures après correction

| Endpoint | Volume de test | Avant | Après |
|---|---:|---:|---:|
| `/api/personalized-exercises/attempts/` | 5 tentatives | 7 | **2** |
| `/api/exercises/attempts/` sans pagination | 5 tentatives | 2 | **2** |
| `/api/exercises/attempts/?page=1&page_size=2` | 5 tentatives | — | **3** (1 COUNT pour `total`) |
| `/api/summaries/validation/` sans pagination | 5 résumés | 4 | **4** |
| `/api/summaries/validation/?page=1&page_size=2` | 5 résumés | — | **5** (aggregate + page + achats) |
| `/api/notifications/` | 4 notifications | 4 | **3** |

Les requêtes applicatives sont mesurées avec `CaptureQueriesContext`, sans les
`SAVEPOINT` du client de test.

### Ce qui a été corrigé

1. **Tentatives personnalisées** (`personalized_exercise_views.py`)
   - Le queryset est annoté avec `Count('personalized_exercise__questions')` ;
     la boucle lit `questions_count_annot` au lieu de la propriété
     `questions_count`, qui déclenchait un `SELECT COUNT(*)` par tentative.
   - Pagination **opt-in** (`page` / `page_size`, max 100) : sans paramètre, la
     réponse reste la liste complète (rétrocompatible avec l'app actuelle).
2. **Tentatives classiques** (`exercise_views.py`)
   - Même pagination opt-in ; le N+1 n'existait déjà pas.
3. **Validation CP** (`views.py`)
   - Filtre serveur `is_validated=true/false` pour les onglets.
   - Pagination opt-in ; `total_count`, `validated_count` et `pending_count`
     sont calculés en **un seul `aggregate`** sur l'ensemble filtré (recherche
     comprise), et non sur la page renvoyée : les compteurs des onglets restent
     globaux quand un onglet est sélectionné.
   - `has_purchases` ne fait plus qu'une requête sur les IDs de la page.
4. **Notifications** (`notifications/models.py`, `views.py`)
   - Index `(user, is_read)` et `(user, -created_at)` sur `UserNotification`
     (migration `notifications/0003_...`).
   - Sans filtre texte/type, `total` et `unread_count` sont calculés en **un
     seul `aggregate`** au lieu de deux COUNT ; avec filtres, le comportement
     reste le même.

### Tests ajoutés

`AttemptsAndValidationPaginationTest` (5 tests) : absence de N+1 sur les
tentatives personnalisées, pagination des deux historiques, compteurs et
filtre de validation, agrégation des notifications. La suite complète
`courses.tests` passe (32 tests).

## Adaptation Flutter (29/10/2026)

### Validation CP — [validation_screen.dart](resume/lib/features/validation/screens/validation_screen.dart)

- Chargement par pages de **20** avec `ScrollController` : la page suivante
  se charge quand on approche du bas (liste virtuelle, pas de blocage).
- **Filtre d'onglet côté serveur** : `is_validated=true/false` accompagne
  chaque requête ; les compteurs « Tous / Validés / En attente » viennent du
  serveur et restent globaux même sous un onglet filtré.
- La recherche est envoyée au serveur (débounce de 500 ms conservé) ; le
  filtrage local a été retiré pour éviter de raisonner sur une seule page.
- Validation, invalidation et suppression mettent à jour les compteurs et la
  liste immédiatement, puis la liste est resynchronisée.
- `getSummariesForValidation` accepte désormais `page`, `pageSize` et
  `isValidated`.

### Mes tentatives — [exercises_screen.dart](resume/lib/features/exercises/screens/exercises_screen.dart)

- Les deux historiques (classique + QCM personnalisé) sont chargés par pages
  de **20**, puis fusionnés et triés par date. Le scroll charge la page
  suivante de chaque source qui en a encore.
- Le backend renvoie désormais, en mode paginé, un bloc `stats`
  (`total`, `passed`, `score_sum`) calculé sur **tout l'historique**. L'onglet
  « Statistiques » (Total / Réussis / Moyenne / Échoués) reste donc exact même
  si seules deux pages sont en mémoire. Un repli calcule les stats sur les
  éléments chargés si un ancien backend ne renvoie pas ce bloc.
- `getExerciseAttempts` retourne la réponse complète (au lieu du seul tableau)
  et accepte `page`/`pageSize` ; `getPersonalizedExerciseAttempts` accepte
  aussi `page`/`pageSize`. Les appels sans pagination conservent le
  comportement historique.
- Coût SQL en mode paginé : une requête d'agrégat supplémentaire par source
  pour les statistiques (3 requêtes par page au lieu de 2 pour la liste
  complète), mais un volume transféré divisé par le nombre de pages. Le coût
  reste **constant** quel que soit l'historique.

### Vérifications Flutter

- `flutter analyze` sur les fichiers modifiés : **aucune erreur** ; seuls des
  avertissements préexistants subsistent (méthode `_loadSummaryById` non
  utilisée, `withOpacity` déprécié).
- Tests backend concernés : 5 tests OK (dont les stats serveur).

## Corrections P3 appliquées — dispenses

- **[list_dispenses_view](resume/backend/courses/views.py)** : pagination
  **opt-in** (`page` / `page_size`, max 100). Sans paramètre, la réponse reste
  la liste complète (rétrocompatible). En mode paginé, la réponse contient
  `results`, `total`, `page`, `page_size`, `total_pages`, `has_more`.
- **[associate_prof_cours_screen.dart](resume/lib/features/upload/screens/associate_prof_cours_screen.dart)** :
  chargement par pages de **20** au défilement ; le badge « Associations
  existantes » affiche le **total serveur**, plus le nombre d'éléments chargés.
  Création et suppression d'une association resynchronisent la liste.
- **`listDispensesPage`** ajouté dans [api_service.dart](resume/lib/services/api_service.dart) ;
  l'ancien `listDispenses()` (liste complète) reste disponible pour les appels
  sans pagination.
- Tests : `DispensesPaginationTest` — 3 tests (pages successives, liste
  complète sans paramètre, paramètres invalides). Les 11 tests d'audit passent.

### Reste à faire

- Le badge de notifications interroge toujours `/unread-count/` séparément ;
  c'est le comportement attendu d'un badge, la liste expose déjà son
  `unread_count`.
- Vérifier sur un appareil avec un volume réaliste (plus de 20 résumés /
  tentatives / associations) le chargement progressif et le retour visuel.

### Fichiers à déployer

Backend :

```
backend/courses/personalized_exercise_views.py
backend/courses/exercise_views.py
backend/courses/views.py
backend/notifications/views.py
backend/notifications/models.py
backend/notifications/migrations/0003_usernotification_notif_user_is_read_idx_and_more.py
```

Puis `python manage.py migrate`.

Flutter (nouvelle build) :

```
lib/services/api_service.dart
lib/features/validation/screens/validation_screen.dart
lib/features/exercises/screens/exercises_screen.dart
lib/features/upload/screens/associate_prof_cours_screen.dart
```

Ne pas oublier les fichiers P0 audio de la session précédente s'ils ne sont pas
encore déployés : `backend/courses/audio_processing.py`,
`backend/courses/serializers.py`, `backend/courses/views.py` et
`lib/features/upload/screens/audio_sessions_screen.dart`.

## Décision demandée

L'audit et toutes ses corrections sont terminés : P0 audio, P1/P2 backend,
adaptation Flutter et P3 dispenses. Prochaine étape : **déployer** le backend
(fichiers listés ci-dessus + `migrate`), reconstruire l'application, puis
passer au **chantier 2** (IA / Celery).
