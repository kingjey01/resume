# Badge "Mes Achats" — Implémentation

## 📋 Objectif

Ajouter un badge (compteur) sur l'icône "Mes Achats" dans la barre de navigation, similaire au badge des notifications, pour notifier l'utilisateur quand un achat ou un abonnement réussit.

---

## 🏗️ Architecture

### 1. **Provider Riverpod** (`lib/providers/purchase_badge_provider.dart`)

Gère l'état du compteur de badges :

```dart
final purchaseBadgeCountProvider = StateNotifierProvider<PurchaseBadgeNotifier, int>((ref) {
  return PurchaseBadgeNotifier();
});
```

**Méthodes :**
- `loadBadgeCount()` — Charge les achats récents (< 24h)
- `incrementBadge()` — Ajoute 1 au compteur
- `resetBadge()` — Réinitialise à 0 (quand on visite "Mes Achats")
- `decrementBadge()` — Décrémente de 1

### 2. **Widget Badge** (`lib/widgets/badge_icon.dart`)

Widget réutilisable pour afficher une icône avec un badge :

```dart
BadgeIcon(
  icon: Icons.shopping_bag_rounded,
  badgeCount: 3,
  badgeColor: Colors.red,
  badgeTextColor: Colors.white,
)
```

**Affichage :**
- Badge rouge avec compteur blanc
- Positionné en haut-à-droite de l'icône
- Affiche "99+" si > 99
- Caché si compteur = 0

### 3. **Navigation** (`lib/features/app/screens/main_navigation_screen.dart`)

Intégration du badge dans la barre de navigation :

```dart
List<NavigationDestination> _buildDestinations(WidgetRef ref) {
  final badgeCount = ref.watch(purchaseBadgeCountProvider);
  
  return [
    ...
    NavigationDestination(
      icon: BadgeIcon(
        icon: Icons.shopping_bag_rounded,
        badgeCount: badgeCount,
      ),
      label: 'Mes Achats',
    ),
    ...
  ];
}
```

**Comportement :**
- Badge mis à jour en temps réel (Riverpod)
- Badge réinitialisé quand on clique sur "Mes Achats"
- Compteur chargé au démarrage de l'app

### 4. **Écran Paiement** (`lib/features/purchases/screens/payment_status_screen.dart`)

Incrément du badge quand le paiement réussit :

```dart
if (status == 'completed') {
  // Incrémenter le badge "Mes Achats"
  ref.read(purchaseBadgeCountProvider.notifier).incrementBadge();
  setState(() => _state = _PaymentState.success);
}
```

---

## 🔄 Flux utilisateur

1. **Utilisateur initie un achat/abonnement**
   - Écran `PaymentStatusScreen` s'affiche
   - Badge reste inchangé

2. **Paiement réussit**
   - Badge "Mes Achats" s'incrémente (+1)
   - Notification push envoyée (backend)
   - Utilisateur voit le badge rouge

3. **Utilisateur clique sur "Mes Achats"**
   - Badge réinitialisé à 0
   - Écran `PurchasesScreen` affiche la liste des achats

4. **Redémarrage de l'app**
   - Badge rechargé automatiquement
   - Compte les achats complétés < 24h

---

## 📁 Fichiers créés/modifiés

| Fichier | Type | Changements |
|---------|------|-------------|
| `lib/providers/purchase_badge_provider.dart` | ✨ Nouveau | Provider Riverpod pour gérer le compteur |
| `lib/widgets/badge_icon.dart` | ✨ Nouveau | Widget badge réutilisable |
| `lib/features/app/screens/main_navigation_screen.dart` | 📝 Modifié | Intégration du badge dans la navigation |
| `lib/features/purchases/screens/payment_status_screen.dart` | 📝 Modifié | Incrément du badge au succès du paiement |

---

## 🎨 Personnalisation

### Couleur du badge

```dart
BadgeIcon(
  icon: Icons.shopping_bag_rounded,
  badgeCount: badgeCount,
  badgeColor: Colors.orange,      // Changer la couleur
  badgeTextColor: Colors.white,
)
```

### Taille du badge

```dart
BadgeIcon(
  icon: Icons.shopping_bag_rounded,
  badgeCount: badgeCount,
  badgeSize: 24,  // Défaut: 20
)
```

---

## ✅ Vérification

Après déploiement, vérifier que :

1. ✅ Badge visible sur "Mes Achats" avec compteur
2. ✅ Badge s'incrémente après un paiement réussi
3. ✅ Badge se réinitialise quand on visite "Mes Achats"
4. ✅ Badge persiste après redémarrage de l'app
5. ✅ Badge affiche "99+" si > 99
6. ✅ Badge caché si compteur = 0

---

## 🚀 Déploiement

Aucune migration backend requise. Simplement :

```bash
# Recompiler l'app Flutter
flutter pub get
flutter run
```

---

## 💡 Améliorations futures

- [ ] Ajouter un son/vibration quand le badge s'incrémente
- [ ] Ajouter une animation d'apparition du badge
- [ ] Ajouter un badge pour les abonnements expirés
- [ ] Synchroniser avec les notifications push (décrémente si notification lue)
