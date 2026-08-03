# Plan : Système Force Update (Mise à jour obligatoire)

## Contexte

Mettre en place un système professionnel de mise à jour obligatoire pour l'application mobile "Résumé Plus" afin d'empêcher les utilisateurs d'utiliser des versions obsolètes lorsque des changements sont effectués dans le backend, les API ou la base de données.

## État d'avancement

### ✅ Backend (Django) — TERMINÉ

**Fichiers modifiés :**
- `backend/security/models.py` — Ajout du modèle `AppVersion` avec :
  - `latest_version`, `minimum_version`, `force_update`
  - `android_latest_version`, `ios_latest_version` (versions par plateforme)
  - `maintenance_mode`, `maintenance_message` (mode maintenance)
  - `play_store_url`, `app_store_url`
  - `mandatory_update_message`
  - `is_active` (soft switch pour basculer entre configs)
- `backend/security/admin.py` — Administration complète avec `fieldsets` organisés
- `backend/security/serializers.py` — `AppVersionSerializer`
- `backend/security/views.py` — `app_version_view()` (GET public, détection plateforme via User-Agent)
- `backend/security/urls.py` — Route `/api/security/app-version/`
- `backend/resume_backend/urls.py` — Route racine `GET /api/app-version/` (import direct de la vue)

**Fonctionnalités API :**
- Endpoint public (AllowAny) : `GET /api/app-version/`
- Détection automatique Android/iOS via User-Agent
- Fallback en mode DEBUG si aucune config en base
- Retourne les versions par plateforme résolues

### ❌ Flutter (à faire)

**Fichiers à créer :**
1. `lib/services/version_service.dart` — Service singleton
2. `lib/screens/force_update_screen.dart` — Écran de mise à jour forcée

**Fichiers à modifier :**
3. `pubspec.yaml` — Ajouter `package_info_plus`
4. `lib/features/splash/screens/splash_screen.dart` — Intégrer la vérification

## Architecture Flutter

### 1. VersionService (`lib/services/version_service.dart`)

```
VersionService (singleton)
├── checkVersion() → Future<VersionCheckResult>
│   ├── Récupère version installée via package_info_plus
│   ├── Appelle GET /api/app-version/
│   ├── Compare versions (comparateur semver maison)
│   └── Retourne un enum : mandatory | optional | upToDate | maintenance | error
├── launchPlayStore() → ouvre URL Play Store
├── launchAppStore() → ouvre URL App Store
└── VersionCheckResult enum
    ├── maintenance    → Bloquer avec message maintenance
    ├── mandatory      → Forcer mise à jour (version < minimum)
    ├── optional       → Suggérer mise à jour (min <= version < latest)
    └── upToDate       → Aucune action
    └── error          → API inaccessible, continuer normalement
```

**Comparateur de versions** (semver maison) :
```dart
int _compareVersions(String a, String b) {
  // split sur '.' → compare chaque segment numériquement
  // 1.9.0 < 1.10.0 → correct
}
```

### 2. ForceUpdateScreen (`lib/screens/force_update_screen.dart`)

**Écran plein écran NON contournable** (PopScope bloque retour) :
- Logo de l'application (icône Résumé Plus)
- Titre : "Mise à jour requise"
- Message personnalisé depuis l'API (ou défaut)
- Version minimale requise affichée
- Bouton unique "Mettre à jour" → ouvre le store selon la plateforme
- Même charte graphique que le thème actuel (couleurs, polices, shadows AppTheme)

**Pas de bouton "Ignorer" ou "Plus tard" en mode mandatory.**

### 3. Modification de `SplashScreen`

Dans `_determineNavigation()` :

```dart
void _determineNavigation() async {
  await Future.delayed(const Duration(milliseconds: 2500));
  
  // Nouvelle étape : vérifier la version
  final versionResult = await VersionService().checkVersion();
  if (!mounted) return;
  
  switch (versionResult) {
    case VersionCheckResult.maintenance:
      Navigator.pushReplacement(..., ForceUpdateScreen(maintenance: true));
      return;
    case VersionCheckResult.mandatory:
      Navigator.pushReplacement(..., ForceUpdateScreen(maintenance: false));
      return;
    case VersionCheckResult.optional:
      showDialog(... "Nouvelle version disponible" ...)
      // Puis continuer normalement
    case VersionCheckResult.upToDate:
    case VersionCheckResult.error:
      // Continuer normalement
  }
  
  // Suite : vérification auth normale
  final startState = await AutoLoginService.determineStartState();
  ...
}
```

**Comportement si API est DOWN :**
- `error` → on skip la vérif, l'utilisateur continue
- Pas de blocage si le serveur est injoignable
- La vérification sera refaite au prochain lancement

### 4. Dialogue optionnel

En mode `optional` : `showDialog` standard avec :
- Titre : "Nouvelle version disponible"
- Message : "Une nouvelle version de Résumé Plus est disponible sur le store."
- Bouton "Plus tard" → ferme le dialogue, continue
- Bouton "Mettre à jour" → ouvre le store

## Flux complet

```
App démarre → SplashScreen
    ↓
checkVersion()
    ├── API error → continuer normalement
    ├── maintenance → ForceUpdateScreen (mode maintenance, message custom)
    ├── v_installée < v_minimum → ForceUpdateScreen (mode force, bouton store)
    ├── v_minimum ≤ v_installée < v_latest → Dialogue optionnel
    └── v_installée ≥ v_latest → continuer normalement
    ↓
AutoLogin → Dashboard / Login / Onboarding
```

## Vérification

1. Lancer le backend : `python manage.py makemigrations security && python manage.py migrate`
2. Créer une config `AppVersion` dans l'admin Django avec `force_update=True`, `minimum_version=99.0.0`
3. Dans le build Flutter : la version installée est < 99.0.0 → l'écran de mise à jour forcée doit s'afficher
4. Désactiver `force_update` → l'utilisateur passe normalement
5. Activer `maintenance_mode` → l'écran de maintenance s'affiche
6. Couper le serveur → l'application démarre normalement (pas de blocage)
