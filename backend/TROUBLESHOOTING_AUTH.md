# 🔧 Guide de Dépannage - Problèmes d'Authentification

Ce guide vous aide à résoudre les erreurs d'authentification dans Resume+.

## 🚨 Erreurs Courantes dans les Logs

### 1. Bad Request: /api/auth/login/
**Cause :** Données de connexion invalides ou format incorrect

**Solutions :**
```bash
# Vérifier que l'utilisateur existe
python manage.py shell
>>> from django.contrib.auth.models import User
>>> User.objects.filter(email='etudiant1@gmail.com').exists()

# Créer des utilisateurs de test si nécessaire
python run_seed.py
```

### 2. Not Found: /api/auth/user/
**Cause :** Endpoint manquant (maintenant corrigé)

**Solution :** L'endpoint a été ajouté dans `users/urls.py` et `users/views.py`

### 3. Unauthorized: /api/summaries/ et /api/purchases/
**Cause :** Token JWT invalide, expiré ou mal formaté

## 🛠️ Solutions Étape par Étape

### Étape 1 : Vérifier le Serveur Django
```bash
cd backend
python manage.py runserver
```
Le serveur doit être accessible sur http://127.0.0.1:8000

### Étape 2 : Créer des Données de Test
```bash
# Exécuter le seed pour créer des utilisateurs de test
python run_seed.py

# Ou utiliser le script simple
python manage.py shell < create_test_data.py
```

### Étape 3 : Tester l'API Manuellement
```bash
# Tester la connexion
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "etudiant1@gmail.com", "password": "Etudiant2024!"}'

# Utiliser le token retourné pour tester les autres endpoints
curl -X GET http://127.0.0.1:8000/api/summaries/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Étape 4 : Vérifier la Configuration de l'App Mobile

Dans votre service API Flutter (`api_service.dart`), assurez-vous que :

1. **L'URL de base est correcte :**
```dart
static const String baseUrl = 'https://resumecours.gestionhospitaliare.site/api';
// ou pour le développement local :
// static const String baseUrl = 'http://127.0.0.1:8000/api';
```

2. **Les headers d'authentification sont corrects :**
```dart
final headers = {
  'Content-Type': 'application/json',
  'Authorization': 'Bearer $token',
};
```

3. **La gestion des erreurs est appropriée :**
```dart
if (response.statusCode == 401) {
  // Token expiré, rediriger vers la connexion
  await _storageService.deleteToken();
  // Rediriger vers l'écran de connexion
}
```

## 🔍 Diagnostic Avancé

### Vérifier les Tokens JWT
```python
# Dans Django shell
python manage.py shell

from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User

user = User.objects.get(email='etudiant1@gmail.com')
refresh = RefreshToken.for_user(user)
print(f"Access Token: {refresh.access_token}")
print(f"Refresh Token: {refresh}")
```

### Vérifier les Permissions
```python
# Vérifier les permissions d'un utilisateur
user = User.objects.get(email='etudiant1@gmail.com')
print(f"User: {user.username}")
print(f"Is Active: {user.is_active}")
print(f"Profile: {user.profile.groupe}")
```

### Logs de Debug
Activez les logs détaillés dans `settings.py` :
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'users': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'courses': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## 📱 Configuration App Mobile

### 1. Vérifier l'URL de Production
Dans `lib/services/api_service.dart`, l'URL doit pointer vers votre serveur :
```dart
static const String baseUrl = 'https://resumecours.gestionhospitaliare.site/api';
```

### 2. Gestion des Certificats SSL
Si vous avez des erreurs SSL, ajoutez dans `android/app/src/main/AndroidManifest.xml` :
```xml
<application
    android:usesCleartextTraffic="true"
    android:networkSecurityConfig="@xml/network_security_config">
```

### 3. Permissions Réseau
Vérifiez que les permissions réseau sont accordées dans `AndroidManifest.xml` :
```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
```

## 🔧 Commandes de Dépannage Rapide

```bash
# 1. Redémarrer le serveur Django
cd backend
python manage.py runserver

# 2. Recréer la base de données (ATTENTION: efface toutes les données)
python manage.py flush
python manage.py migrate
python run_seed.py

# 3. Tester l'API
python test_api_auth.py

# 4. Vérifier les utilisateurs existants
python manage.py shell -c "from django.contrib.auth.models import User; print([u.email for u in User.objects.all()])"

# 5. Créer un superutilisateur
python manage.py createsuperuser
```

## 📊 Comptes de Test Disponibles

Après avoir exécuté `python run_seed.py` :

| Email | Password | Rôle |
|-------|----------|------|
| admin@resumeplus.cd | AdminResume2024! | Administrateur |
| cp.info@unikin.cd | CPInfo2024! | Chef de Promotion |
| etudiant1@gmail.com | Etudiant2024! | Étudiant |
| etudiant2@gmail.com | Etudiant2024! | Étudiant |

## 🚀 Vérification Finale

1. ✅ Serveur Django en cours d'exécution
2. ✅ Base de données avec des utilisateurs de test
3. ✅ API accessible depuis l'app mobile
4. ✅ Tokens JWT générés correctement
5. ✅ Permissions configurées correctement

Si tous ces points sont verts, votre authentification devrait fonctionner !

---

**Créé par Kiro IDE** 🤖  
*Pour Resume+ Application*