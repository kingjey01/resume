# 🚀 Guide de Déploiement Rapide - Resume+ Backend

## 📋 Résumé des Problèmes Résolus

### Erreurs Identifiées en Production
1. ❌ **Table `auth_user` manquante** → Migrations non exécutées
2. ❌ **Erreur 401 Unauthorized** sur `/api/courses/universites/`, `/filieres/`, `/promotions/`
3. ❌ **Method Not Allowed** sur `/api/auth/register/`

### Solutions Appliquées
1. ✅ Ajout de `permission_classes = [permissions.AllowAny]` sur les endpoints publics
2. ✅ Correction des permissions d'inscription
3. ✅ Guide de migration complet

## 📦 Fichiers Modifiés

### Fichiers Backend à Copier
```
backend/
├── courses/views.py          ← MODIFIÉ (permissions publiques)
├── users/views.py            ← MODIFIÉ (permissions inscription)
├── deploy.sh                 ← NOUVEAU (script automatique)
├── create_test_data.py       ← NOUVEAU (données de test)
├── DEPLOYMENT_GUIDE.md       ← NOUVEAU (guide détaillé)
├── CHANGES_SUMMARY.md        ← NOUVEAU (résumé des changements)
└── README_DEPLOYMENT.md      ← CE FICHIER
```

## 🚀 Déploiement en 3 Étapes

### Étape 1 : Copier les Fichiers

```bash
# Depuis votre machine locale
cd "d:\PROJETS\WINDSURF-STUDENT - Copie\backend"

# Copier les fichiers modifiés vers le serveur
scp courses/views.py user@server:/home/jey/resumecours.gestionhospitaliare.site/backend/courses/
scp users/views.py user@server:/home/jey/resumecours.gestionhospitaliare.site/backend/users/
scp deploy.sh user@server:/home/jey/resumecours.gestionhospitaliare.site/
scp create_test_data.py user@server:/home/jey/resumecours.gestionhospitaliare.site/backend/
```

### Étape 2 : Se Connecter au Serveur

```bash
ssh user@resumecours.gestionhospitaliare.site
cd /home/jey/resumecours.gestionhospitaliare.site
```

### Étape 3 : Exécuter le Déploiement

#### Option A : Script Automatique (Recommandé)
```bash
chmod +x deploy.sh
./deploy.sh
```

#### Option B : Commandes Manuelles
```bash
# Activer l'environnement virtuel
source env/bin/activate

# Appliquer les migrations
python manage.py migrate

# Créer les données de test
python manage.py shell < backend/create_test_data.py

# Collecter les fichiers statiques
python manage.py collectstatic --noinput

# Redémarrer les services
sudo systemctl restart apache2
```

## ✅ Vérification Post-Déploiement

### 1. Tester les Endpoints Publics

```bash
# Test universités
curl https://resumecours.gestionhospitaliare.site/api/courses/universites/

# Test filières
curl https://resumecours.gestionhospitaliare.site/api/courses/filieres/

# Test promotions
curl https://resumecours.gestionhospitaliare.site/api/courses/promotions/
```

**Résultat attendu** : Liste JSON des données (pas d'erreur 401)

### 2. Tester l'Inscription

```bash
curl -X POST https://resumecours.gestionhospitaliare.site/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "nouveau@test.com",
    "password": "Test123!",
    "password2": "Test123!",
    "first_name": "Nouveau",
    "last_name": "Utilisateur",
    "groupe": "ETUDIANT",
    "universite": 1,
    "filiere": 1,
    "promotion": 1
  }'
```

**Résultat attendu** : Tokens JWT et informations utilisateur

### 3. Vérifier les Logs

```bash
tail -f /var/log/apache2/error.log
```

**Résultat attendu** : Pas d'erreurs 401 ou "Method Not Allowed"

## 🔑 Comptes de Test Créés

Après avoir exécuté `create_test_data.py`, vous aurez :

### Compte CP (Chargé de Promotion)
- **Email** : `cp@test.com`
- **Password** : `TestCP123!`
- **Rôle** : CP
- **Permissions** : Peut uploader des enregistrements audio

### Compte Étudiant
- **Email** : `etudiant@test.com`
- **Password** : `TestEtudiant123!`
- **Rôle** : ETUDIANT
- **Permissions** : Peut consulter et acheter des résumés

## 📊 Données de Test Créées

### Universités (5)
- Université de Kinshasa (UNIKIN)
- Université de Lubumbashi (UNILU)
- Université de Kisangani (UNIKIS)
- Université Protestante au Congo (UPC)
- Université Catholique du Congo (UCC)

### Filières (7)
- Informatique
- Médecine
- Droit
- Économie
- Ingénierie
- Lettres
- Sciences

### Promotions (5)
- L1 (Année 1)
- L2 (Année 2)
- L3 (Année 3)
- M1 (Année 4)
- M2 (Année 5)

### Cours (3 exemples en Informatique)
- Introduction à la Programmation (INFO101)
- Structures de Données (INFO201)
- Bases de Données (INFO202)

## 🔧 Commandes Utiles

### Vérifier les Tables
```bash
python manage.py dbshell
> SHOW TABLES;
> exit;
```

### Créer un Superutilisateur
```bash
python manage.py createsuperuser
```

### Voir les Migrations
```bash
python manage.py showmigrations
```

### Collecter les Fichiers Statiques
```bash
python manage.py collectstatic --noinput
```

### Redémarrer les Services
```bash
sudo systemctl restart apache2
sudo systemctl restart gunicorn  # si applicable
```

## 📝 Checklist de Déploiement

- [ ] Fichiers copiés sur le serveur
- [ ] Connexion SSH établie
- [ ] Environnement virtuel activé
- [ ] Migrations appliquées (`python manage.py migrate`)
- [ ] Tables vérifiées dans la base de données
- [ ] Données de test créées
- [ ] Fichiers statiques collectés
- [ ] Services redémarrés
- [ ] Endpoints publics testés (universités, filières, promotions)
- [ ] Inscription testée
- [ ] Connexion testée
- [ ] Logs vérifiés (pas d'erreurs)
- [ ] Application mobile testée

## 🎯 Test depuis l'Application Mobile

1. **Lancer l'application Flutter**
   ```bash
   flutter run
   ```

2. **Tester l'inscription**
   - Ouvrir l'écran d'inscription
   - Vérifier que les listes déroulantes se remplissent :
     - ✅ Universités chargées depuis l'API
     - ✅ Filières chargées depuis l'API
     - ✅ Promotions chargées depuis l'API
   - Remplir le formulaire
   - Soumettre l'inscription
   - ✅ Inscription réussie avec tokens JWT

3. **Tester la connexion**
   - Utiliser les identifiants créés
   - ✅ Connexion réussie

4. **Tester l'upload audio (compte CP)**
   - Se connecter avec `cp@test.com`
   - Aller dans "Enregistrer un cours"
   - Sélectionner un cours
   - Enregistrer un audio
   - ✅ Upload réussi

## ⚠️ Problèmes Courants et Solutions

### Problème : "Table doesn't exist"
**Solution** :
```bash
python manage.py migrate
```

### Problème : "Unauthorized" sur endpoints publics
**Solution** : Vérifier que les fichiers `views.py` modifiés ont bien été copiés

### Problème : "Method Not Allowed"
**Solution** : Redémarrer Apache après avoir copié les fichiers
```bash
sudo systemctl restart apache2
```

### Problème : Listes vides dans l'application
**Solution** : Exécuter le script de création de données
```bash
python manage.py shell < backend/create_test_data.py
```

## 📞 Support

### Logs à Vérifier
```bash
# Logs Apache
tail -f /var/log/apache2/error.log
tail -f /var/log/apache2/access.log

# Logs Django (si configurés)
tail -f /path/to/django/logs/django.log
```

### Commandes de Diagnostic
```bash
# Vérifier le statut des services
sudo systemctl status apache2
sudo systemctl status gunicorn

# Tester la connexion à la base de données
python manage.py check --database default

# Vérifier les migrations
python manage.py showmigrations
```

## 🎉 Résultat Final Attendu

Après avoir suivi ce guide :

✅ **Backend**
- Toutes les tables créées
- Données de test disponibles
- Endpoints publics accessibles
- Inscription et connexion fonctionnelles

✅ **Application Mobile**
- Listes déroulantes remplies dynamiquement
- Inscription possible
- Connexion possible
- Upload audio fonctionnel (pour CP)

✅ **Logs**
- Pas d'erreurs 401 Unauthorized
- Pas d'erreurs "Method Not Allowed"
- Pas d'erreurs "Table doesn't exist"

## 📚 Documentation Complète

Pour plus de détails, consultez :
- `DEPLOYMENT_GUIDE.md` - Guide détaillé de déploiement
- `CHANGES_SUMMARY.md` - Résumé des modifications
- `deploy.sh` - Script automatique de déploiement
- `create_test_data.py` - Script de création de données

---

**Version** : 1.0  
**Date** : 8 Novembre 2025  
**Auteur** : Cascade AI  
**Status** : ✅ Prêt pour le déploiement
