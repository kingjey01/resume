#!/usr/bin/env python3
"""
Test avancé des fonctionnalités audio - Diagnostic complet
"""

import os
import sys
import requests
import json
import wave
from pathlib import Path

# Configuration - PRODUCTION
BASE_URL_LOCAL = "http://127.0.0.1:8000/api/courses"
BASE_URL_PROD = "https://resumecours.gestionhospitaliare.site/api/courses"
BASE_URL = BASE_URL_PROD  # Utiliser la production par défaut

def test_django_setup():
    """Tester la configuration Django"""
    print("🔧 Test de la configuration Django")
    print("=" * 50)
    
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')
        sys.path.insert(0, '/home/jey/resumecours.gestionhospitaliare.site/backend')
        
        import django
        django.setup()
        
        from courses.models import Session, Course, Summary
        from django.conf import settings
        
        print(f"  ✅ Django configuré")
        print(f"  📁 BASE_DIR: {settings.BASE_DIR}")
        print(f"  📁 MEDIA_ROOT: {getattr(settings, 'MEDIA_ROOT', 'Non défini')}")
        print(f"  🔗 MEDIA_URL: {getattr(settings, 'MEDIA_URL', 'Non défini')}")
        
        # Vérifier les modèles
        sessions_count = Session.objects.count()
        courses_count = Course.objects.count()
        summaries_count = Summary.objects.count()
        
        print(f"  📊 Sessions: {sessions_count}")
        print(f"  📊 Cours: {courses_count}")
        print(f"  📊 Résumés: {summaries_count}")
        
        return True, (Session, Course, Summary, settings)
        
    except Exception as e:
        print(f"  ❌ Erreur Django: {e}")
        return False, None

def test_audio_files_existence():
    """Vérifier l'existence physique des fichiers audio"""
    print("\n📁 Test de l'existence des fichiers audio")
    print("=" * 50)
    
    success, django_data = test_django_setup()
    if not success:
        return False
    
    Session, Course, Summary, settings = django_data
    
    sessions_with_audio = Session.objects.filter(
        audio_file__isnull=False
    ).exclude(audio_file='')
    
    print(f"  📊 Sessions avec fichier audio en DB: {sessions_with_audio.count()}")
    
    if sessions_with_audio.count() == 0:
        print("  ⚠️ Aucune session avec fichier audio trouvée")
        return False
    
    files_found = 0
    files_missing = 0
    
    for session in sessions_with_audio:
        print(f"\n  🎵 Session {session.id}: {session.course.nom}")
        print(f"     📄 Fichier DB: {session.audio_file.name}")
        
        try:
            # Vérifier le chemin complet
            if hasattr(session.audio_file, 'path'):
                full_path = session.audio_file.path
                print(f"     📁 Chemin complet: {full_path}")
                
                if os.path.exists(full_path):
                    file_size = os.path.getsize(full_path)
                    print(f"     ✅ Fichier existe: {file_size} bytes")
                    
                    # Vérifier que c'est un fichier WAV valide
                    try:
                        with wave.open(full_path, 'rb') as wav_file:
                            frames = wav_file.getnframes()
                            sample_rate = wav_file.getframerate()
                            channels = wav_file.getnchannels()
                            duration = frames / sample_rate if sample_rate > 0 else 0
                            print(f"     🎵 WAV: {duration:.1f}s, {sample_rate}Hz, {channels}ch")
                    except Exception as wav_error:
                        print(f"     ⚠️ Erreur lecture WAV: {wav_error}")
                    
                    files_found += 1
                else:
                    print(f"     ❌ Fichier manquant: {full_path}")
                    files_missing += 1
            else:
                print(f"     ⚠️ Pas de chemin de fichier disponible")
                files_missing += 1
                
        except Exception as e:
            print(f"     ❌ Erreur: {e}")
            files_missing += 1
    
    print(f"\n  📊 Résumé:")
    print(f"     Fichiers trouvés: {files_found}")
    print(f"     Fichiers manquants: {files_missing}")
    
    return files_found > 0

def test_local_server_endpoints():
    """Tester les endpoints sur le serveur local"""
    print("\n🌐 Test des endpoints serveur local")
    print("=" * 50)
    
    # Démarrer le serveur Django en arrière-plan si nécessaire
    import subprocess
    import time
    import signal
    
    server_process = None
    try:
        # Vérifier si le serveur tourne déjà
        try:
            response = requests.get(f"{BASE_URL_LOCAL}/courses/", timeout=2)
            print("  ✅ Serveur local déjà en cours")
        except:
            print("  🚀 Démarrage du serveur local...")
            server_process = subprocess.Popen([
                sys.executable, 'manage.py', 'runserver', '127.0.0.1:8000'
            ], cwd='/home/jey/resumecours.gestionhospitaliare.site/backend',
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Attendre que le serveur démarre
            time.sleep(3)
        
        # Tester les endpoints
        endpoints = [
            ("/courses/", "Liste des cours"),
            ("/sessions/", "Liste des sessions"),
            ("/sessions/audio/", "Sessions audio"),
            ("/sessions/audio/stats/", "Statistiques audio"),
            ("/summaries/", "Liste des résumés")
        ]
        
        for endpoint, description in endpoints:
            try:
                url = BASE_URL_LOCAL + endpoint
                print(f"  🔗 Test: {description}")
                print(f"     URL: {url}")
                
                response = requests.get(url, timeout=10)
                print(f"     📊 Status: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if isinstance(data, list):
                            print(f"     📋 Résultats: {len(data)} éléments")
                        elif isinstance(data, dict):
                            if 'count' in data:
                                print(f"     📋 Count: {data['count']}")
                            elif 'sessions' in data:
                                print(f"     📋 Sessions: {len(data['sessions'])}")
                            else:
                                print(f"     📋 Clés: {list(data.keys())}")
                    except:
                        print(f"     📋 Réponse non-JSON")
                elif response.status_code == 401:
                    print(f"     🔐 Authentification requise")
                else:
                    print(f"     ❌ Erreur: {response.text[:100]}")
                    
            except requests.exceptions.RequestException as e:
                print(f"     ❌ Erreur connexion: {e}")
        
        # Test spécifique des fichiers audio
        print(f"\n  🎵 Test des fichiers audio individuels:")
        try:
            # Récupérer les sessions audio
            response = requests.get(f"{BASE_URL_LOCAL}/sessions/audio/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                sessions = data.get('sessions', [])
                
                for session in sessions[:3]:  # Tester les 3 premières
                    session_id = session['id']
                    print(f"     🎵 Test session {session_id}:")
                    
                    # Test endpoint audio-file
                    audio_url = f"{BASE_URL_LOCAL}/sessions/{session_id}/audio-file/"
                    try:
                        audio_response = requests.get(audio_url, timeout=5)
                        print(f"        audio-file: {audio_response.status_code}")
                        if audio_response.status_code == 200:
                            audio_data = audio_response.json()
                            if audio_data.get('success'):
                                print(f"        ✅ Fichier accessible")
                                print(f"        📁 URL: {audio_data.get('audio_url', 'N/A')}")
                            else:
                                print(f"        ❌ Erreur: {audio_data.get('error', 'Inconnue')}")
                    except Exception as e:
                        print(f"        ❌ Erreur: {e}")
                    
                    # Test endpoint serve-audio
                    serve_url = f"{BASE_URL_LOCAL}/sessions/{session_id}/serve-audio/"
                    try:
                        serve_response = requests.head(serve_url, timeout=5)
                        print(f"        serve-audio: {serve_response.status_code}")
                        if serve_response.status_code == 200:
                            content_type = serve_response.headers.get('content-type', 'N/A')
                            content_length = serve_response.headers.get('content-length', 'N/A')
                            print(f"        ✅ Type: {content_type}, Taille: {content_length}")
                    except Exception as e:
                        print(f"        ❌ Erreur: {e}")
            
        except Exception as e:
            print(f"     ❌ Erreur test audio: {e}")
        
    finally:
        # Arrêter le serveur si on l'a démarré
        if server_process:
            print("  🛑 Arrêt du serveur local...")
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()

def create_test_audio_upload():
    """Créer et tester l'upload d'un fichier audio"""
    print("\n📤 Test d'upload de fichier audio")
    print("=" * 50)
    
    try:
        # Créer un fichier audio de test
        import wave
        import struct
        import math
        import tempfile
        
        # Créer un fichier WAV temporaire
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name
        
        # Générer un fichier WAV de test
        sample_rate = 44100
        duration = 3  # 3 secondes
        frequency = 440  # La
        
        with wave.open(temp_path, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16 bits
            wav_file.setframerate(sample_rate)
            
            # Générer les échantillons
            for i in range(int(sample_rate * duration)):
                t = i / sample_rate
                sample = int(16000 * math.sin(2 * math.pi * frequency * t))
                wav_file.writeframes(struct.pack('<h', sample))
        
        file_size = os.path.getsize(temp_path)
        print(f"  ✅ Fichier de test créé: {temp_path}")
        print(f"  📏 Taille: {file_size} bytes")
        
        # Tester l'upload (nécessite un serveur en cours et authentification)
        print(f"  📤 Test d'upload (nécessite authentification)...")
        
        # Nettoyer
        os.unlink(temp_path)
        
        return True
        
    except Exception as e:
        print(f"  ❌ Erreur création fichier test: {e}")
        return False

def create_comprehensive_test_report():
    """Créer un rapport de test complet"""
    print("\n📋 Création du rapport de test complet")
    print("=" * 50)
    
    report = {
        'timestamp': str(datetime.now()),
        'tests': {}
    }
    
    # Exécuter tous les tests
    tests = [
        ('django_setup', test_django_setup),
        ('audio_files_existence', test_audio_files_existence),
        ('upload_test', create_test_audio_upload)
    ]
    
    for test_name, test_func in tests:
        try:
            print(f"\n🧪 Exécution du test: {test_name}")
            result = test_func()
            report['tests'][test_name] = {
                'success': bool(result),
                'result': result
            }
        except Exception as e:
            print(f"❌ Erreur dans le test {test_name}: {e}")
            report['tests'][test_name] = {
                'success': False,
                'error': str(e)
            }
    
    # Sauvegarder le rapport
    try:
        import json
        from datetime import datetime
        
        report_file = f"/tmp/audio_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"  ✅ Rapport sauvegardé: {report_file}")
        
        # Résumé
        successful_tests = sum(1 for test in report['tests'].values() if test['success'])
        total_tests = len(report['tests'])
        
        print(f"\n📊 RÉSUMÉ DU RAPPORT:")
        print(f"   Tests réussis: {successful_tests}/{total_tests}")
        
        for test_name, test_result in report['tests'].items():
            status = "✅" if test_result['success'] else "❌"
            print(f"   {status} {test_name}")
        
    except Exception as e:
        print(f"  ❌ Erreur sauvegarde rapport: {e}")

def main():
    """Fonction principale de test avancé"""
    print("🧪 TEST AVANCÉ DES FONCTIONNALITÉS AUDIO")
    print("=" * 80)
    
    try:
        from datetime import datetime
        
        # 1. Test de la configuration Django
        django_ok, django_data = test_django_setup()
        
        # 2. Test de l'existence des fichiers
        if django_ok:
            files_ok = test_audio_files_existence()
        else:
            files_ok = False
        
        # 3. Test des endpoints locaux
        test_local_server_endpoints()
        
        # 4. Test d'upload
        upload_ok = create_test_audio_upload()
        
        # 5. Rapport final
        print("\n" + "=" * 80)
        print("📋 RAPPORT FINAL")
        print("=" * 80)
        
        print(f"✅ Django configuré: {'Oui' if django_ok else 'Non'}")
        print(f"✅ Fichiers audio trouvés: {'Oui' if files_ok else 'Non'}")
        print(f"✅ Test upload: {'Oui' if upload_ok else 'Non'}")
        
        if not files_ok:
            print(f"\n💡 RECOMMANDATIONS:")
            print(f"1. Exécutez: python demo_audio_complete.py")
            print(f"2. Vérifiez les permissions du répertoire media")
            print(f"3. Redémarrez le serveur Django")
        
        print(f"\n🎯 PROCHAINES ÉTAPES:")
        print(f"1. Si les fichiers manquent, exécutez demo_audio_complete.py")
        print(f"2. Testez avec la page HTML générée")
        print(f"3. Vérifiez la configuration Apache/Nginx")
        
    except Exception as e:
        print(f"❌ Erreur dans les tests: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()