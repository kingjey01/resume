#!/usr/bin/env python3
"""
Script de diagnostic pour les problèmes audio
"""

import os
import sys
import pymysql
from pathlib import Path
import requests

def check_database_audio_files():
    """Vérifier les fichiers audio en base de données"""
    print("🔍 Vérification des fichiers audio en base de données")
    print("=" * 60)
    
    try:
        connection = pymysql.connect(
            host='localhost',
            user='jey_resume',
            password='1234',
            database='jey_resume',
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        # Vérifier toutes les sessions
        cursor.execute("""
            SELECT s.id, s.audio_file, s.professeur, c.nom as course_name, s.created_at
            FROM courses_session s
            JOIN courses_course c ON s.course_id = c.id
            ORDER BY s.created_at DESC
        """)
        
        sessions = cursor.fetchall()
        print(f"📊 Total des sessions: {len(sessions)}")
        
        sessions_with_audio = 0
        sessions_without_audio = 0
        
        for session in sessions:
            session_id, audio_file, professor, course_name, created_at = session
            if audio_file and audio_file.strip():
                sessions_with_audio += 1
                print(f"  ✅ Session {session_id}: {course_name} - {professor}")
                print(f"     📁 Fichier: {audio_file}")
            else:
                sessions_without_audio += 1
                print(f"  ❌ Session {session_id}: {course_name} - PAS DE FICHIER AUDIO")
        
        print(f"\n📈 Résumé:")
        print(f"  Sessions avec audio: {sessions_with_audio}")
        print(f"  Sessions sans audio: {sessions_without_audio}")
        
        connection.close()
        return sessions_with_audio > 0
        
    except Exception as e:
        print(f"❌ Erreur base de données: {e}")
        return False

def check_media_directory():
    """Vérifier le répertoire media sur le disque"""
    print("\n🗂️ Vérification du répertoire media")
    print("=" * 60)
    
    base_dir = "/home/jey/resumecours.gestionhospitaliare.site/backend"
    media_dir = os.path.join(base_dir, "media")
    audio_dir = os.path.join(media_dir, "audio_sessions")
    
    print(f"📁 Répertoire base: {base_dir}")
    print(f"📁 Répertoire media: {media_dir}")
    print(f"📁 Répertoire audio: {audio_dir}")
    
    # Vérifier l'existence des répertoires
    if os.path.exists(media_dir):
        print(f"  ✅ {media_dir} existe")
        
        if os.path.exists(audio_dir):
            print(f"  ✅ {audio_dir} existe")
            
            # Lister les fichiers audio
            try:
                audio_files = os.listdir(audio_dir)
                print(f"  📊 Fichiers audio trouvés: {len(audio_files)}")
                
                for i, file in enumerate(audio_files[:10]):  # Limiter à 10 fichiers
                    file_path = os.path.join(audio_dir, file)
                    file_size = os.path.getsize(file_path)
                    print(f"    {i+1}. {file} ({file_size} bytes)")
                
                if len(audio_files) > 10:
                    print(f"    ... et {len(audio_files) - 10} autres fichiers")
                    
                return len(audio_files) > 0
                
            except Exception as e:
                print(f"  ❌ Erreur lecture répertoire: {e}")
                return False
        else:
            print(f"  ❌ {audio_dir} n'existe pas")
            return False
    else:
        print(f"  ❌ {media_dir} n'existe pas")
        return False

def test_api_endpoints():
    """Tester les endpoints API audio"""
    print("\n🌐 Test des endpoints API audio")
    print("=" * 60)
    
    base_url = "https://resumecours.gestionhospitaliare.site/api/courses"
    # base_url = "http://localhost:8000/api/courses"  # Pour tests locaux
    
    endpoints = [
        "/sessions/",
        "/sessions/audio/",
        "/sessions/audio/stats/",
        "/courses/",
        "/summaries/"
    ]
    
    for endpoint in endpoints:
        try:
            url = base_url + endpoint
            print(f"🔗 Test: {url}")
            
            response = requests.get(url, timeout=10)
            print(f"  📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, list):
                        print(f"  📋 Résultats: {len(data)} éléments")
                    elif isinstance(data, dict):
                        if 'count' in data:
                            print(f"  📋 Résultats: {data['count']} éléments")
                        elif 'sessions' in data:
                            print(f"  📋 Sessions: {len(data['sessions'])} éléments")
                        else:
                            print(f"  📋 Données: {list(data.keys())}")
                except:
                    print(f"  📋 Réponse non-JSON")
            else:
                print(f"  ❌ Erreur: {response.text[:100]}")
                
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Erreur connexion: {e}")
        except Exception as e:
            print(f"  ❌ Erreur: {e}")

def create_test_audio_files():
    """Créer des fichiers audio de test"""
    print("\n🎵 Création de fichiers audio de test")
    print("=" * 60)
    
    try:
        # Configuration Django
        import django
        import os
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')
        
        # Ajouter le path
        sys.path.insert(0, '/home/jey/resumecours.gestionhospitaliare.site/backend')
        
        try:
            django.setup()
        except:
            print("⚠️ Django déjà configuré")
        
        from courses.models import Session, Course
        from django.core.files.base import ContentFile
        
        # Créer le répertoire s'il n'existe pas
        media_dir = "/home/jey/resumecours.gestionhospitaliare.site/backend/media/audio_sessions"
        os.makedirs(media_dir, exist_ok=True)
        print(f"📁 Répertoire créé: {media_dir}")
        
        # Récupérer les sessions sans fichier audio
        sessions_without_audio = Session.objects.filter(
            audio_file__isnull=True
        ) | Session.objects.filter(audio_file='')
        
        print(f"📊 Sessions sans audio: {sessions_without_audio.count()}")
        
        # Créer des fichiers audio factices
        created_count = 0
        for session in sessions_without_audio[:5]:  # Limiter à 5 pour le test
            try:
                # Créer un fichier WAV minimal mais valide
                wav_header = b'RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x08\x00\x00'
                silence_data = b'\x00' * 2048  # 2KB de silence
                fake_audio_content = wav_header + silence_data
                
                filename = f'session_{session.id}_test_audio.wav'
                
                # Sauvegarder le fichier
                session.audio_file.save(
                    filename,
                    ContentFile(fake_audio_content),
                    save=True
                )
                
                created_count += 1
                print(f"  ✅ Fichier créé pour session {session.id}: {filename}")
                
            except Exception as e:
                print(f"  ❌ Erreur session {session.id}: {e}")
        
        print(f"\n✅ {created_count} fichiers audio créés")
        return created_count > 0
        
    except Exception as e:
        print(f"❌ Erreur création fichiers: {e}")
        return False

def test_specific_audio_file():
    """Tester l'accès à un fichier audio spécifique"""
    print("\n🎵 Test d'accès à un fichier audio spécifique")
    print("=" * 60)
    
    try:
        # Configuration Django
        import django
        import os
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')
        sys.path.insert(0, '/home/jey/resumecours.gestionhospitaliare.site/backend')
        
        try:
            django.setup()
        except:
            pass
        
        from courses.models import Session
        
        # Récupérer une session avec fichier audio
        session_with_audio = Session.objects.filter(
            audio_file__isnull=False
        ).exclude(audio_file='').first()
        
        if session_with_audio:
            print(f"📁 Session trouvée: {session_with_audio.id}")
            print(f"📄 Fichier: {session_with_audio.audio_file.name}")
            
            # Tester l'URL du fichier
            try:
                file_url = session_with_audio.audio_file.url
                print(f"🔗 URL: {file_url}")
                
                # Tester l'accès direct
                full_url = f"https://resumecours.gestionhospitaliare.site{file_url}"
                print(f"🌐 URL complète: {full_url}")
                
                response = requests.head(full_url, timeout=10)
                print(f"📊 Status accès direct: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"✅ Fichier accessible directement")
                    if 'content-length' in response.headers:
                        size = int(response.headers['content-length'])
                        print(f"📏 Taille: {size} bytes")
                else:
                    print(f"❌ Fichier non accessible: {response.status_code}")
                
            except Exception as e:
                print(f"❌ Erreur test URL: {e}")
            
            # Tester via l'API
            try:
                api_url = f"https://resumecours.gestionhospitaliare.site/api/courses/sessions/{session_with_audio.id}/audio-file/"
                print(f"🔗 Test API: {api_url}")
                
                api_response = requests.get(api_url, timeout=10)
                print(f"📊 Status API: {api_response.status_code}")
                
                if api_response.status_code == 200:
                    data = api_response.json()
                    print(f"✅ API fonctionne")
                    print(f"📄 Infos fichier: {data.get('file_info', {})}")
                else:
                    print(f"❌ API erreur: {api_response.text[:200]}")
                    
            except Exception as e:
                print(f"❌ Erreur test API: {e}")
                
        else:
            print("❌ Aucune session avec fichier audio trouvée")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Erreur test fichier: {e}")
        return False

def main():
    """Fonction principale de diagnostic"""
    print("🔧 DIAGNOSTIC COMPLET DES PROBLÈMES AUDIO")
    print("=" * 80)
    
    results = {}
    
    # 1. Vérifier la base de données
    results['database'] = check_database_audio_files()
    
    # 2. Vérifier le répertoire media
    results['media_dir'] = check_media_directory()
    
    # 3. Créer des fichiers de test si nécessaire
    if not results['media_dir']:
        print("\n🔧 Création de fichiers audio de test...")
        results['created_files'] = create_test_audio_files()
    
    # 4. Tester les endpoints API
    test_api_endpoints()
    
    # 5. Tester un fichier spécifique
    results['file_access'] = test_specific_audio_file()
    
    # Résumé final
    print("\n" + "=" * 80)
    print("📋 RÉSUMÉ DU DIAGNOSTIC")
    print("=" * 80)
    
    for test, result in results.items():
        status = "✅ OK" if result else "❌ PROBLÈME"
        print(f"  {test}: {status}")
    
    # Recommandations
    print("\n💡 RECOMMANDATIONS:")
    
    if not results.get('database', False):
        print("  1. Exécuter: python create_test_data.py")
    
    if not results.get('media_dir', False):
        print("  2. Créer les répertoires media et définir les permissions")
        print("     sudo mkdir -p /home/jey/resumecours.gestionhospitaliare.site/backend/media/audio_sessions")
        print("     sudo chown -R apache:apache /home/jey/resumecours.gestionhospitaliare.site/backend/media/")
    
    if not results.get('file_access', False):
        print("  3. Vérifier la configuration Apache pour les fichiers media")
        print("  4. Redémarrer le serveur: sudo bash restart_server.sh")
    
    print("\n🎯 PROCHAINES ÉTAPES:")
    print("  1. Corriger les problèmes identifiés")
    print("  2. Relancer ce diagnostic")
    print("  3. Tester l'upload d'un vrai fichier audio")

if __name__ == '__main__':
    main()