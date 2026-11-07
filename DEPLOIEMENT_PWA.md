# Déploiement de la PWA Muhtasari+

URL cible : **`https://resumecours.gestionhospitaliare.site/`** (même domaine de
production que l'application Android, qui appelle `/api`).

Cette procédure ne concerne **que la cible Web/PWA**. Elle ne modifie ni le
package Android, ni la signature, ni les versions, ni les paiements mobiles.
Le backend Django et ses routes `/api` restent inchangés.

## 1. Construire le bundle Web

Depuis `resume/` :

```bash
flutter build web --release --base-href=/
```

Le bundle est produit dans `build/web/`. Le `--base-href=/` sert la PWA à la
racine du domaine.

> Si Git Bash réécrit le chemin, préfixer par `MSYS_NO_PATHCONV=1`.

## 2. Copier sur le serveur

Créer un répertoire **distinct** pour les fichiers statiques de la PWA, par
exemple `pwa/`, afin de ne jamais écraser le backend ni un éventuel fichier
Android :

```bash
scp -r build/web/* jey@<serveur>:/home/jey/resumecours.gestionhospitaliare.site/pwa/
```

Sauvegarder la version précédente :

```bash
ssh jey@<serveur>
cd /home/jey/resumecours.gestionhospitaliare.site
cp -r pwa pwa.backup.$(date +%Y%m%d_%H%M%S)
```

## 3. Configuration Apache — coexistence PWA / API

**Point critique :** la racine du domaine sert aujourd'hui le backend Django.
Il faut servir les fichiers de `pwa/` pour le Web, tout en laissant
`/api`, `/admin`, `/static` et `/media` à Django.

Avant de modifier quoi que ce soit, inspecter la configuration actuelle :

```bash
sudo apachectl -S
sudo grep -rn "DocumentRoot\|WSGIScriptAlias\|ProxyPass" /etc/httpd/conf.d/ /etc/httpd/conf/
```

Sauvegarder le vhost, puis appliquer l'une des deux variantes.

### Variante A — Django derrière Gunicorn (ProxyPass)

Si le vhost actuel relaie vers Gunicorn (port 8000), remplacer le service
statique racine par `pwa/` et garder les relais API :

```apache
DocumentRoot /home/jey/resumecours.gestionhospitaliare.site/pwa

<Directory "/home/jey/resumecours.gestionhospitaliare.site/pwa">
    Options -Indexes +FollowSymLinks
    AllowOverride None
    Require all granted
    DirectoryIndex index.html

    <IfModule mod_mime.c>
        AddType application/manifest+json .webmanifest
        AddType application/wasm .wasm
    </IfModule>

    # Repli SPA : toute URL inconnue retombe sur index.html.
    <IfModule mod_rewrite.c>
        RewriteEngine On
        RewriteCond %{REQUEST_FILENAME} !-f
        RewriteCond %{REQUEST_FILENAME} !-d
        RewriteRule ^ /index.html [L]
    </IfModule>

    # Fichiers qui doivent TOUJOURS être revalidés (mise à jour PWA).
    <FilesMatch "^(index\.html|flutter_bootstrap\.js|main\.dart\.js|sw\.js|manifest\.json|version\.json|firebase-config\.js)$">
        Header always set Cache-Control "no-cache, no-store, must-revalidate"
    </FilesMatch>

    # Assets immuables.
    <FilesMatch "\.(wasm|png|jpg|jpeg|gif|svg|webp|ttf|otf|woff2?)$">
        Header set Cache-Control "public, max-age=604800"
    </FilesMatch>

    <IfModule mod_deflate.c>
        AddOutputFilterByType DEFLATE text/html text/css application/javascript application/json application/wasm image/svg+xml
    </IfModule>
</Directory>

# Garder/ajouter les relais vers le backend Django existant :
ProxyPass        /api  http://127.0.0.1:8000/api
ProxyPassReverse /api  http://127.0.0.1:8000/api
ProxyPass        /admin http://127.0.0.1:8000/admin
ProxyPassReverse /admin http://127.0.0.1:8000/admin
ProxyPass        /static http://127.0.0.1:8000/static
ProxyPassReverse /static http://127.0.0.1:8000/static
ProxyPass        /media http://127.0.0.1:8000/media
ProxyPassReverse /media http://127.0.0.1:8000/media
```

### Variante B — Django avec mod_wsgi

Si le vhost utilise `WSGIScriptAlias / ...`, ne pas le supprimer. Servir la
PWA depuis un sous-répertoire (`/app/`) est alors la solution la plus sûre :
reconstruire avec `--base-href=/app/` et suivre la variante précédente en
remplaçant `DocumentRoot` par un `Alias /app ...`, sans toucher au
`WSGIScriptAlias /`.

> Pourquoi cette prudence : `WSGIScriptAlias /` capture toutes les URL. Une
> PWA à la racine exigerait de réécrire le routage Django, avec un risque réel
> de couper `/api` et donc l'application Android en production.

Recharger Apache après essai de configuration :

```bash
sudo apachectl configtest && sudo systemctl reload httpd
```

## 4. Configurer le push Web (Firebase)

Le code est intégré ; il ne manque que les identifiants Web, car Firebase doit
connaître ce nouveau client.

Les clés ne sont **jamais versionnées**. Elles sont lues depuis `.env.pwa`
(ignoré par Git) ou depuis les variables d'environnement du build.

1. Console Firebase → projet **`resumeplus-2d47f`** → ⚙️ Paramètres du projet
   → **Vos applications** → ajouter une application **Web**
   (par exemple `Muhtasari PWA`).
2. Copier `.env.pwa.example` en `.env.pwa`, puis renseigner :
   `FIREBASE_API_KEY`, `FIREBASE_APP_ID`, `FIREBASE_PROJECT_ID`,
   `FIREBASE_MESSAGING_SENDER_ID`, et éventuellement `FIREBASE_AUTH_DOMAIN`,
   `FIREBASE_STORAGE_BUCKET`, `FIREBASE_MEASUREMENT_ID`.
3. Console Firebase → **Cloud Messaging** → **Certificats push Web** →
   générer/copier la **paire de clés VAPID**, puis renseigner
   `FIREBASE_VAPID_KEY` dans `.env.pwa`.
4. Générer le fichier consommé par la page et le service worker :
   ```bash
   dart run tool/generate_firebase_config.dart
   ```
   Il produit `web/firebase-config.js` (ignoré par Git).
5. Reconstruire (`flutter build web --release --base-href=/`) et redéployer.

En CI ou sur un autre poste, il suffit d'exporter les mêmes variables
d'environnement avant l'étape 4 ; aucune clé n'est écrite dans le dépôt.
Si une variable manque, le script l'indique et le push Web reste désactivé
sans erreur.

Le backend envoie déjà les notifications à tous les appareils enregistrés
(`UserDevice.fcm_token`), Web compris (`device_type = 'web'`). Le service
worker `firebase-messaging-sw.js` affiche les notifications en arrière-plan ;
`sw.js` continue de gérer le cache et le hors ligne sur un scope distinct.

### Limites du push sur iOS

- Web Push fonctionne sur **iOS 16.4+**, uniquement pour une PWA **installée
  sur l'écran d'accueil** et après autorisation des notifications.
- Sur les versions antérieures, la liste et le badge de notifications restent
  fonctionnels par polling.

## 5. Enregistrement audio Web

L'écran `RecordAudioScreenWebSafe` enregistre réellement via `MediaRecorder` :

- Chrome/Edge/Android : Opus dans WebM ;
- Safari : AAC dans MP4 (si Opus indisponible) ;
- le micro est demandé par le navigateur ; **HTTPS obligatoire** en production ;
- l'onglet doit rester ouvert pendant l'enregistrement (pas d'enregistrement
  en arrière-plan dans un navigateur).

Les octets réels sont envoyés au même endpoint `/courses/sessions/upload-audio/`
que l'application mobile. Aucun changement backend n'est nécessaire.

## 6. Vérifications après déploiement

```bash
curl -I https://resumecours.gestionhospitaliare.site/
curl -I https://resumecours.gestionhospitaliare.site/sw.js
curl -I https://resumecours.gestionhospitaliare.site/manifest.json
curl -I https://resumecours.gestionhospitaliare.site/api/health/
```

Attendu : la PWA répond `200 text/html`, `sw.js` en `application/javascript`
avec `Cache-Control: no-cache`, le manifeste est servi, et **`/api/health/`
répond toujours** (l'application Android ne doit pas être coupée).

Dans Chrome → `DevTools → Application` :

- **Manifest** : « Muhtasari+ », icônes 192/512, `standalone`.
- **Service Workers** : `sw.js` activé ; `firebase-messaging-sw.js` apparaît
  après la demande de permission de notifications.
- **Cache Storage** : `muhtasari-pwa-v1` rempli.
- Recharger hors connexion : l'application démarre depuis le cache.

Sur iPhone/iPad (Safari) : Partager → **Sur l'écran d'accueil**, ouvrir
l'icône, autoriser les notifications si demandé, tester connexion, audio,
achats et QCM.

## 7. Mise à jour

1. Incrémenter `CACHE_VERSION` dans `web/sw.js` si la stratégie de cache change.
2. Reconstruire et recopier le bundle.
3. `sw.js`, `index.html`, `main.dart.js` et `firebase-config.js` sont servis
   en `no-cache` ; un rechargement récupère la nouvelle version.

## 8. Retour arrière

```bash
cd /home/jey/resumecours.gestionhospitaliare.site
rm -rf pwa && mv pwa.backup.<date> pwa
sudo systemctl reload httpd
```

## 9. Non-régression Android

- Aucune build Android/AAB/IPA n'est produite par cette mission.
- `git status` : aucun fichier sous `android/` modifié.
- Aucun changement de package ID, de signature, de version ni de paiement.
- Vérifier après déploiement que `https://resumecours.gestionhospitaliare.site/api/`
  répond toujours (connexion et paiements Android).
- Ne pas publier de nouvelle version Android dans le cadre de cette mise en œuvre.
