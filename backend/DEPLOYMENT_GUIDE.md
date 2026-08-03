# 🚀 Guide de Déploiement et Fonctionnalités Audio - Resume+

## 1. 🔄 Redémarrage du serveur httpd

### Commandes de redémarrage
```bash
# Méthode 1: Script automatique
sudo bash restart_server.sh

# Méthode 2: Commandes manuelles
sudo systemctl stop httpd
sudo systemctl stop gunicorn
sudo pkill -f gunicorn
sudo systemctl start gunicorn
sudo systemctl start httpd

# Vérifier le statut
sudo systemctl status httpd
sudo systemctl status gunicorn
```

### Vérification des logs
```bash
# Logs Apache
sudo tail -f /var/log/httpd/error_log
sudo tail -f /var/log/httpd/access_log

# Logs Gunicorn
sudo journalctl -u gunicorn -f

# Logs Django
tail -f /home/jey/resumecours.gestionhospitaliare.site/backend/django.log
```

## 2. 🎵 Fonctionnalités Audio Implémentées

### Endpoints API disponibles

#### 📤 Upload d'enregistrement audio
```bash
POST /api/courses/sessions/upload-audio/
Content-Type: multipart/form-data

Paramètres:
- audio_file: Fichier audio (mp3, wav, m4a, ogg, webm)
- course_id: ID du cours
- title: Titre de l'enregistrement (optionnel)
- auto_process: true/false (génération automatique de résumé)
```

#### 📋 Récupération des sessions audio
```bash
GET /api/courses/sessions/audio/
```

#### 🎵 Récupération d'un fichier audio
```bash
GET /api/courses/sessions/{session_id}/audio-file/
```

#### 🤖 Traitement automatique d'une session
```bash
POST /api/courses/sessions/{session_id}/process-audio/
```

#### 📊 Statistiques de traitement
```bash
GET /api/courses/sessions/audio/stats/
```

### Exemple d'utilisation avec curl
```bash
# Upload d'un fichier audio
curl -X POST \
  -H "Authorization: Token YOUR_TOKEN" \
  -F "audio_file=@recording.mp3" \
  -F "course_id=1" \
  -F "auto_process=true" \
  https://resumecours.gestionhospitaliare.site/api/courses/sessions/upload-audio/

# Récupérer les sessions audio
curl -H "Authorization: Token YOUR_TOKEN" \
  https://resumecours.gestionhospitaliare.site/api/courses/sessions/audio/
```

## 3. 🔧 Configuration des fichiers statiques et media

### Configuration Apache pour les fichiers media
Ajoutez dans votre configuration Apache (`/etc/httpd/conf.d/resume.conf`):

```apache
# Servir les fichiers media
Alias /media/ /home/jey/resumecours.gestionhospitaliare.site/backend/media/
<Directory "/home/jey/resumecours.gestionhospitaliare.site/backend/media/">
    Require all granted
    # Permettre la lecture des fichiers audio
    <FilesMatch "\.(mp3|wav|m4a|ogg|webm)$">
        Header set Access-Control-Allow-Origin "*"
        Header set Access-Control-Allow-Methods "GET, OPTIONS"
    </FilesMatch>
</Directory>

# Servir les fichiers statiques
Alias /static/ /home/jey/resumecours.gestionhospitaliare.site/backend/staticfiles/
<Directory "/home/jey/resumecours.gestionhospitaliare.site/backend/staticfiles/">
    Require all granted
</Directory>
```

### Permissions des répertoires
```bash
# Créer les répertoires nécessaires
sudo mkdir -p /home/jey/resumecours.gestionhospitaliare.site/backend/media/audio_sessions
sudo mkdir -p /home/jey/resumecours.gestionhospitaliare.site/backend/staticfiles

# Définir les permissions
sudo chown -R apache:apache /home/jey/resumecours.gestionhospitaliare.site/backend/media/
sudo chown -R apache:apache /home/jey/resumecours.gestionhospitaliare.site/backend/staticfiles/
sudo chmod -R 755 /home/jey/resumecours.gestionhospitaliare.site/backend/media/
sudo chmod -R 755 /home/jey/resumecours.gestionhospitaliare.site/backend/staticfiles/
```

## 4. 🗄️ Configuration Django pour les fichiers media

### Mise à jour de settings.py
```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Configuration des fichiers media
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Configuration des fichiers statiques
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Taille maximale des fichiers uploadés (100MB)
FILE_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024
```

## 5. 🎯 Tests et Vérifications

### Créer les données de test
```bash
cd /home/jey/resumecours.gestionhospitaliare.site/backend
source ../env/bin/activate
python create_test_data.py
```

### Tester les fonctionnalités audio
```bash
python test_audio_functionality.py
```

### Vérifier la base de données
```bash
python test_seed_creation.py
```

## 6. 🐛 Résolution des problèmes courants

### Problème: Sessions audio ne se lisent pas

#### Vérification 1: Fichiers audio existants
```bash
# Vérifier les fichiers dans la base
mysql -u jey_resume -p1234 jey_resume -e "
SELECT s.id, s.audio_file, c.nom 
FROM courses_session s 
JOIN courses_course c ON s.course_id = c.id 
WHERE s.audio_file IS NOT NULL AND s.audio_file != '';
"

# Vérifier les fichiers sur le disque
ls -la /home/jey/resumecours.gestionhospitaliare.site/backend/media/audio_sessions/
```

#### Vérification 2: URLs accessibles
```bash
# Tester l'accès direct au fichier
curl -I https://resumecours.gestionhospitaliare.site/media/audio_sessions/session_1_demo.wav

# Tester via l'API
curl -H "Authorization: Token YOUR_TOKEN" \
  https://resumecours.gestionhospitaliare.site/api/courses/sessions/1/audio-file/
```

#### Solution: Créer des fichiers audio de test
```bash
cd /home/jey/resumecours.gestionhospitaliare.site/backend
python -c "
import os
from courses.models import Session
from django.core.files.base import ContentFile

# Créer des fichiers audio factices
for session in Session.objects.filter(audio_file__isnull=True)[:3]:
    fake_audio = b'RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x08\x00\x00' + b'\x00' * 2048
    session.audio_file.save(f'session_{session.id}_demo.wav', ContentFile(fake_audio))
    print(f'Fichier créé pour session {session.id}')
"
```

### Problème: Erreurs de permissions
```bash
# Corriger les permissions
sudo chown -R apache:apache /home/jey/resumecours.gestionhospitaliare.site/
sudo chmod -R 755 /home/jey/resumecours.gestionhospitaliare.site/backend/media/

# Vérifier SELinux (si activé)
sudo setsebool -P httpd_can_network_connect 1
sudo chcon -R -t httpd_exec_t /home/jey/resumecours.gestionhospitaliare.site/
```

### Problème: Gunicorn ne démarre pas
```bash
# Vérifier la configuration Gunicorn
sudo systemctl status gunicorn
sudo journalctl -u gunicorn --no-pager -l

# Redémarrer manuellement
cd /home/jey/resumecours.gestionhospitaliare.site
source env/bin/activate
cd backend
gunicorn --bind 127.0.0.1:8000 resume_backend.wsgi:application
```

## 7. 📱 Intégration Flutter

### Endpoints à utiliser dans Flutter
```dart
// Configuration de base
const String baseUrl = 'https://resumecours.gestionhospitaliare.site/api/courses';

// Récupérer les sessions audio
GET $baseUrl/sessions/audio/

// Récupérer un fichier audio spécifique
GET $baseUrl/sessions/{sessionId}/audio-file/

// Upload d'un enregistrement
POST $baseUrl/sessions/upload-audio/
```

### Exemple de lecture audio en Flutter
```dart
import 'package:audioplayers/audioplayers.dart';

class AudioPlayerService {
  final AudioPlayer _audioPlayer = AudioPlayer();
  
  Future<void> playAudioFromUrl(String audioUrl) async {
    try {
      await _audioPlayer.play(UrlSource(audioUrl));
    } catch (e) {
      print('Erreur lecture audio: $e');
    }
  }
  
  Future<void> stopAudio() async {
    await _audioPlayer.stop();
  }
}
```

## 8. 🔍 Monitoring et Logs

### Surveiller les logs en temps réel
```bash
# Terminal 1: Logs Apache
sudo tail -f /var/log/httpd/error_log

# Terminal 2: Logs Gunicorn
sudo journalctl -u gunicorn -f

# Terminal 3: Logs Django
tail -f /home/jey/resumecours.gestionhospitaliare.site/backend/django.log
```

### Commandes de diagnostic
```bash
# Vérifier l'espace disque
df -h

# Vérifier les processus
ps aux | grep -E "(httpd|gunicorn|python)"

# Vérifier les ports
netstat -tlnp | grep -E "(80|443|8000)"

# Tester la connectivité
curl -I https://resumecours.gestionhospitaliare.site/
```

## 9. ✅ Checklist de vérification

- [ ] Serveur httpd redémarré
- [ ] Gunicorn fonctionne
- [ ] Base de données accessible
- [ ] Données de test créées
- [ ] Répertoires media créés avec bonnes permissions
- [ ] Configuration Apache mise à jour
- [ ] Endpoints audio accessibles
- [ ] Fichiers audio de test créés
- [ ] Tests API passent
- [ ] Logs sans erreurs critiques

## 10. 🆘 Support et Dépannage

### Commandes de dépannage rapide
```bash
# Tout redémarrer
sudo bash restart_server.sh

# Recréer les données de test
python create_test_data.py

# Tester les fonctionnalités
python test_audio_functionality.py

# Vérifier la configuration
python manage.py check
python manage.py collectstatic --noinput
```

### Contacts et ressources
- Logs: `/var/log/httpd/` et `journalctl -u gunicorn`
- Configuration: `/etc/httpd/conf.d/`
- Application: `/home/jey/resumecours.gestionhospitaliare.site/`
- Documentation Django: https://docs.djangoproject.com/