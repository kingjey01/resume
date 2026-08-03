# Solution pour le problème SQLite3 en production

## Problème
```
ModuleNotFoundError: No module named '_sqlite3'
```

## Solutions possibles

### Option 1: Installation rapide de SQLite3 (Recommandée)

```bash
# En tant que root
yum install -y sqlite-devel python3-devel gcc

# Réinstaller Python dans l'environnement virtuel
cd /home/jey/resumecours.gestionhospitaliare.site
source env/bin/activate
pip uninstall -y sqlite3
pip install pysqlite3-binary

# Tester
python -c "import sqlite3; print('SQLite3 OK')"
```

### Option 2: Utiliser PostgreSQL (Production recommandée)

```bash
# 1. Installer PostgreSQL
yum install -y postgresql postgresql-server postgresql-devel python3-psycopg2

# 2. Initialiser PostgreSQL
postgresql-setup initdb
systemctl enable postgresql
systemctl start postgresql

# 3. Créer la base de données
sudo -u postgres createdb resume_plus_db
sudo -u postgres createuser resume_user
sudo -u postgres psql -c "ALTER USER resume_user WITH PASSWORD 'SecurePassword123!';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE resume_plus_db TO resume_user;"

# 4. Installer psycopg2 dans l'environnement virtuel
cd /home/jey/resumecours.gestionhospitaliare.site
source env/bin/activate
pip install psycopg2-binary

# 5. Mettre à jour settings.py avec la configuration PostgreSQL
```

### Option 3: Script de création de données sans shell Django

```bash
# Utiliser le script standalone
cd /home/jey/resumecours.gestionhospitaliare.site/backend
source ../env/bin/activate
python create_test_data_postgresql.py
```

## Configuration recommandée pour la production

1. **Utiliser PostgreSQL** au lieu de SQLite3
2. **Variables d'environnement** pour les secrets
3. **Fichier .env** pour la configuration

### Créer le fichier .env

```bash
cat > /home/jey/resumecours.gestionhospitaliare.site/backend/.env << EOF
DEBUG=False
SECRET_KEY=your-super-secret-key-here
DB_NAME=resume_plus_db
DB_USER=resume_user
DB_PASSWORD=SecurePassword123!
DB_HOST=localhost
DB_PORT=5432
ALLOWED_HOSTS=resumecours.gestionhospitaliare.site,www.resumecours.gestionhospitaliare.site
EOF
```

### Installer python-decouple

```bash
source env/bin/activate
pip install python-decouple
```

## Test rapide

```bash
# Test de la base de données
cd /home/jey/resumecours.gestionhospitaliare.site/backend
source ../env/bin/activate

# Avec SQLite3 (si réparé)
python manage.py check

# Avec PostgreSQL
python manage.py migrate
python create_test_data_postgresql.py
```

## Commandes de dépannage

```bash
# Vérifier Python et SQLite3
python -c "import sqlite3; print(sqlite3.sqlite_version)"

# Vérifier PostgreSQL
sudo -u postgres psql -c "SELECT version();"

# Vérifier les modules Python
pip list | grep -E "(sqlite|psycopg)"

# Logs Django
tail -f /home/jey/resumecours.gestionhospitaliare.site/backend/django.log
```