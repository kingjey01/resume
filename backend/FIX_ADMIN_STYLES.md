# 🎨 Correction du Style de l'Admin Django

## ❌ Problème
L'admin Django n'a pas de style après `collectstatic` en production.

## 🔍 Cause
En production (`DEBUG=False`), Django ne sert pas les fichiers statiques. C'est le rôle d'Apache ou Nginx.

## ✅ Solutions

### Solution 1 : Configuration Apache (Recommandée)

#### Étape 1 : Collecter les fichiers statiques
```bash
cd /home/jey/resumecours.gestionhospitaliare.site
source env/bin/activate
python manage.py collectstatic --noinput

# Vérifier que les fichiers existent
ls -la staticfiles/admin/css/
```

#### Étape 2 : Trouver votre fichier de configuration Apache
```bash
# Chercher le fichier de configuration
ls /etc/apache2/sites-available/
ls /etc/httpd/conf.d/

# Ou chercher par nom de domaine
grep -r "resumecours" /etc/apache2/
grep -r "resumecours" /etc/httpd/
```

#### Étape 3 : Modifier la configuration Apache

```bash
# Exemple pour Apache2
sudo nano /etc/apache2/sites-available/resumecours.conf

# Ou pour httpd
sudo nano /etc/httpd/conf.d/resumecours.conf
```

**Contenu à ajouter/modifier :**

```apache
<VirtualHost *:80>
    ServerName resumecours.gestionhospitaliare.site
    ServerAlias www.resumecours.gestionhospitaliare.site

    # ============================================
    # FICHIERS STATIQUES - IMPORTANT !
    # ============================================
    Alias /static /home/jey/resumecours.gestionhospitaliare.site/staticfiles
    <Directory /home/jey/resumecours.gestionhospitaliare.site/staticfiles>
        Require all granted
        Options -Indexes
        AllowOverride None
    </Directory>

    # ============================================
    # FICHIERS MÉDIA
    # ============================================
    Alias /media /home/jey/resumecours.gestionhospitaliare.site/media
    <Directory /home/jey/resumecours.gestionhospitaliare.site/media>
        Require all granted
        Options -Indexes
        AllowOverride None
    </Directory>

    # ============================================
    # WSGI DJANGO
    # ============================================
    WSGIDaemonProcess resumecours \
        python-path=/home/jey/resumecours.gestionhospitaliare.site/backend \
        python-home=/home/jey/resumecours.gestionhospitaliare.site/env
    WSGIProcessGroup resumecours
    WSGIScriptAlias / /home/jey/resumecours.gestionhospitaliare.site/backend/resume_backend/wsgi.py

    <Directory /home/jey/resumecours.gestionhospitaliare.site/backend/resume_backend>
        <Files wsgi.py>
            Require all granted
        </Files>
    </Directory>

    # ============================================
    # LOGS
    # ============================================
    ErrorLog ${APACHE_LOG_DIR}/resumecours_error.log
    CustomLog ${APACHE_LOG_DIR}/resumecours_access.log combined
</VirtualHost>
```

#### Étape 4 : Vérifier les permissions
```bash
# Donner les bonnes permissions
sudo chown -R www-data:www-data /home/jey/resumecours.gestionhospitaliare.site/staticfiles
sudo chown -R www-data:www-data /home/jey/resumecours.gestionhospitaliare.site/media
sudo chmod -R 755 /home/jey/resumecours.gestionhospitaliare.site/staticfiles
sudo chmod -R 755 /home/jey/resumecours.gestionhospitaliare.site/media
```

#### Étape 5 : Redémarrer Apache
```bash
# Tester la configuration
sudo apachectl configtest
# ou
sudo apache2ctl configtest

# Si OK, redémarrer
sudo systemctl restart apache2
# ou
sudo systemctl restart httpd
```

### Solution 2 : Configuration Nginx (Alternative)

Si vous utilisez Nginx avec Gunicorn :

```bash
sudo nano /etc/nginx/sites-available/resumecours
```

**Contenu :**

```nginx
server {
    listen 80;
    server_name resumecours.gestionhospitaliare.site www.resumecours.gestionhospitaliare.site;

    client_max_body_size 100M;

    # Fichiers statiques
    location /static/ {
        alias /home/jey/resumecours.gestionhospitaliare.site/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Fichiers média
    location /media/ {
        alias /home/jey/resumecours.gestionhospitaliare.site/media/;
        expires 30d;
    }

    # Proxy vers Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Puis :
```bash
sudo ln -s /etc/nginx/sites-available/resumecours /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Solution 3 : Whitenoise (Alternative Simple)

Si vous ne voulez pas configurer Apache/Nginx, utilisez Whitenoise :

#### Étape 1 : Installer Whitenoise
```bash
pip install whitenoise
```

#### Étape 2 : Modifier `settings.py`

Ajoutez dans `MIDDLEWARE` (juste après `SecurityMiddleware`) :

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ← AJOUTER ICI
    'corsheaders.middleware.CorsMiddleware',
    # ... reste du middleware
]
```

Ajoutez à la fin de `settings.py` :

```python
# Whitenoise configuration
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

#### Étape 3 : Collecter les fichiers statiques
```bash
python manage.py collectstatic --noinput
```

#### Étape 4 : Redémarrer
```bash
sudo systemctl restart apache2
# ou
sudo systemctl restart gunicorn
```

## 🧪 Vérification

### 1. Tester l'accès aux fichiers statiques
```bash
# Depuis le serveur
curl -I https://resumecours.gestionhospitaliare.site/static/admin/css/base.css

# Résultat attendu : HTTP/1.1 200 OK
```

### 2. Vérifier dans le navigateur
```
https://resumecours.gestionhospitaliare.site/admin/
```

L'admin devrait maintenant avoir du style !

### 3. Vérifier les logs
```bash
tail -f /var/log/apache2/error.log
# ou
tail -f /var/log/httpd/error_log
```

## 🔍 Diagnostic

### Commandes utiles pour identifier le problème

```bash
# 1. Vérifier que les fichiers statiques existent
ls -la /home/jey/resumecours.gestionhospitaliare.site/staticfiles/admin/css/

# 2. Vérifier les permissions
ls -ld /home/jey/resumecours.gestionhospitaliare.site/staticfiles/

# 3. Tester l'accès direct
curl -I http://localhost/static/admin/css/base.css

# 4. Vérifier la configuration Apache
sudo apachectl -S
# ou
sudo apache2ctl -S

# 5. Vérifier les modules Apache chargés
apache2ctl -M | grep alias
# Doit afficher : alias_module
```

## ⚠️ Problèmes Courants

### Problème 1 : "403 Forbidden" sur /static/
**Solution** : Vérifier les permissions
```bash
sudo chmod -R 755 /home/jey/resumecours.gestionhospitaliare.site/staticfiles
sudo chown -R www-data:www-data /home/jey/resumecours.gestionhospitaliare.site/staticfiles
```

### Problème 2 : "404 Not Found" sur /static/
**Solution** : Vérifier l'Alias dans Apache
```apache
Alias /static /home/jey/resumecours.gestionhospitaliare.site/staticfiles
```

### Problème 3 : Module alias non chargé
**Solution** : Activer le module
```bash
sudo a2enmod alias
sudo systemctl restart apache2
```

## 📋 Checklist

- [ ] `collectstatic` exécuté
- [ ] Fichiers dans `staticfiles/admin/css/` existent
- [ ] Configuration Apache/Nginx modifiée
- [ ] Alias `/static` configuré
- [ ] Permissions correctes (755 pour dossiers, 644 pour fichiers)
- [ ] Propriétaire www-data
- [ ] Apache/Nginx redémarré
- [ ] Test curl réussi
- [ ] Admin a du style dans le navigateur

## 🎯 Résultat Attendu

Après avoir suivi ces étapes :
- ✅ L'admin Django a du style
- ✅ Les CSS et JS se chargent correctement
- ✅ Pas d'erreurs 404 dans la console du navigateur

---

**Recommandation** : Utilisez la Solution 1 (Apache) ou Solution 3 (Whitenoise) selon votre configuration actuelle.
