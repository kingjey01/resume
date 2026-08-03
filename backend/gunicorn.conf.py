# Configuration Gunicorn pour la production

import multiprocessing

# Serveur
bind = "127.0.0.1:8000"
backlog = 2048

# Workers
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
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