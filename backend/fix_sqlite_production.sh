#!/bin/bash

echo "🔧 Installation de SQLite3 pour Python en production"
echo "=================================================="

# Vérifier si nous sommes root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Ce script doit être exécuté en tant que root"
    exit 1
fi

# Installer les dépendances SQLite3
echo "📦 Installation des paquets SQLite3..."
yum install -y sqlite-devel sqlite3 || apt-get install -y libsqlite3-dev sqlite3

# Réinstaller Python avec le support SQLite3
echo "🐍 Réinstallation de Python avec support SQLite3..."

# Sauvegarder l'environnement virtuel actuel
if [ -d "/home/jey/resumecours.gestionhospitaliare.site/env" ]; then
    echo "💾 Sauvegarde de l'environnement virtuel..."
    cp -r /home/jey/resumecours.gestionhospitaliare.site/env /home/jey/resumecours.gestionhospitaliare.site/env_backup
fi

# Installer Python depuis les sources avec SQLite3
cd /tmp
wget https://www.python.org/ftp/python/3.7.16/Python-3.7.16.tgz
tar xzf Python-3.7.16.tgz
cd Python-3.7.16

# Configurer avec SQLite3
./configure --enable-optimizations --with-sqlite3
make altinstall

# Créer un nouveau lien symbolique
ln -sf /usr/local/bin/python3.7 /usr/local/bin/python3

echo "✅ Installation terminée"
echo "🔄 Veuillez recréer votre environnement virtuel:"
echo "   cd /home/jey/resumecours.gestionhospitaliare.site"
echo "   rm -rf env"
echo "   python3 -m venv env"
echo "   source env/bin/activate"
echo "   pip install -r requirements.txt"