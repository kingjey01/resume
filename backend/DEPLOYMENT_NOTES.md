# Notes de Déploiement - Mise à jour de l'authentification JWT

Ce document décrit les modifications apportées pour résoudre les problèmes d'authentification JWT.

## Fichiers modifiés

### 1. `users/views.py`
- Ajout de logs détaillés dans `profile_view`
- Meilleure gestion des erreurs
- Ajout d'un endpoint de test `/api/auth/test/`

### 2. `users/middleware.py` (NOUVEAU)
```python
# Contenu du fichier à créer dans users/middleware.py
# [Le contenu complet du fichier middleware.py que nous avons créé]
```

### 3. `resume_backend/settings.py`

#### Configuration JWT mise à jour :
```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer', 'JWT'),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'JTI_CLAIM': 'jti',
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}
```

#### Configuration CORS mise à jour :
```python
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = True  # À restreindre en production si possible

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://resumecours.gestionhospitaliare.site",
    "https://www.resumecours.gestionhospitaliare.site",
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]
```

#### Middleware mis à jour dans `MIDDLEWARE` :
```python
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middlewareAuthenticationMiddleware',
    'users.middleware.JWTAuthenticationMiddleware',  # Nouveau middleware
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

## Étapes de déploiement

1. **Arrêter le serveur** :
   ```bash
   sudo systemctl stop apache2  # ou le service que vous utilisez
   ```

2. **Mettre à jour les fichiers** :
   - Copier les fichiers modifiés sur le serveur
   - S'assurer que les permissions sont correctes

3. **Appliquer les migrations** :
   ```bash
   source /chemin/vers/votre/env/bin/activate
   cd /chemin/vers/votre/projet
   python manage.py migrate 
   ```

4. **Collecter les fichiers statiques** :
   ```bash
   python manage.py collectstatic --noinput
   ```

5. **Redémarrer le serveur** :
   ```bash
   sudo systemctl start apache2
   ```

## Tests à effectuer après déploiement

1. **Tester la connexion** :
   ```bash
   curl -X POST https://resumecours.gestionhospitaliare.site/api/auth/login/ \
     -H "Content-Type: application/json" \
     -d '{"email": "yeta@gmail.com", "password": "yeta123test!"}'
   ```

2. **Tester l'accès au profil** (avec le token reçu) :
   ```bash
   curl -X GET https://resumecours.gestionhospitaliare.site/api/auth/profile/ \
     -H "Authorization: Bearer VOTRE_TOKEN_ICI" \
     -H "Content-Type: application/json"
   ```

3. **Vérifier les logs** :
   ```bash
   tail -f /var/log/apache2/error.log
   # Ou pour le fichier de log personnalisé
   tail -f /chemin/vers/votre/projet/debug.log
   ```

## Dépannage

Si vous rencontrez des erreurs :
1. Vérifiez les logs d'erreur
2. Vérifiez que le token est correctement formaté
3. Assurez-vous que le middleware est correctement installé et configuré
4. Vérifiez les permissions des fichiers et dossiers

## Rollback

En cas de problème, pour revenir à la version précédente :
1. Restaurer la sauvegarde de la base de données
2. Revenir à la version précédente du code
3. Redémarrer le serveur
