#!/usr/bin/env python3
"""
Test de l'API de production pour Flutter
"""
import requests
import json

BASE_URL = "https://resumecours.gestionhospitaliare.site"
TOKEN = "9743c81fdd50b11c38a55fb9de24c56d8d4857dd"

def test_sessions_endpoint():
    """Test l'endpoint des sessions pour Flutter"""
    print("🔍 Test de l'endpoint des sessions pour Flutter...")
    
    headers = {
        'Authorization': f'Token {TOKEN}',
        'Content-Type': 'application/json'
    }
    
    try:
        # Test de l'URL corrigée (sans double /api/)
        response = requests.get(f"{BASE_URL}/api/courses/sessions/", headers=headers, timeout=10)
        print(f"📡 Réponse /api/courses/sessions/: {response.status_code}")
        
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
            
            # Analyser les sessions avec fichiers audio
            audio_sessions = [s for s in sessions if s.get('audio_file')]
            print(f"🎵 Sessions avec audio: {len(audio_sessions)}")
            
            # Afficher les détails des sessions audio
            for i, session in enumerate(audio_sessions[:3]):  # Afficher les 3 premières
                print(f"\n📁 Session {i+1}:")
                print(f"   ID: {session.get('id', 'N/A')}")
                print(f"   Titre: {session.get('title', 'Sans titre')}")
                print(f"   Cours: {session.get('course_name', 'N/A')}")
                print(f"   Professeur: {session.get('professeur', 'N/A')}")
                print(f"   Fichier: {session.get('audio_file', 'N/A')}")
                print(f"   Date: {session.get('created_at', 'N/A')}")
            
            return sessions
        else:
            print(f"❌ Erreur: {response.status_code}")
            print(f"📄 Contenu: {response.text[:500]}")
            return []
            
    except Exception as e:
        print(f"❌ Erreur de requête: {e}")
        return []

def test_audio_files_access(sessions):
    """Test l'accès aux fichiers audio pour Flutter"""
    print(f"\n🎵 Test d'accès aux fichiers audio pour Flutter...")
    
    audio_sessions = [s for s in sessions if s.get('audio_file')]
    print(f"📊 Sessions avec fichier audio: {len(audio_sessions)}")
    
    if not audio_sessions:
        print("❌ Aucune session avec fichier audio trouvée")
        return False
    
    success_count = 0
    
    for i, session in enumerate(audio_sessions[:3]):  # Tester les 3 premiers
        audio_file = session.get('audio_file', '')
        session_id = session.get('id', 'N/A')
        
        print(f"\n📁 Test session {i+1}/{min(3, len(audio_sessions))}")
        print(f"   ID: {session_id}")
        print(f"   Fichier: {audio_file}")
        
        # Construire l'URL complète comme Flutter le ferait
        if audio_file.startswith('http'):
            audio_url = audio_file
        else:
            audio_url = f"{BASE_URL}{audio_file}"
        
        print(f"   URL Flutter: {audio_url}")
        
        # Tester l'accès au fichier (comme Flutter le ferait)
        try:
            response = requests.head(audio_url, timeout=10)
            print(f"   📡 Réponse: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ Fichier accessible pour Flutter!")
                
                # Obtenir des informations sur le fichier
                content_length = response.headers.get('Content-Length')
                content_type = response.headers.get('Content-Type')
                
                if content_length:
                    size_kb = int(content_length) / 1024
                    print(f"   📏 Taille: {size_kb:.1f} KB")
                
                if content_type:
                    print(f"   🎵 Type MIME: {content_type}")
                
                success_count += 1
                
            elif response.status_code == 404:
                print(f"   ❌ Fichier non trouvé (404) - Flutter ne pourra pas lire")
            elif response.status_code == 403:
                print(f"   ❌ Accès interdit (403) - Problème de permissions")
            else:
                print(f"   ❌ Erreur {response.status_code} - Flutter aura des problèmes")
                
        except Exception as e:
            print(f"   ❌ Erreur d'accès: {e} - Flutter ne pourra pas se connecter")
    
    print(f"\n📊 Résumé pour Flutter: {success_count}/{min(3, len(audio_sessions))} fichiers accessibles")
    return success_count > 0

def test_flutter_api_simulation():
    """Simuler les appels API que Flutter va faire"""
    print(f"\n📱 Simulation des appels API Flutter...")
    
    headers = {
        'Authorization': f'Token {TOKEN}',
        'Content-Type': 'application/json'
    }
    
    # Test 1: Récupération des sessions (comme AudioPlaybackTestPage)
    print("🔄 Test 1: Récupération des sessions...")
    try:
        response = requests.get(f"{BASE_URL}/api/courses/sessions/", headers=headers, timeout=10)
        if response.status_code == 200:
            print("✅ Flutter pourra récupérer les sessions")
            sessions = response.json()
            if isinstance(sessions, dict) and 'results' in sessions:
                sessions = sessions['results']
            
            # Test 2: Vérification des URLs audio
            print("🔄 Test 2: Vérification des URLs audio...")
            audio_sessions = [s for s in sessions if s.get('audio_file')]
            
            if audio_sessions:
                test_session = audio_sessions[0]
                audio_url = test_session.get('audio_file')
                
                if audio_url and not audio_url.startswith('http'):
                    audio_url = f"{BASE_URL}{audio_url}"
                
                print(f"🎵 Test URL: {audio_url}")
                
                # Test d'accès comme le ferait AudioFilePlayerService
                audio_response = requests.head(audio_url, timeout=10)
                if audio_response.status_code == 200:
                    print("✅ Flutter pourra lire les fichiers audio")
                    print("✅ AudioFilePlayerService fonctionnera")
                else:
                    print(f"❌ Flutter aura des problèmes de lecture: {audio_response.status_code}")
            else:
                print("⚠️ Aucun fichier audio à tester")
        else:
            print(f"❌ Flutter ne pourra pas récupérer les sessions: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Flutter aura des erreurs de connexion: {e}")

def test_encoding_in_api_response():
    """Tester l'encodage dans les réponses API"""
    print(f"\n🔤 Test de l'encodage dans les réponses API...")
    
    headers = {
        'Authorization': f'Token {TOKEN}',
        'Content-Type': 'application/json'
    }
    
    try:
        # Test des résumés (qui peuvent contenir des emojis)
        response = requests.get(f"{BASE_URL}/api/summaries/", headers=headers, timeout=10)
        if response.status_code == 200:
            summaries = response.json()
            if isinstance(summaries, dict) and 'results' in summaries:
                summaries = summaries['results']
            
            print(f"📊 {len(summaries)} résumés récupérés")
            
            # Vérifier l'encodage des titres et textes
            encoding_issues = 0
            for summary in summaries[:5]:  # Vérifier les 5 premiers
                titre = summary.get('titre', '')
                texte = summary.get('texte_resume', '')
                
                if '\\x' in titre or '\\x' in texte or 'Ã' in titre:
                    encoding_issues += 1
                    print(f"⚠️ Problème d'encodage détecté dans résumé {summary.get('id')}")
                    print(f"   Titre: {titre[:50]}...")
            
            if encoding_issues == 0:
                print("✅ Aucun problème d'encodage détecté dans les résumés")
                print("✅ Flutter recevra des données correctement encodées")
            else:
                print(f"❌ {encoding_issues} résumés avec problèmes d'encodage")
                print("❌ Flutter pourrait afficher des caractères bizarres")
        else:
            print(f"❌ Impossible de tester l'encodage: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur lors du test d'encodage: {e}")

def main():
    print("🚀 TEST DE L'API DE PRODUCTION POUR FLUTTER")
    print("="*60)
    print(f"🌐 URL de base: {BASE_URL}")
    print(f"🔑 Token: {TOKEN[:20]}...")
    print("="*60)
    
    # Test 1: Endpoint des sessions
    sessions = test_sessions_endpoint()
    
    # Test 2: Accès aux fichiers audio
    if sessions:
        audio_accessible = test_audio_files_access(sessions)
    else:
        audio_accessible = False
    
    # Test 3: Simulation Flutter
    test_flutter_api_simulation()
    
    # Test 4: Encodage des réponses
    test_encoding_in_api_response()
    
    print(f"\n{'='*60}")
    print("📋 RÉSUMÉ POUR FLUTTER")
    print('='*60)
    
    if sessions:
        print("✅ API des sessions: FONCTIONNELLE")
    else:
        print("❌ API des sessions: PROBLÈME")
    
    if audio_accessible:
        print("✅ Fichiers audio: ACCESSIBLES")
        print("✅ AudioFilePlayerService: FONCTIONNERA")
    else:
        print("❌ Fichiers audio: PROBLÈME")
        print("❌ AudioFilePlayerService: NE FONCTIONNERA PAS")
    
    print(f"\n💡 ACTIONS POUR FLUTTER:")
    if sessions and audio_accessible:
        print("✅ Votre app Flutter devrait fonctionner parfaitement!")
        print("✅ Testez la page 'Test Lecture Audio' dans les paramètres")
    else:
        print("❌ Corrigez d'abord les problèmes d'API/fichiers")
        print("❌ Exécutez fix_production_encoding.py si nécessaire")

if __name__ == "__main__":
    main()