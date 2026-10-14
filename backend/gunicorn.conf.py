# Configuration Gunicorn pour la production

import multiprocessing

# Serveur
bind = "127.0.0.1:8000"
backlog = 2048

# Workers
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000

# TIMEOUT PORTÉ DE 30 s À 300 s — CAUSE DE « l'envoi a été interrompu : plus
# aucune donnée transmise ».
#
# Avec un worker `sync`, gunicorn surveille la durée de traitement d'une requête
# et TUE le worker au-delà de ce délai. 30 s suffisent pour les requêtes courtes
# (OTP, profil), pas pour l'envoi d'un fichier audio : le worker meurt en pleine
# réception du corps, l'Apache qui l'expose cesse de lire la requête, et le
# téléphone n'a plus qu'à écrire dans un tuyau que personne ne vide. Son
# garde-fou anti-blocage (60 s sans un octet transmis) annule alors l'envoi et
# affiche « l'envoi a été interrompu : plus aucune donnée transmise » — message
# exact, mais qui accuse la connexion du téléphone alors que la panne est ici.
#
# 300 s couvre l'envoi d'un fichier volumineux sur un réseau mobile lent. Le
# côté application attend la réponse jusqu'à 10 minutes (uploadAudio).
#
# POUR CONFIRMER SUR LE SERVEUR, avant même de redéployer :
#     grep -i "WORKER TIMEOUT" /var/log/resume_plus/gunicorn_error.log
#     journalctl -u resume_plus -n 100 | grep -i timeout
# Une ligne « [CRITICAL] WORKER TIMEOUT (pid:…) » datée de l'heure de l'échec
# d'envoi confirme le diagnostic.
timeout = 300

keepalive = 2
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "/var/log/resume_plus/gunicorn_access.log"
errorlog = "/var/log/resume_plus/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "resume_plus_gunicorn"

# Server mechanics
daemon = False
pidfile = "/var/run/gunicorn/resume_plus.pid"
user = "www-data"
group = "www-data"
tmp_upload_dir = None

# SSL (si vous utilisez HTTPS directement avec Gunicorn)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"