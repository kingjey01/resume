# Site Web Résumé+

Site statique contenant la politique de confidentialité, les conditions d'utilisation
et les informations à propos de l'application Résumé+.

## Déploiement

### Option 1 — GitHub Pages (gratuit)
1. Créer un dépôt GitHub nommé `resumeplus-site`
2. Pousser le contenu du dossier `website/` sur la branche `main`
3. Aller dans Settings → Pages → choisir `main` comme source
4. Le site sera disponible à `https://<username>.github.io/resumeplus-site/`

### Option 2 — Netlify (gratuit)
1. Glisser le dossier `website/` sur https://app.netlify.com
2. Netlify génère un URL du type `resumeplus.netlify.app`

### Option 3 — VPS / Hébergement FTP
1. Copier les 3 fichiers (index.html, style.css, script.js) sur le serveur
2. Configurer le domaine dans le panneau d'hébergement

## Utilisation dans Google Play Console

Dans Google Play Console, aller dans :
- `Politique` → `Politique de confidentialité`
- Coller l'URL du site déployé

## Fichiers
- `index.html` — page principale (contient tout le contenu)
- `style.css` — styles responsives
- `script.js` — interactions (navigation, scroll)
