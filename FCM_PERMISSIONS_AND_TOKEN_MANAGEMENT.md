# FCM Permissions & Token Management — Corrections

## 📋 Problèmes identifiés et solutions

### 1. **Permissions FCM non demandées à l'installation**

**Problème :** Les permissions FCM ne sont pas demandées à l'utilisateur lors de l'installation.

**Solution implémentée :**

#### AndroidManifest.xml ✅
```xml
<!-- Déjà présent -->
<uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
```

#### FcmService (lib/services/fcm_service.dart) ✅
```dart
Future<bool> _requestPermissions() async {
  final settings = await _messaging.requestPermission(
    alert: true,
    badge: true,
    sound: true,
    provisional: false,
    announcement: false,
    carPlay: false,
    criticalAlert: false,
  );

  final granted = settings.authorizationStatus == AuthorizationStatus.authorized ||
      settings.authorizationStatus == AuthorizationStatus.provisional;

  debugPrint(granted
      ? '✅ [FCM] Permissions accordées'
      : '⚠️ [FCM] Permissions refusées: ${settings.authorizationStatus}');

  return granted;
}
```

#### Initialisation (main.dart) ✅
```dart
if (!kIsWeb) {
  await FcmService().initialize();  // Demande les permissions
}
```

**Résultat :** Les permissions sont demandées automatiquement au démarrage de l'app.

---

### 2. **Tokens inactifs non supprimés (surcharge BD)**

**Problème :** Après désinstallation, les tokens restent dans la BD et s'accumulent.

**Solution implémentée :**

#### Tâche Celery (notifications/tasks.py) ✅
```python
@shared_task(bind=True)
def cleanup_inactive_tokens(self):
    """
    Delete inactive FCM tokens older than 30 days to prevent database bloat.
    Run daily via Celery Beat.
    """
    try:
        from datetime import timedelta
        from django.utils import timezone
        from .models import UserDevice
        
        cutoff_date = timezone.now() - timedelta(days=30)
        
        # Delete inactive tokens older than 30 days
        deleted_count, _ = UserDevice.objects.filter(
            is_active=False,
            updated_at__lt=cutoff_date
        ).delete()
        
        logger.info(f'🗑️ [Task] {deleted_count} tokens inactifs supprimés (> 30 jours)')
        
        return {'deleted_count': deleted_count}
```

#### Celery Beat Schedule (settings.py) ✅
```python
CELERY_BEAT_SCHEDULE = {
    'cleanup-inactive-tokens': {
        'task': 'notifications.tasks.cleanup_inactive_tokens',
        'schedule': crontab(hour=2, minute=0),  # Tous les jours à 2h du matin
    },
    ...
}
```

**Résultat :** 
- Les tokens inactifs sont supprimés automatiquement après 30 jours
- Exécution quotidienne à 2h du matin
- Prévient la surcharge de la BD

---

### 3. **Gestion des tokens lors de la désinscription**

**Endpoint existant (notifications/views.py) ✅**

```python
@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def unregister_device(request):
    """
    Mark an FCM token as inactive (e.g. on logout).
    Body: { "fcm_token": "..." }
    """
    fcm_token = request.data.get('fcm_token', '').strip()
    if not fcm_token:
        return Response({'error': 'fcm_token requis'}, status=status.HTTP_400_BAD_REQUEST)

    updated = UserDevice.objects.filter(user=request.user, fcm_token=fcm_token).update(is_active=False)
    return Response({'deactivated': updated > 0})
```

**Comportement :**
- Token marqué comme `is_active=False` (pas suppression immédiate)
- Suppression automatique après 30 jours
- Permet la récupération en cas d'erreur

---

## 🔄 Flux complet FCM

### 1. **Installation & Démarrage**
```
App lancée
  ↓
Firebase.initializeApp()
  ↓
FcmService().initialize()
  ↓
_requestPermissions() → Demande à l'utilisateur
  ↓
refreshToken() → Récupère le token FCM
  ↓
registerFcmToken() → Envoie au backend
  ↓
UserDevice créé avec is_active=True
```

### 2. **Réception de notification**
```
Message FCM reçu
  ↓
Foreground → Notification locale affichée
Background → Tap ouvre l'app
  ↓
NotificationService.refresh() → Récupère les notifications
  ↓
Badge mis à jour
```

### 3. **Désinscription (Logout)**
```
Utilisateur se déconnecte
  ↓
DELETE /notifications/devices/unregister/
  ↓
UserDevice.is_active = False
  ↓
Token reste 30 jours
  ↓
cleanup_inactive_tokens() → Suppression
```

---

## 📁 Fichiers modifiés

| Fichier | Changements |
|---------|------------|
| `backend/notifications/tasks.py` | Ajout tâche `cleanup_inactive_tokens` |
| `backend/resume_backend/settings.py` | Ajout `CELERY_BEAT_SCHEDULE` |
| `lib/services/fcm_service.dart` | ✅ Déjà correct (demande permissions) |
| `android/app/src/main/AndroidManifest.xml` | ✅ Déjà correct (permission présente) |
| `lib/main.dart` | ✅ Déjà correct (initialise FcmService) |

---

## ✅ Checklist de vérification

### Frontend Flutter
- ✅ `AndroidManifest.xml` contient `POST_NOTIFICATIONS`
- ✅ `FcmService.initialize()` appelé au démarrage
- ✅ `_requestPermissions()` demande les permissions
- ✅ Token enregistré via `registerFcmToken()`
- ✅ Handlers de messages configurés

### Backend Django
- ✅ Endpoint `POST /notifications/devices/register/`
- ✅ Endpoint `DELETE /notifications/devices/unregister/`
- ✅ Tâche `cleanup_inactive_tokens` créée
- ✅ Celery Beat schedule configuré
- ✅ Tokens marqués `is_active=False` au logout

---

## 🚀 Déploiement

### 1. Redémarrer Celery Beat
```bash
sudo systemctl restart celery-beat
```

### 2. Redémarrer Celery Worker
```bash
sudo systemctl restart celery
```

### 3. Vérifier les logs
```bash
sudo journalctl -u celery-beat -f
sudo journalctl -u celery -f
```

### 4. Tester manuellement (optionnel)
```bash
# Dans Django shell
from notifications.tasks import cleanup_inactive_tokens
cleanup_inactive_tokens.delay()
```

---

## 📊 Monitoring

### Vérifier les tokens inactifs
```bash
python manage.py shell
>>> from notifications.models import UserDevice
>>> UserDevice.objects.filter(is_active=False).count()
```

### Vérifier les tokens actifs
```bash
>>> UserDevice.objects.filter(is_active=True).count()
```

### Voir les tokens d'un utilisateur
```bash
>>> from django.contrib.auth.models import User
>>> user = User.objects.get(username='john')
>>> user.userdevice_set.all()
```

---

## 💡 Notes

- Les tokens inactifs sont conservés 30 jours pour permettre la récupération
- La suppression est automatique via Celery Beat (2h du matin)
- Aucune suppression immédiate pour éviter les faux positifs
- Les permissions sont demandées une seule fois (gérées par Android)
- Le token est rafraîchi automatiquement quand Firebase le change

---

## 🔗 Endpoints API

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/notifications/devices/register/` | Enregistrer un token FCM |
| DELETE | `/notifications/devices/unregister/` | Désactiver un token FCM |
| GET | `/notifications/` | Lister les notifications |
| POST | `/notifications/{id}/read/` | Marquer comme lue |
| GET | `/notifications/unread-count/` | Compteur non-lues |
