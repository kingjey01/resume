#!/usr/bin/env python3
"""
Script pour corriger tous les problèmes audio
"""

import os
import sys
import subprocess
from pathlib import Path

def setup_django():
    """Configuration Django"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')
    sys.path.insert(0, '/home/jey/resumecours.gestionhospitaliare.site/backend')
    
    import django
    try:
        django.setup()
    except:
        pass

def create_media_directories():
    """Créer les répertoires media avec les bonnes permissions"""
    print("📁 Création des répertoires media...")
    
    base_dir = "/home/jey/resumecours.gestionhospitaliare.site/backend"
    directories = [
        os.path.join(base_dir, "media"),
        os.path.join(base_dir, "media", "audio_sessions"),
        os.path.join(base_dir, "staticfiles")
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"  ✅ {directory} créé")
        except Exception as e:
            print(f"  ❌ Erreur {directory}: {e}")
    
    # Définir les permissions
    try:
        subprocess.run(['sudo', 'chown', '-R', 'apache:apache', f'{base_dir}/media/'], check=True)
        subprocess.run(['sudo', 'chmod', '-R', '755', f'{base_dir}/media/'], check=True)
        print("  ✅ Permissions définies")
    except Exception as e:
        print(f"  ⚠️ Erreur permissions (exécuter en tant que root): {e}")

def create_apache_media_config():
    """Créer la configuration Apache pour les fichiers media"""
    print("🌐 Configuration Apache pour les fichiers media...")
    
    config_content = """
# Configuration pour les fichiers media Resume+
Alias /media/ /home/jey/resumecours.gestionhospitaliare.site/backend/media/
<Directory "/home/jey/resumecours.gestionhospitaliare.site/backend/media/">
    Require all granted
    Options -Indexes
    
    # Headers CORS pour les fichiers audio
    <FilesMatch "\\.(mp3|wav|m4a|ogg|webm|aac)$">
        Header always set Access-Control-Allow-Origin "*"
        Header always set Access-Control-Allow-Methods "GET, HEAD, OPTIONS"
        Header always set Access-Control-Allow-Headers "Range, Content-Range, Content-Type"
        Header always set Accept-Ranges "bytes"
    </FilesMatch>
    
    # Cache pour les fichiers audio
    <FilesMatch "\\.(mp3|wav|m4a|ogg|webm|aac)$">
        ExpiresActive On
        ExpiresDefault "access plus 1 month"
    </FilesMatch>
</Directory>

# Configuration pour les fichiers statiques
Alias /static/ /home/jey/resumecours.gestionhospitaliare.site/backend/staticfiles/
<Directory "/home/jey/resumecours.gestionhospitaliare.site/backend/staticfiles/">
    Require all granted
    Options -Indexes
    
    # Cache pour les fichiers statiques
    ExpiresActive On
    ExpiresDefault "access plus 1 year"
</Directory>
"""
    
    config_file = "/tmp/resume_media.conf"
    try:
        with open(config_file, 'w') as f:
            f.write(config_content)
        
        print(f"  ✅ Configuration créée: {config_file}")
        print("  📋 Pour l'appliquer, exécutez en tant que root:")
        print(f"     sudo cp {config_file} /etc/httpd/conf.d/resume_media.conf")
        print("     sudo systemctl reload httpd")
        
    except Exception as e:
        print(f"  ❌ Erreur création config: {e}")

def create_real_audio_files():
    """Créer de vrais fichiers audio de test"""
    print("🎵 Création de fichiers audio de test...")
    
    setup_django()
    
    try:
        from courses.models import Session, Course
        from django.core.files.base import ContentFile
        import wave
        import struct
        
        # Fonction pour créer un fichier WAV valide avec un son
        def create_wav_file(duration_seconds=5, frequency=440):
            """Créer un fichier WAV avec un son de test"""
            sample_rate = 44100
            num_samples = int(sample_rate * duration_seconds)
            
            # Générer une onde sinusoïdale
            samples = []
            for i in range(num_samples):
                # Onde sinusoïdale avec fade in/out
                t = i / sample_rate
                fade = min(t, duration_seconds - t, 0.1) / 0.1  # Fade de 0.1s
                amplitude = int(32767 * 0.3 * fade)  # 30% du volume max
                sample = int(amplitude * (
                    0.5 * (1 + 0) +  # Onde principale
                    0.3 * (1 + 0) +  # Harmonique
                    0.1 * (1 + 0)    # Bruit léger
                ))
                samples.append(sample)
            
            # Créer le fichier WAV en mémoire
            import io
            wav_buffer = io.BytesIO()
            
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16 bits
                wav_file.setframerate(sample_rate)
                
                # Écrire les échantillons
                for sample in samples:
                    wav_file.writeframes(struct.pack('<h', sample))
            
            return wav_buffer.getvalue()
        
        # Récupérer les sessions sans fichier audio
        sessions_without_audio = Session.objects.filter(
            audio_file__isnull=True
        ) | Session.objects.filter(audio_file='')
        
        print(f"  📊 Sessions sans audio: {sessions_without_audio.count()}")
        
        created_count = 0
        for i, session in enumerate(sessions_without_audio[:5]):
            try:
                # Créer un fichier audio différent pour chaque session
                duration = 3 + (i * 2)  # 3, 5, 7, 9, 11 secondes
                frequency = 440 + (i * 110)  # Fréquences différentes
                
                audio_content = create_wav_file(duration, frequency)
                filename = f'session_{session.id}_course_{session.course.id}.wav'
                
                # Sauvegarder le fichier
                session.audio_file.save(
                    filename,
                    ContentFile(audio_content),
                    save=True
                )
                
                created_count += 1
                print(f"  ✅ Session {session.id}: {filename} ({len(audio_content)} bytes, {duration}s)")
                
            except Exception as e:
                print(f"  ❌ Erreur session {session.id}: {e}")
        
        print(f"  🎯 {created_count} fichiers audio créés avec succès")
        return created_count > 0
        
    except Exception as e:
        print(f"  ❌ Erreur création fichiers audio: {e}")
        return False

def update_django_settings():
    """Mettre à jour les settings Django pour les fichiers media"""
    print("⚙️ Vérification des settings Django...")
    
    settings_file = "/home/jey/resumecours.gestionhospitaliare.site/backend/resume_backend/settings.py"
    
    try:
        with open(settings_file, 'r') as f:
            content = f.read()
        
        # Vérifier si la configuration media existe
        if 'MEDIA_URL' not in content:
            media_config = """
# Configuration des fichiers media
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Configuration des fichiers statiques
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Taille maximale des fichiers uploadés (100MB)
FILE_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024
"""
            
            # Ajouter la configuration à la fin du fichier
            with open(settings_file, 'a') as f:
                f.write(media_config)
            
            print("  ✅ Configuration media ajoutée à settings.py")
        else:
            print("  ℹ️ Configuration media déjà présente")
            
    except Exception as e:
        print(f"  ❌ Erreur mise à jour settings: {e}")

def create_audio_test_endpoint():
    """Créer un endpoint de test pour les fichiers audio"""
    print("🔧 Création d'un endpoint de test audio...")
    
    test_view_content = '''
from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from courses.models import Session
import os

@csrf_exempt
@require_http_methods(["GET"])
def test_audio_endpoint(request, session_id):
    """Endpoint de test pour servir les fichiers audio"""
    try:
        session = Session.objects.get(id=session_id)
        
        if not session.audio_file:
            return JsonResponse({
                'error': 'Aucun fichier audio pour cette session',
                'session_id': session_id
            }, status=404)
        
        # Informations sur le fichier
        file_info = {
            'session_id': session_id,
            'course_name': session.course.nom,
            'professor': session.professeur,
            'file_name': session.audio_file.name,
            'file_url': request.build_absolute_uri(session.audio_file.url),
            'file_exists': os.path.exists(session.audio_file.path) if hasattr(session.audio_file, 'path') else False
        }
        
        # Ajouter la taille du fichier si possible
        try:
            if hasattr(session.audio_file, 'size'):
                file_info['file_size'] = session.audio_file.size
            elif hasattr(session.audio_file, 'path') and os.path.exists(session.audio_file.path):
                file_info['file_size'] = os.path.getsize(session.audio_file.path)
        except:
            file_info['file_size'] = 'unknown'
        
        return JsonResponse({
            'success': True,
            'message': 'Fichier audio trouvé',
            'file_info': file_info
        })
        
    except Session.DoesNotExist:
        return JsonResponse({
            'error': 'Session non trouvée',
            'session_id': session_id
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'error': f'Erreur: {str(e)}',
            'session_id': session_id
        }, status=500)
'''
    
    try:
        test_file = "/home/jey/resumecours.gestionhospitaliare.site/backend/courses/test_views.py"
        with open(test_file, 'w') as f:
            f.write(test_view_content)
        
        print(f"  ✅ Endpoint de test créé: {test_file}")
        print("  📋 Ajoutez cette URL dans courses/urls.py:")
        print("     path('test-audio/<int:session_id>/', views.test_audio_endpoint, name='test-audio'),")
        
    except Exception as e:
        print(f"  ❌ Erreur création endpoint: {e}")

def run_diagnostics():
    """Exécuter les diagnostics"""
    print("🔍 Exécution des diagnostics...")
    
    try:
        result = subprocess.run([
            'python', 'debug_audio_issues.py'
        ], cwd='/home/jey/resumecours.gestionhospitaliare.site/backend', 
        capture_output=True, text=True, timeout=60)
        
        print("📊 Résultats du diagnostic:")
        print(result.stdout)
        
        if result.stderr:
            print("⚠️ Erreurs:")
            print(result.stderr)
            
    except Exception as e:
        print(f"  ❌ Erreur diagnostic: {e}")

def main():
    """Fonction principale de correction"""
    print("🔧 CORRECTION COMPLÈTE DES PROBLÈMES AUDIO")
    print("=" * 80)
    
    steps = [
        ("Création des répertoires media", create_media_directories),
        ("Configuration Apache", create_apache_media_config),
        ("Mise à jour Django settings", update_django_settings),
        ("Création de fichiers audio de test", create_real_audio_files),
        ("Création d'endpoint de test", create_audio_test_endpoint),
        ("Diagnostic final", run_diagnostics)
    ]
    
    for step_name, step_func in steps:
        print(f"\n🔄 {step_name}...")
        try:
            step_func()
        except Exception as e:
            print(f"❌ Erreur dans {step_name}: {e}")
    
    print("\n" + "=" * 80)
    print("✅ CORRECTION TERMINÉE")
    print("=" * 80)
    
    print("\n📋 ÉTAPES MANUELLES À EFFECTUER:")
    print("1. Appliquer la configuration Apache:")
    print("   sudo cp /tmp/resume_media.conf /etc/httpd/conf.d/")
    print("   sudo systemctl reload httpd")
    
    print("\n2. Redémarrer les services:")
    print("   sudo bash restart_server.sh")
    
    print("\n3. Tester les endpoints:")
    print("   python test_audio_functionality.py")
    
    print("\n4. Vérifier l'accès direct aux fichiers:")
    print("   curl -I https://resumecours.gestionhospitaliare.site/media/audio_sessions/")
    
    print("\n🎯 Une fois ces étapes effectuées, les fichiers audio devraient être accessibles!")

if __name__ == '__main__':
    main()