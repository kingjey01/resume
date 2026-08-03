# Correction Finale — Badges non affichés et non réinitialisés

## 🔴 Problèmes identifiés

1. **Badges "Résumés" et "Validation" ne s'affichent pas**
   - Les providers n'étaient pas initialisés correctement
   - Les compteurs n'étaient pas chargés au démarrage

2. **Badges ne se réinitialisent pas après consultation**
   - Le `resetBadge()` ne sauvegardait pas l'état
   - Après un refresh, les badges réapparaissaient

3. **Badge "Mes Achats" persiste après consultation**
   - Le compteur était basé sur une date fixe (24h)
   - Pas de tracking de la dernière visite

---

## ✅ Solutions implémentées

### 1. **Initialisation des badges au démarrage**

**Fichier :** `lib/features/app/screens/main_navigation_screen.dart`

```dart
@override
void initState() {
  super.initState();
  _loadUserProfile();
  // Charger les compteurs de badges au démarrage
  Future.microtask(() {
    ref.read(purchaseBadgeCountProvider.notifier).loadBadgeCount();
    ref.read(validatedSummariesBadgeProvider.notifier).refreshBadge();
    ref.read(createdSummariesBadgeProvider.notifier).refreshBadge();
  });
}
```

### 2. **Chargement des badges depuis l'API**

**Fichier :** `lib/features/home/providers/summary_provider.dart`

**Badge "Résumés" (validés) :**
```dart
Future<void> _loadBadgeCount() async {
  final summaries = await _apiService.getSummaries();
  
  // Compter les résumés validés créés dans les 24 dernières heures
  int recentCount = 0;
  final now = DateTime.now();
  
  for (var summary in summaries) {
    if (summary.isValidated) {
      final createdAt = summary.createdAt ?? DateTime(1970);
      final difference = now.difference(createdAt);
      
      if (difference.inHours < 24) {
        recentCount++;
      }
    }
  }
  
  state = recentCount;
}
```

**Badge "Validation" (créés/générés) :**
```dart
Future<void> _loadBadgeCount() async {
  final summaries = await _apiService.getSummaries();
  
  // Compter les résumés non validés dans les 24 dernières heures
  int recentCount = 0;
  final now = DateTime.now();
  
  for (var summary in summaries) {
    if (!summary.isValidated) {
      final createdAt = summary.createdAt ?? DateTime(1970);
      final difference = now.difference(createdAt);
      
      if (difference.inHours < 24) {
        recentCount++;
      }
    }
  }
  
  state = recentCount;
}
```

### 3. **Réinitialisation persistante des badges**

**Fichier :** `lib/features/app/screens/main_navigation_screen.dart`

```dart
onDestinationSelected: (index) async {
  // ...
  if (_userRole == 'CP') {
    if (index == 1) {  // Résumés
      ref.read(validatedSummariesBadgeProvider.notifier).resetBadge();
      await ref.read(validatedSummariesBadgeProvider.notifier).refreshBadge();
    } else if (index == 2) {  // Validation
      ref.read(createdSummariesBadgeProvider.notifier).resetBadge();
      await ref.read(createdSummariesBadgeProvider.notifier).refreshBadge();
    } else if (index == 3) {  // Mes Achats
      await ref.read(purchaseBadgeCountProvider.notifier).resetBadge();
    }
  }
  // ...
}
```

### 4. **Tracking de la dernière visite pour "Mes Achats"**

**Fichier :** `lib/providers/purchase_badge_provider.dart`

```dart
Future<void> loadBadgeCount() async {
  final prefs = await SharedPreferences.getInstance();
  final lastViewedStr = prefs.getString(_lastViewedKey);
  final lastViewed = lastViewedStr != null ? DateTime.parse(lastViewedStr) : DateTime(2000);
  
  final purchases = await _apiService.getPurchasedSummaries();
  
  // Compter les achats complétés APRÈS la dernière visite
  int recentCount = 0;
  
  for (var purchase in purchases) {
    if (purchase['status'] == 'completed') {
      final completedAt = DateTime.parse(purchase['completed_at'] ?? '');
      
      // Compter les achats complétés APRÈS la dernière visite
      if (completedAt.isAfter(lastViewed)) {
        recentCount++;
      }
    }
  }
  
  state = recentCount;
}

Future<void> resetBadge() async {
  state = 0;
  final prefs = await SharedPreferences.getInstance();
  await prefs.setString(_lastViewedKey, DateTime.now().toIso8601String());
}
```

---

## 📁 Fichiers modifiés

| Fichier | Changements |
|---------|------------|
| `lib/features/home/providers/summary_provider.dart` | Ajout `_loadBadgeCount()` pour charger depuis l'API |
| `lib/features/app/screens/main_navigation_screen.dart` | Initialisation + réinitialisation async des badges |
| `lib/providers/purchase_badge_provider.dart` | Tracking de la dernière visite avec SharedPreferences |

---

## 🔄 Flux complet

### Démarrage de l'app
```
App lancée
  ↓
initState() appelé
  ↓
loadBadgeCount() pour "Mes Achats"
refreshBadge() pour "Résumés" (validés)
refreshBadge() pour "Validation" (créés)
  ↓
Badges affichés avec les compteurs corrects
```

### Consultation d'un onglet
```
Utilisateur clique sur "Résumés"
  ↓
resetBadge() → state = 0
refreshBadge() → recharge depuis l'API
  ↓
Sauvegarde de la date de visite (SharedPreferences)
  ↓
Badge réinitialisé et persiste après refresh
```

### Après un refresh de page
```
App redémarrée
  ↓
initState() appelé
  ↓
Charge les badges depuis l'API
  ↓
Compare avec la date de dernière visite
  ↓
Affiche uniquement les nouveaux résumés/achats
```

---

## ✅ Vérification

Après le build, vérifier que :

1. ✅ Badge rouge sur "Résumés" au démarrage
2. ✅ Badge orange sur "Validation" au démarrage
3. ✅ Badge rouge sur "Mes Achats" au démarrage
4. ✅ Badges se réinitialisent quand on clique dessus
5. ✅ Badges ne réapparaissent pas après un refresh
6. ✅ Nouveaux résumés/achats incrémentent les badges

---

## 🚀 Déploiement

```bash
flutter clean
flutter pub get
flutter run
```

---

## 💡 Notes techniques

- **SharedPreferences** utilisé pour persister la date de dernière visite
- **Async/await** pour les opérations de sauvegarde
- **API loading** pour charger les compteurs depuis le backend
- **24h window** pour les résumés validés/créés
- **Timestamp-based** pour les achats (plus flexible)

---

## 🔗 Dépendances requises

- `shared_preferences` — Déjà dans pubspec.yaml
- `flutter_riverpod` — Déjà dans pubspec.yaml

Aucune nouvelle dépendance requise.
