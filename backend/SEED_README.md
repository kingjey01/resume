# Guide de création des données de test avec MySQL

## Problème résolu
Le problème `ModuleNotFoundError: No module named '_sqlite3'` vient du fait que Django essaie de charger SQLite3 même si vous utilisez MySQL.

## Solution rapide

### 1. Corriger les settings pour MySQL
```bash
cd /home/jey/resumecours.gestionhospitaliare.site/backend
source ../env/bin/activate
python fix_settings_mysql.py
```

### 2. Configurer les variables d'environnement
Éditez le fichier `.env` créé avec vos vraies informations MySQL :
```bash
nano .env
```

Exemple de configuration :
```env
DEBUG=False
SECRET_KEY=votre-cle-secrete-super-longue-et-complexe

DB_NAME=resume_plus_db
DB_USER=votre_utilisateur_mysql
DB_PASSWORD=votre_mot_de_passe_mysql
DB_HOST=localhost
DB_PORT=3306

ALLOWED_HOSTS=resumecours.gestionhospitaliare.site,www.resumecours.gestionhospitaliare.site
```

### 3. Installer les dépendances
```bash
pip install python-decouple mysqlclient
```

### 4. Créer les données de test
```bash
# Méthode 1: Script standalone (recommandé)
python create_test_data_mysql.py

# Méthode 2: Via Django (si settings.py est corrigé)
python manage.py migrate
python manage.py shell < create_test_data.py
```

## Vérification de la configuration MySQL

### Tester la connexion MySQL
```bash
mysql -u votre_utilisateur -p -h localhost resume_plus_db
```

### Vérifier les tables Django
```bash
python manage.py showmigrations
python manage.py migrate --dry-run
```

### Tester l'API
```bash
python manage.py runserver 0.0.0.0:8000
```

## Comptes de test créés

Une fois les données créées, vous aurez ces comptes :

### 👨‍🏫 Compte CP (Chargé de Promotion)
- **Email:** cp@test.com
- **Password:** TestCP123!
- **Rôle:** CP

### 👨‍🎓 Compte Étudiant
- **Email:** etudiant@test.com  
- **Password:** TestEtudiant123!
- **Rôle:** ETUDIANT

### 👨‍💼 Compte Admin
- **Email:** admin@test.com
- **Password:** AdminTest123!
- **Rôle:** ADMIN (Superuser)

## Données créées

- **5 Universités** (Kinshasa, Lubumbashi, etc.)
- **7 Filières** (Informatique, Médecine, Droit, etc.)
- **5 Promotions** (L1, L2, L3, M1, M2)
- **5 Cours** d'exemple en Informatique
- **3 Utilisateurs** de test

## Dépannage

### Erreur de connexion MySQL
```bash
# Vérifier que MySQL fonctionne
sudo systemctl status mysql
sudo systemctl start mysql

# Vérifier les permissions
mysql -u root -p
GRANT ALL PRIVILEGES ON resume_plus_db.* TO 'votre_utilisateur'@'localhost';
FLUSH PRIVILEGES;
```

### Erreur de module Python
```bash
# Réinstaller les dépendances MySQL
pip uninstall mysqlclient
pip install mysqlclient

# Alternative si mysqlclient pose problème
pip install PyMySQL
```

### Erreur de migration
```bash
# Réinitialiser les migrations
python manage.py migrate --fake-initial
python manage.py migrate
```

## Variables d'environnement importantes

Assurez-vous que ces variables sont définies :
- `DB_NAME` : Nom de votre base de données MySQL
- `DB_USER` : Utilisateur MySQL
- `DB_PASSWORD` : Mot de passe MySQL  
- `DB_HOST` : Hôte MySQL (généralement localhost)
- `DB_PORT` : Port MySQL (généralement 3306)

## Test final

```bash
# Tester que tout fonctionne
python manage.py check
python manage.py test
curl http://localhost:8000/api/courses/
```