#!/bin/bash

echo "🔄 Redémarrage du serveur de production"
echo "======================================"

# Vérifier si nous sommes root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Ce script doit être exécuté en tant que root"
    echo "Utilisez: sudo bash restart_server.sh"
    exit 1
fi

# Arrêter les services
echo "🛑 Arrêt des services..."
systemctl stop httpd
systemctl stop gunicorn

# Vérifier les processus Django/Gunicorn restants
echo "🔍 Vérification des processus restants..."
pkill -f gunicorn
pkill -f python.*manage.py

# Attendre un peu
sleep 2

# Redémarrer les services
echo "🚀 Redémarrage des services..."
systemctl start gunicorn
systemctl start httpd

# Vérifier le statut
echo "📊 Statut des services:"
systemctl status gunicorn --no-pager -l
systemctl status httpd --no-pager -l

# Vérifier les logs récents
echo "📝 Logs récents:"
echo "--- Gunicorn ---"
journalctl -u gunicorn --no-pager -n 5

echo "--- Apache ---"
journalctl -u httpd --no-pager -n 5

echo "✅ Redémarrage terminé"
echo "🌐 Votre site devrait être accessible sur: https://resumecours.gestionhospitaliare.site"