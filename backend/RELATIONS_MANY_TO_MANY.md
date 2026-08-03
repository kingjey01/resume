# Documentation des relations ManyToMany

Ce document explique comment utiliser les nouvelles relations ManyToMany entre les modèles Université, Filière et Promotion.

## Modifications apportées

1. **Modèles** :
   - Ajout de `ManyToManyField` entre `Université` et `Filière` via la table `UniversiteFiliere`
   - Ajout de `ManyToManyField` entre `Filière` et `Promotion` via la table `FilierePromotion`
   - Conservation de la rétrocompatibilité avec les champs existants

2. **Sérialiseurs** :
   - Création de `UniversiteFiliereSerializer` et `FilierePromotionSerializer`
   - Mise à jour des sérialiseurs existants pour inclure les relations

3. **Vues** :
   - Conversion des vues en ViewSets pour une meilleure gestion des relations
   - Ajout d'actions personnalisées pour gérer les relations

4. **URLs** :
   - Utilisation de `DefaultRouter` pour générer automatiquement les URLs
   - Ajout d'endpoints pour gérer les relations

## Comment utiliser les nouvelles fonctionnalités

### 1. Obtenir toutes les filières d'une université
```http
GET /api/universites/{id}/filieres/
```

### 2. Ajouter une filière à une université
```http
POST /api/universites/{id}/add_filiere/
Content-Type: application/json

{
    "filiere_id": 1
}
```

### 3. Obtenir toutes les promotions d'une filière
```http
GET /api/filieres/{id}/promotions/
```

### 4. Ajouter une promotion à une filière
```http
POST /api/filieres/{id}/add_promotion/
Content-Type: application/json

{
    "promotion_id": 1
}
```

### 5. Obtenir toutes les filières associées à une promotion
```http
GET /api/promotions/{id}/filieres/
```

### 6. Gérer directement les relations via les endpoints dédiés
- `GET /api/universite-filieres/` - Lister toutes les relations université-filière
- `POST /api/universite-filieres/` - Créer une relation
- `GET /api/universite-filieres/{id}/` - Détails d'une relation
- `PUT /api/universite-filieres/{id}/` - Mettre à jour une relation
- `DELETE /api/universite-filieres/{id}/` - Supprimer une relation

## Migration des données existantes

Un script de migration a été créé pour migrer automatiquement les relations existantes vers la nouvelle structure. Pour l'exécuter :

```bash
python manage.py migrate courses 0010_migrate_existing_relations
```

## Exemples d'utilisation dans le frontend Flutter

### Chargement des filières en fonction de l'université sélectionnée

```dart
// Charger les filières d'une université
Future<void> loadFilieres(int universiteId) async {
  try {
    final response = await http.get(
      Uri.parse('$baseUrl/api/universites/$universiteId/filieres/'),
      headers: {'Authorization': 'Bearer $token'},
    );
    
    if (response.statusCode == 200) {
      setState(() {
        filieres = List<dynamic>.from(json.decode(response.body));
      });
    }
  } catch (e) {
    print('Erreur lors du chargement des filières: $e');
  }
}
```

### Ajout d'une filière à une université

```dart
Future<void> addFiliereToUniversite(int universiteId, int filiereId) async {
  try {
    final response = await http.post(
      Uri.parse('$baseUrl/api/universites/$universiteId/add_filiere/'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
      body: json.encode({'filiere_id': filiereId}),
    );
    
    if (response.statusCode == 201) {
      // Rafraîchir la liste des filières
      loadFilieres(universiteId);
    }
  } catch (e) {
    print('Erreur lors de l\'ajout de la filière: $e');
  }
}
```

## Notes importantes

1. Les anciens champs `universite` et `promotion` dans le modèle `Filiere` sont conservés pour la rétrocompatibilité.
2. Il est recommandé de migrer progressivement le code pour utiliser les nouvelles relations.
3. Les performances ont été optimisées avec `select_related` et `prefetch_related` pour éviter les requêtes N+1.

## Prochaines étapes

1. Mettre à jour le frontend pour utiliser les nouveaux endpoints
2. Supprimer les anciens champs une fois la migration terminée
3. Ajouter des tests unitaires pour les nouvelles fonctionnalités
