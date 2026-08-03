# 🔍 Diagnostic FCM Complet — Causes & Corrections

## 📊 Résumé exécutif

Tu avais raison : l'infrastructure serveur (Celery, Redis, Firebase Admin SDK, IAM) est OK. Le problème est dans la **logique d'association user ↔ token** côté Flutter et le **manque de logs** côté Django.

---

## 🔴 Causes classées par probabilité

### **#1 (95%) — Token envoyé AVANT authentification**
**Fichier :** `lib/main.dart:33`

```dart
// ❌ AVANT
await FcmService().initialize();  // Appelle refreshToken() → API call sans JWT
```

**Conséquence :**
- Au premier lancement : 401 silencieux, token non enregistré
- Aux lancements suivants : si un JWT en cache existe, le token est associé à l'**ancien user** (avant logout)

### **#2 (90%) — Token non re-envoyé après changement de user**
**Fichier :** `lib/services/fcm_service.dart:103`

```dart
// ❌ AVANT
if (token != null && token != _currentToken) {
  await _api.registerFcmToken(token, ...);
}
```

**Conséquence :** Sur le même appareil :
1. User1 login → token T1 enregistré, `_currentToken = T1`
2. User1 logout → `_currentToken = null` (ok)
3. User2 login → Firebase retourne T1 (le même), mais après `deleteToken()`, c'est T2
4. **MAIS** si Firebase retourne le même token entre 2 sessions → `token == _currentToken` → API jamais appelée → User2 sans device

### **#3 (85%) — Erreurs silencieuses sur registerFcmToken**
**Fichier :** `lib/services/api_service.dart:1198`

```dart
// ❌ AVANT
catch (e) {
  AppLogger.error('registerFcmToken error', e);
  // return void → impossible de savoir si succès
}
```

**Conséquence :** Aucun feedback. Si l'API renvoie 401/500, l'app continue comme si tout allait bien.

### **#4 (80%) — Login OTP bypassait l'enregistrement FCM**
**Fichier :** `lib/features/auth/screens/otp_verification_screen.dart`

L'OTP login sauvegardait les JWT mais n'appelait **jamais** `FcmService().registerCurrentUserToken()`. Tous les users qui se connectent par OTP n'avaient AUCUN device enregistré.

### **#5 (70%) — Logs backend insuffisants**
**Fichier :** `backend/notifications/views.py`

Aucun log ne traçait `user.id ↔ token` lors du register. Impossible de débugger les associations en production.

### **#6 (50%) — Race condition login/logout (fire-and-forget)**
**Fichier :** `lib/features/auth/providers/auth_provider.dart`

```dart
// ❌ AVANT
FcmService().refreshToken().catchError((_) => null); // Pas d'await
```

Si l'utilisateur navigue rapidement, le token peut arriver après logout.

---

## ✅ Corrections appliquées

### **1. Séparation init pré-auth / register post-auth**

**`lib/services/fcm_service.dart`**

```dart
/// Init au démarrage : permissions + handlers UNIQUEMENT
Future<void> initialize() async {
  FirebaseMessaging.onBackgroundMessage(_firebaseBackgroundHandler);
  await _requestPermissions();
  await _setupLocalNotifications();
  // ... configurer iOS, listeners onTokenRefresh, message handlers
  // ❌ NE PAS appeler refreshToken() ici
}

/// À appeler APRÈS le login
Future<bool> registerCurrentUserToken() async {
  final token = await _messaging.getToken();
  if (token == null) return false;
  _currentToken = token;
  // FORCE l'envoi (pas de check token != _currentToken)
  return await _api.registerFcmToken(token, deviceType: _deviceType());
}
```

### **2. Suppression du check d'égalité bloquant**

```dart
// ✅ APRÈS — toujours envoyer
final success = await _api.registerFcmToken(token, deviceType: _deviceType());
```

### **3. API retourne maintenant `bool`**

**`lib/services/api_service.dart`**

```dart
Future<bool> registerFcmToken(String token, {String deviceType = 'android'}) async {
  try {
    final response = await _dio.post('/notifications/devices/register/', ...);
    AppLogger.info('✅ [API] FCM token enregistré: status=${response.statusCode}');
    return true;
  } catch (e) {
    AppLogger.error('❌ [API] registerFcmToken error', e);
    return false;
  }
}
```

### **4. Login/Logout/OTP : await garanti**

**`lib/features/auth/providers/auth_provider.dart`**

```dart
// Login
state = AsyncValue.data(user);
if (!kIsWeb) {
  final success = await FcmService().registerCurrentUserToken();
  debugPrint('🔔 [Auth] FCM: ${success ? "✅ OK" : "❌ FAILED"}');
}

// Logout (AVANT de supprimer les JWT)
if (!kIsWeb) {
  await FcmService().deleteToken();  // → unregister via API + Firebase delete
}
await _authRepository.logout();
```

**`lib/features/auth/screens/otp_verification_screen.dart`**

```dart
await storageService.saveTokens(...);
if (!kIsWeb) {
  final fcmSuccess = await FcmService().registerCurrentUserToken();
}
```

### **5. Logs backend détaillés**

**`backend/notifications/views.py`**

```python
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def register_device(request):
    user = request.user
    token_suffix = fcm_token[-10:]
    
    logger.info(f"📲 [FCM Register] user={user.id}({user.username}) token=...{token_suffix}")
    
    # Détecter changement d'utilisateur
    existing = UserDevice.objects.filter(fcm_token=fcm_token).first()
    if existing and existing.user_id != user.id:
        logger.warning(
            f"🔄 [FCM Register] Token réassigné: "
            f"ancien_user={existing.user_id} → nouveau_user={user.id}"
        )
    
    device, created = UserDevice.objects.update_or_create(
        fcm_token=fcm_token,
        defaults={'user': user, 'device_type': device_type, 'is_active': True}
    )
    
    active_count = UserDevice.objects.filter(user=user, is_active=True).count()
    logger.info(f"📊 [FCM Register] {user.username} a {active_count} device(s) actif(s)")
```

---

## 🔄 Architecture FCM corrigée

```
┌─────────────────────────────────────────────────────────────┐
│                    DÉMARRAGE APP (main.dart)                 │
│  Firebase.initializeApp() → FcmService().initialize()        │
│  ▸ Permissions                                               │
│  ▸ Handlers (foreground/background/terminated)               │
│  ▸ onTokenRefresh listener                                   │
│  ❌ PAS de getToken() ni d'appel API                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                          LOGIN                               │
│  apiService.login(user, pwd) → JWT stocké                    │
│  await FcmService().registerCurrentUserToken()               │
│    ▸ getToken() Firebase                                     │
│    ▸ POST /notifications/devices/register/ (avec JWT)        │
│    ▸ Backend: update_or_create par fcm_token                 │
│    ▸ Si token existait pour user X → réassigné à user Y      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    PENDANT LA SESSION                        │
│  onTokenRefresh.listen → si Firebase régénère le token       │
│    ▸ POST /notifications/devices/register/ (auto)            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                          LOGOUT                              │
│  await FcmService().deleteToken()  (AVANT logout)            │
│    ▸ DELETE /notifications/devices/unregister/ (avec JWT)    │
│    ▸ Backend: is_active=False                                │
│    ▸ FirebaseMessaging.deleteToken() → régénération force    │
│  await apiService.logout() → suppression JWT                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Fichiers modifiés

| Fichier | Changement |
|---------|-----------|
| `lib/services/fcm_service.dart` | Split init/register, retire check token, deleteToken async |
| `lib/services/api_service.dart` | Retourne `bool`, logs détaillés |
| `lib/features/auth/providers/auth_provider.dart` | `await` sur register/delete, logs |
| `lib/features/auth/screens/otp_verification_screen.dart` | Ajout `registerCurrentUserToken()` |
| `backend/notifications/views.py` | Logs détaillés user/token, détection réassignation |

---

## 🧪 Tests de vérification

### Test #1 : Login simple
```bash
# Logs attendus côté Flutter :
📱 [FCM] Token récupéré: ...XYZ123
✅ [API] FCM token enregistré: status=201
🔔 [Auth] FCM token registration: ✅ OK

# Logs attendus côté Django :
📲 [FCM Register] user=42(john) token=...XYZ123 type=android
✅ [FCM Register] 📱 Créé — device_id=10 user=42(john)
📊 [FCM Register] john a maintenant 1 device(s) actif(s)
```

### Test #2 : Changement de compte (même téléphone)
```bash
# 1. User1 login
✅ Token T1 → User1 (device_id=10, active)

# 2. User1 logout
🗑️ [FCM] Désactivation token côté backend
✅ [FCM Unregister] 1 device(s) désactivé(s) pour user1

# 3. User2 login
🔄 [FCM Register] Token réassigné: ancien_user=42(user1) → nouveau_user=43(user2)
✅ [FCM Register] 🔄 Mis à jour — device_id=10 user=43(user2)
```

### Test #3 : Multi-device (même user, 2 téléphones)
```bash
# Phone A: user1 login → device_id=10, token=T1
# Phone B: user1 login → device_id=11, token=T2
📊 [FCM Register] user1 a maintenant 2 device(s) actif(s)
```

### Test #4 : Vérification BD après chaque opération
```python
# Django shell
python manage.py shell
>>> from notifications.models import UserDevice
>>> UserDevice.objects.filter(is_active=True).values('user__username', 'fcm_token', 'device_type')
```

---

## 🚀 Déploiement

### Frontend
```bash
flutter clean
flutter pub get
flutter run
```

### Backend
```bash
sudo systemctl restart gunicorn
# Pas besoin de migration (logique inchangée, juste logs ajoutés)
```

### Vérifier les logs en production
```bash
# Logs Django avec filtre FCM
tail -f /var/log/django/app.log | grep "FCM"
```

---

## 💡 Bonnes pratiques mises en place

✅ **Pas de getToken avant auth** — évite les 401 silencieux  
✅ **Toujours `await`** — pas de race condition  
✅ **Force re-send après login** — gère le cas même token + nouveau user  
✅ **Logs détaillés** — user.id, token suffix, action (créé/MAJ/réassigné)  
✅ **Detect réassignation** — warning quand un token change de propriétaire  
✅ **Multi-device supporté** — un user peut avoir plusieurs `UserDevice` actifs  
✅ **Cleanup automatique** — `cleanup_inactive_tokens` Celery task supprime > 30j  
✅ **OTP login couvert** — bug critique qui empêchait FCM pour tous les users OTP

---

## ⚠️ Erreur `UnregisteredError` restante

Cette erreur signifie que **le token Firebase est invalide / l'app a été désinstallée**. La gestion est déjà faite dans `tasks.py` :

```python
def _is_invalid_token_error(exc: Exception) -> bool:
    return isinstance(exc, (UnregisteredError, ...))

# Dans send_fcm_notification :
if _is_invalid_token_error(e):
    UserDevice.objects.filter(fcm_token=token).update(is_active=False)
```

**→** Les tokens invalides sont automatiquement marqués `is_active=False` puis supprimés après 30j par `cleanup_inactive_tokens`. C'est le comportement attendu.

---

## 📝 Checklist post-déploiement

- [ ] `flutter clean && flutter run` sur 2 téléphones de test
- [ ] Login user1 sur phone A → vérifier log `[FCM Register] user=...`
- [ ] Login user1 sur phone B → vérifier 2 devices actifs en BD
- [ ] Logout user1 → vérifier `[FCM Unregister]` + `is_active=False`
- [ ] Login user2 sur phone A → vérifier `Token réassigné`
- [ ] Envoyer notification depuis admin → vérifier réception sur le bon device
- [ ] Tester OTP login → vérifier que le token est bien enregistré
