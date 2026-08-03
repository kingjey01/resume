# 🔧 Correction de l'Erreur MySQL

## ❌ Erreur Rencontrée
```
ERROR 1045 (28000): Access denied for user 'jey_resume'@'localhost' (using password: YES)
```

## 🔍 Cause
Le mot de passe MySQL dans votre fichier `.env` ou `settings.py` est incorrect.

## ✅ Solutions

### Solution 1 : Vérifier le Fichier .env

```bash
# Vérifier le contenu du fichier .env
cat .env

# Vous devriez voir quelque chose comme :
# DB_NAME=jey_resume
# DB_USER=jey_resume
# DB_PASSWORD=votre_mot_de_passe
# DB_HOST=localhost
# DB_PORT=3306
```

### Solution 2 : Tester la Connexion MySQL Directement

```bash
# Tester avec le mot de passe du fichier .env
mysql -u jey_resume -p jey_resume

# Si ça ne fonctionne pas, essayez avec root
mysql -u root -p
```

### Solution 3 : Réinitialiser le Mot de Passe MySQL

Si vous avez accès root à MySQL :

```bash
# Se connecter en tant que root
mysql -u root -p

# Dans MySQL, exécuter :
ALTER USER 'jey_resume'@'localhost' IDENTIFIED BY 'nouveau_mot_de_passe';
FLUSH PRIVILEGES;
exit;
```

Puis mettre à jour votre fichier `.env` :
```bash
nano .env
# Modifier DB_PASSWORD=nouveau_mot_de_passe
```

### Solution 4 : Créer un Nouvel Utilisateur MySQL

```bash
# Se connecter en tant que root
mysql -u root -p

# Créer l'utilisateur et la base de données
CREATE DATABASE IF NOT EXISTS jey_resume CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'jey_resume'@'localhost' IDENTIFIED BY 'VotreMotDePasse123!';
GRANT ALL PRIVILEGES ON jey_resume.* TO 'jey_resume'@'localhost';
FLUSH PRIVILEGES;
exit;
```

## 🚀 Après Avoir Corrigé la Connexion

### 1. Tester la Connexion
```bash
python manage.py check --database default
```

### 2. Appliquer les Migrations
```bash
python manage.py migrate
```

### 3. Créer les Données de Test (Script Corrigé)
```bash
# Le script a été corrigé pour correspondre aux modèles
python manage.py shell < create_test_data.py
```

### 4. Vérifier les Tables
```bash
python manage.py dbshell
> SHOW TABLES;
> SELECT * FROM courses_universite;
> exit;
```

## 📝 Note Importante

Le script `create_test_data.py` a été corrigé pour :
- ✅ Supprimer le champ `code` qui n'existe pas dans `Universite`
- ✅ Utiliser les noms (CharField) au lieu des objets pour `Course.university` et `Course.filiere`
- ✅ Ajouter une meilleure gestion des erreurs

## ✅ Commandes Complètes à Exécuter

```bash
# 1. Vérifier la connexion
python manage.py check --database default

# 2. Appliquer les migrations
python manage.py migrate

# 3. Créer les données de test
python manage.py shell < create_test_data.py

# 4. Vérifier les données
python manage.py shell
>>> from courses.models import Universite, Filiere, Promotion
>>> print(f"Universités: {Universite.objects.count()}")
>>> print(f"Filières: {Filiere.objects.count()}")
>>> print(f"Promotions: {Promotion.objects.count()}")
>>> exit()

# 5. Redémarrer les services
sudo systemctl restart apache2
```

## 🧪 Test Final

```bash
# Tester les endpoints
curl https://resumecours.gestionhospitaliare.site/api/courses/universites/
curl https://resumecours.gestionhospitaliare.site/api/courses/filieres/
curl https://resumecours.gestionhospitaliare.site/api/courses/promotions/
```

Résultat attendu : Liste JSON des données (pas d'erreur 401)
