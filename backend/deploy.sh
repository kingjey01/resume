#!/bin/bash

# Script de déploiement pour Resume Plus Backend

echo "🚀 Début du déploiement..."

# 1. Arrêter les services
echo "📦 Arrêt des services..."
sudo systemctl stop gunicorn
sudo systemctl stop nginx

# 2. Sauvegarder la base de données
echo "💾 Sauvegarde de la base de données..."
python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission --indent 2 > backup_$(date +%Y%m%d_%H%M%S).json

# 3. Mettre à jour le code
echo "📥 Mise à jour du code..."
git pull origin main

# 4. Installer les dépendances
echo "📦 Installation des dépendances..."
pip install -r requirements.txt

# 5. Collecter les fichiers statiques
echo "📁 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput --settings=resume_backend.production_settings

# 6. Appliquer les migrations
echo "🗄️ Application des migrations..."
python manage.py migrate --settings=resume_backend.production_settings

# 7. Créer un superutilisateur si nécessaire (optionnel)
# python manage.py createsuperuser --settings=resume_backend.production_settings

# 8. Redémarrer les services
echo "🔄 Redémarrage des services..."
sudo systemctl start gunicorn
sudo systemctl start nginx

# 9. Vérifier le statut
echo "✅ Vérification du statut..."
sudo systemctl status gunicorn --no-pager
sudo systemctl status nginx --no-pager

echo "🎉 Déploiement terminé !"

# 10. Test de l'API
echo "🧪 Test de l'API..."
curl -f https://resumecours.gestionhospitaliare.site/api/health/ || echo "❌ L'API ne répond pas"

echo "📋 Logs récents de Gunicorn:"
sudo journalctl -u gunicorn --no-pager -n 10