#!/bin/bash

echo "📦 Installation des dépendances manquantes"
echo "=========================================="

# Activer l'environnement virtuel
source ../env/bin/activate

# Installer les packages manquants
echo "🔧 Installation de requests..."
pip install requests

echo "🔧 Installation de python-decouple..."
pip install python-decouple

echo "🔧 Installation de PyMySQL..."
pip install PyMySQL

echo "✅ Installation terminée"
echo ""
echo "📋 Packages installés:"
pip list | grep -E "(requests|decouple|PyMySQL)"