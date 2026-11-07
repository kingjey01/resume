# Audit des performances SQL, du cache et des requêtes N+1 — Avant le chantier 2

Avant de passer au deuxième axe de développement, effectuer un audit ciblé des interfaces suivantes pour vérifier si les optimisations déjà appliquées contre les requêtes N+1 et les chargements SQL inefficaces sont également prises en compte.

### 1. Interfaces à auditer

1. **Création de professeurs** : vérifier le chargement de la liste après création et détecter les requêtes répétitives.
2. **Association des professeurs** : examiner le chargement des associations enregistrées et identifier les éventuels N+1.
3. **Validation des résumés (CP)** : analyser le chargement des résumés disponibles, en attente et validés, ainsi que l’utilisation du cache.
4. **Exercices — Mes tentatives** : vérifier le chargement des tentatives, les relations SQL sollicitées et les éventuels accès répétés à la base de données.
5. **Interface notification** : comment le notification se chargent dans l'interface et autre
6. ** File d'attente audio : vérifié aussi ses charges les données la bas et autres

### 2. Vérifications techniques

- Rechercher les N+1 dans les vues Django, serializers, querysets et relations associées.
- Vérifier l’utilisation pertinente de `select_related()` et `prefetch_related()`.
- Examiner les caches existants : utilité, invalidation après création ou modification, risques de données obsolètes et isolation par utilisateur.
- Mesurer le nombre de requêtes SQL et vérifier leur efficacité sur des volumes réalistes.
- Comparer les résultats avec les optimisations déjà réalisées, sans supposer que les mêmes corrections s’appliquent partout.

### 3. Livrable attendu

Présenter, pour chaque interface, les problèmes détectés, les preuves observées, les optimisations déjà présentes et les corrections recommandées.

**Important :** réaliser cet audit avant toute modification du deuxième axe. Ne modifier aucun code pendant cette phase sans autorisation. Après présentation des résultats, attendre la validation avant de commencer les corrections.