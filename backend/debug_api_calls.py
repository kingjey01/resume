#!/usr/bin/env python3
"""
Script pour déboguer les appels API et identifier les URLs dupliquées
"""
import requests
import json
from datetime import datetime

BASE_URL = "https://resumecours.gestionhospitaliare.site"
TOKEN = "9743c81fdd50b11c38a55fb9de24c56d8d4857dd"

def test_all_possible_urls():
    """Tester toutes les URLs possibles pour identifier le problème"""
    print("🔍 Test de toutes les URLs possibles...")
    
    headers = {
        'Authorization': f'Token {TOKEN}',
        'Content-Type': 'application/json'
    }
    
    # URLs à tester
    test_urls = [
        "/api/courses/sessions/",           # ✅ Correct
        "/api/api/courses/sessions/",       # ❌ Problématique (double /api/)
        "/courses/sessions/",               # ❌ Sans /api/ initial
        "/api/courses/sessions",            # ❌ Sans / final
        "/api/courses/sessions/?format=json", # ✅ Avec paramètre
    ]
    
    for url in test_urls:
        full_url = f"{BASE_URL}{url}"
        print(f"\n🔗 Test: {url}")
        print(f"   URL complète: {full_url}")
        
        try:
            response = requests.get(full_url, headers=headers, timeout=5)
            print(f"   📡 Réponse: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ FONCTIONNE")
                data = response.json()
                if isinstance(data, list):
                    sessions_count = len(data)
                elif isinstance(data, dict) and 'results' in data:
                    sessions_count = len(data['results'])
                else:
                    sessions_count = 0
                print(f"   📊 Sessions: {sessions_count}")
            elif response.status_code == 404:
                print(f"   ❌ NOT FOUND - Cette URL est utilisée par Flutter!")
            else:
                print(f"   ⚠️ Erreur: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Erreur de connexion: {e}")

def simulate_flutter_calls():
    """Simuler exactement les appels que Flutter devrait faire"""
    print(f"\n📱 Simulation des appels Flutter...")
    
    headers = {
        'Authorization': f'Token {TOKEN}',
        'Content-Type': 'application/json'
    }
    
    # Simuler l'appel de AudioPlaybackTestPage
    print("🔄 Simulation: AudioPlaybackTestPage._loadAudioSessions()")
    print("   Code Flutter: await _apiService.get('/courses/sessions/')")
    print("   Base URL: https://resumecours.gestionhospitaliare.site/api")
    print("   URL finale: https://resumecours.gestionhospitaliare.site/api/courses/sessions/")
    
    try:
        response = requests.get(f"{BASE_URL}/api/courses/sessions/", headers=headers, timeout=10)
        print(f"   📡 Résultat: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Flutter devrait recevoir les données correctement")
            data = response.json()
            if isinstance(data, list):
                sessions = data
            elif isinstance(data, dict) and 'results' in data:
                sessions = data['results']
            else:
                sessions = []
            
            audio_sessions = [s for s in sessions if s.get('audio_file')]
            print(f"   📊 Sessions avec audio: {len(audio_sessions)}")
            
            if audio_sessions:
                print("   🎵 Exemple de session:")
                session = audio_sessions[0]
                print(f"      ID: {session.get('id')}")
                print(f"      Fichier: {session.get('audio_file')}")
        else:
            print(f"   ❌ Flutter recevra une erreur: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Flutter aura une erreur de connexion: {e}")

def check_django_urls():
    """Vérifier la configuration des URLs Django"""
    print(f"\n🔧 Vérification de la configuration Django...")
    
    # Tester les endpoints Django directement
    endpoints_to_test = [
        ("/api/", "API Root"),
        ("/api/courses/", "Courses API"),
        ("/api/courses/sessions/", "Sessions API"),
        ("/admin/", "Django Admin"),
    ]
    
    for endpoint, name in endpoints_to_test:
        url = f"{BASE_URL}{endpoint}"
        print(f"\n🔗 {name}: {endpoint}")
        
        try:
            # Test sans authentification d'abord
            response = requests.get(url, timeout=5)
            print(f"   📡 Sans auth: {response.status_code}")
            
            # Test avec authentification
            headers = {'Authorization': f'Token {TOKEN}'}
            response = requests.get(url, headers=headers, timeout=5)
            print(f"   📡 Avec auth: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ Endpoint fonctionnel")
            elif response.status_code == 404:
                print(f"   ❌ Endpoint non trouvé - Vérifiez urls.py")
            elif response.status_code == 403:
                print(f"   ⚠️ Accès interdit - Problème d'authentification")
            else:
                print(f"   ⚠️ Statut inattendu: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Erreur: {e}")

def generate_flutter_debug_code():
    """Générer du code Flutter pour déboguer"""
    print(f"\n💻 Code Flutter pour déboguer:")
    
    debug_code = '''
// Ajoutez ce code dans votre AudioPlaybackTestPage pour déboguer
Future<void> _debugApiCall() async {
  print('🔍 DEBUG: Base URL: \${ApiService.baseUrl}');
  print('🔍 DEBUG: Appel: /courses/sessions/');
  print('🔍 DEBUG: URL finale: \${ApiService.baseUrl}/courses/sessions/');
  
  try {
    final response = await _apiService.get('/courses/sessions/');
    print('✅ DEBUG: Succès - Status: \${response.statusCode}');
  } catch (e) {
    print('❌ DEBUG: Erreur - \$e');
  }
}
'''
    
    print(debug_code)

def main():
    print("🚀 DÉBOGAGE DES APPELS API FLUTTER")
    print("="*60)
    print(f"🌐 Serveur: {BASE_URL}")
    print(f"🔑 Token: {TOKEN[:20]}...")
    print(f"⏰ Heure: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Test 1: Toutes les URLs possibles
    test_all_possible_urls()
    
    # Test 2: Simulation Flutter
    simulate_flutter_calls()
    
    # Test 3: Configuration Django
    check_django_urls()
    
    # Test 4: Code de débogage
    generate_flutter_debug_code()
    
    print(f"\n{'='*60}")
    print("📋 RÉSUMÉ DU DÉBOGAGE")
    print('='*60)
    print("✅ URL correcte: /api/courses/sessions/")
    print("❌ URL problématique: /api/api/courses/sessions/")
    print("\n💡 SOLUTIONS:")
    print("1. Vérifiez que Flutter utilise bien '/courses/sessions/' (sans /api/ au début)")
    print("2. Recompilez l'application Flutter")
    print("3. Videz le cache du navigateur")
    print("4. Redémarrez l'application complètement")
    print("5. Vérifiez les logs du serveur pour identifier la source de l'appel")

if __name__ == "__main__":
    main()