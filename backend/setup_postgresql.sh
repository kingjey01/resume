#!/bin/bash

echo "🐘 Configuration de PostgreSQL pour la production"
echo "================================================"

# Installer PostgreSQL
echo "📦 Installation de PostgreSQL..."
yum install -y postgresql postgresql-server postgresql-devel || apt-get install -y postgresql postgresql-contrib libpq-dev

# Initialiser la base de données (CentOS/RHEL)
if command -v postgresql-setup >/dev/null 2>&1; then
    postgresql-setup initdb
    systemctl enable postgresql
    systemctl start postgresql
fi

# Démarrer PostgreSQL (Ubuntu/Debian)
if command -v systemctl >/dev/null 2>&1; then
    systemctl enable postgresql
    systemctl start postgresql
fi

# Créer la base de données et l'utilisateur
echo "🔧 Configuration de la base de données..."
sudo -u postgres psql << EOF
CREATE DATABASE resume_plus_db;
CREATE USER resume_user WITH PASSWORD 'SecurePassword123!';
GRANT ALL PRIVILEGES ON DATABASE resume_plus_db TO resume_user;
ALTER USER resume_user CREATEDB;
\q
EOF

echo "✅ PostgreSQL configuré avec succès!"
echo ""
echo "📝 Informations de connexion:"
echo "  Database: resume_plus_db"
echo "  User: resume_user"
echo "  Password: SecurePassword123!"
echo ""
echo "🔄 Mettez à jour votre settings.py avec ces informations"