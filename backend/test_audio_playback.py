#!/usr/bin/env python3
"""
Test de lecture des fichiers audio uploadés
"""
import requests
import json
import os

BASE_URL = "https://resumecours.gestionhospitaliare.site"
TOKEN = "9743c81fdd50b11c38a55fb9de24c56d8d4857dd"

def test_sessions_endpoint():
    """Test l'endpoint des sessions"""
    print("🔍 Test de l'endpoint des sessions...")
    
    headers = {
        'Authorization': f'Token {TOKEN}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(f"{BASE_URL}/api/courses/sessions/", headers=headers, timeout=10)
        print(f"📡 Réponse: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Sessions récupérées avec succès!")
            
            if isinstance(data, list):
                sessions = data
            elif isinstance(data, dict) and 'results' in data:
                sessions = data['results']
            else:
                sessions = []
            
            print(f"📊 Nombre de sessions: {len(sessions)}")
            
            return sessions
        else:
            print(f"❌ Erreur: {response.status_code}")
            print(f"📄 Contenu: {response.text[:500]}")
            return []
            
    except Exception as e:
        print(f"❌ Erreur de requête: {e}")
        return []

def test_audio_file_access(sessions):
    """Test l'accès aux fichiers audio"""
    print(f"\n🎵 Test d'accès aux fichiers audio...")
    
    audio_sessions = [s for s in sessions if s.get('audio_file')]
    print(f"📊 Sessions avec fichier audio: {len(audio_sessions)}")
    
    if not audio_sessions:
        print("❌ Aucune session avec fichier audio trouvée")
        return False
    
    success_count = 0
    
    for i, session in enumerate(audio_sessions[:5]):  # Tester les 5 premiers
        audio_file = session.get('audio_file', '')
        session_id = session.get('id', 'N/A')
        title = session.get('title', 'Sans titre')
        
        print(f"\n📁 Session {i+1}/{min(5, len(audio_sessions))}")
        print(f"   ID: {session_id}")
        print(f"   Titre: {title}")
        print(f"   Fichier: {audio_file}")
        
        # Construire l'URL complète
        if audio_file.startswith('http'):
            audio_url = audio_file
        else:
            audio_url = f"{BASE_URL}{audio_file}"
        
        print(f"   URL: {audio_url}")
        
        # Tester l'accès au fichier
        try:
            response = requests.head(audio_url, timeout=10)
            print(f"   📡 Réponse: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ Fichier accessible!")
                
                # Obtenir des informations sur le fichier
                content_length = response.headers.get('Content-Length')
                content_type = response.headers.get('Content-Type')
                
                if content_length:
                    size_kb = int(content_length) / 1024
                    print(f"   📏 Taille: {size_kb:.1f} KB")
                
                if content_type:
                    print(f"   🎵 Type: {content_type}")
                
                success_count += 1
                
            elif response.status_code == 404:
                print(f"   ❌ Fichier non trouvé (404)")
            elif response.status_code == 403:
                print(f"   ❌ Accès interdit (403)")
            else:
                print(f"   ❌ Erreur {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Erreur d'accès: {e}")
    
    print(f"\n📊 Résumé: {success_count}/{min(5, len(audio_sessions))} fichiers accessibles")
    return success_count > 0

def test_direct_audio_access():
    """Test d'accès direct aux fichiers audio"""
    print(f"\n🎯 Test d'accès direct aux fichiers audio...")
    
    # Tester quelques chemins typiques
    test_paths = [
        "/media/audio_sessions/test_recording.wav",
        "/static/media/audio_sessions/test_recording.wav",
        "/media/audio_sessions/",
    ]
    
    for path in test_paths:
        url = f"{BASE_URL}{path}"
        print(f"\n🔗 Test: {url}")
        
        try:
            response = requests.head(url, timeout=10)
            print(f"   📡 Réponse: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ Accessible!")
                
                content_length = response.headers.get('Content-Length')
                if content_length:
                    size_kb = int(content_length) / 1024
                    print(f"   📏 Taille: {size_kb:.1f} KB")
                    
            elif response.status_code == 404:
                print(f"   ❌ Non trouvé")
            elif response.status_code == 403:
                print(f"   ❌ Accès interdit")
            else:
                print(f"   ❌ Erreur {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Erreur: {e}")

def test_media_directory_listing():
    """Test de listage du répertoire media"""
    print(f"\n📂 Test de listage du répertoire media...")
    
    media_urls = [
        f"{BASE_URL}/media/",
        f"{BASE_URL}/media/audio_sessions/",
        f"{BASE_URL}/static/media/",
        f"{BASE_URL}/static/media/audio_sessions/",
    ]
    
    for url in media_urls:
        print(f"\n📁 Test: {url}")
        
        try:
            response = requests.get(url, timeout=10)
            print(f"   📡 Réponse: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ Accessible!")
                content = response.text[:500]
                if 'test_recording' in content.lower() or '.wav' in content.lower():
                    print(f"   🎵 Fichiers audio détectés dans le listing")
                else:
                    print(f"   📄 Contenu: {content[:100]}...")
                    
            elif response.status_code == 403:
                print(f"   ❌ Accès interdit (normal pour la sécurité)")
            elif response.status_code == 404:
                print(f"   ❌ Répertoire non trouvé")
            else:
                print(f"   ❌ Erreur {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Erreur: {e}")

def main():
    print("🚀 TEST DE LECTURE DES FICHIERS AUDIO")
    print("="*60)
    
    # Test 1: Récupérer les sessions
    sessions = test_sessions_endpoint()
    
    # Test 2: Tester l'accès aux fichiers audio
    if sessions:
        audio_accessible = test_audio_file_access(sessions)
    else:
        audio_accessible = False
    
    # Test 3: Test d'accès direct
    test_direct_audio_access()
    
    # Test 4: Test de listage des répertoires
    test_media_directory_listing()
    
    print(f"\n{'='*60}")
    print("📋 RÉSUMÉ DU TEST")
    print('='*60)
    
    if sessions:
        print("✅ Récupération des sessions: OK")
    else:
        print("❌ Récupération des sessions: ÉCHEC")
    
    if audio_accessible:
        print("✅ Accès aux fichiers audio: OK")
        print("✅ Votre système de lecture devrait fonctionner!")
    else:
        print("❌ Accès aux fichiers audio: ÉCHEC")
        print("❌ Problème de configuration des fichiers statiques")
    
    print(f"\n💡 CONSEILS:")
    print("1. Vérifiez la configuration MEDIA_URL et MEDIA_ROOT dans Django")
    print("2. Vérifiez la configuration Nginx pour servir les fichiers media")
    print("3. Vérifiez les permissions des fichiers (755 pour les dossiers, 644 pour les fichiers)")
    print("4. Testez la page Flutter: AudioPlaybackTestPage")

if __name__ == "__main__":
    main()