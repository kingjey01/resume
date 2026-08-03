#!/usr/bin/env python3
"""
Test des fonctionnalités audio en PRODUCTION
"""

import requests
import json
import time
from datetime import datetime

# Configuration PRODUCTION
BASE_URL = "https://resumecours.gestionhospitaliare.site/api/courses"
MEDIA_BASE_URL = "https://resumecours.gestionhospitaliare.site/media"

def test_production_endpoints():
    """Tester tous les endpoints audio en production"""
    print("🌐 TEST DES ENDPOINTS AUDIO EN PRODUCTION")
    print("=" * 60)
    print(f"🔗 URL de base: {BASE_URL}")
    print(f"📁 Media URL: {MEDIA_BASE_URL}")
    print()
    
    # Liste des endpoints à tester
    endpoints = [
        {
            'url': '/courses/',
            'name': 'Liste des cours',
            'method': 'GET',
            'auth_required': False
        },
        {
            'url': '/sessions/',
            'name': 'Liste des sessions',
            'method': 'GET',
            'auth_required': False
        },
        {
            'url': '/sessions/audio/',
            'name': 'Sessions audio',
            'method': 'GET',
            'auth_required': True
        },
        {
            'url': '/sessions/audio/stats/',
            'name': 'Statistiques audio',
            'method': 'GET',
            'auth_required': True
        },
        {
            'url': '/summaries/',
            'name': 'Liste des résumés',
            'method': 'GET',
            'auth_required': True
        }
    ]
    
    results = {}
    
    for endpoint in endpoints:
        print(f"🔍 Test: {endpoint['name']}")
        url = BASE_URL + endpoint['url']
        print(f"   URL: {url}")
        
        try:
            # Headers de base
            headers = {
                'User-Agent': 'Resume+ Audio Test Client',
                'Accept': 'application/json'
            }
            
            # Faire la requête
            response = requests.get(url, headers=headers, timeout=15)
            
            print(f"   📊 Status: {response.status_code}")
            
            # Analyser la réponse
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    if isinstance(data, list):
                        count = len(data)
                        print(f"   ✅ Succès: {count} éléments")
                        
                        # Afficher quelques exemples
                        if count > 0 and isinstance(data[0], dict):
                            keys = list(data[0].keys())[:5]
                            print(f"   📋 Champs: {keys}")
                    
                    elif isinstance(data, dict):
                        if 'count' in data:
                            print(f"   ✅ Succès: {data['count']} éléments (paginé)")
                        elif 'sessions' in data:
                            sessions = data['sessions']
                            print(f"   ✅ Succès: {len(sessions)} sessions audio")
                            
                            # Analyser les sessions audio
                            if sessions:
                                session = sessions[0]
                                print(f"   🎵 Exemple session: {session.get('course_name', 'N/A')}")
                                if 'audio_info' in session:
                                    audio_info = session['audio_info']
                                    print(f"   📁 Fichier: {audio_info.get('file_name', 'N/A')}")
                                    print(f"   📏 Taille: {audio_info.get('file_size_mb', 0)}MB")
                        
                        elif 'stats' in data:
                            stats = data['stats']
                            print(f"   📊 Sessions totales: {stats.get('total_audio_sessions', 0)}")
                            print(f"   📊 Sessions traitées: {stats.get('processed_sessions', 0)}")
                        
                        else:
                            keys = list(data.keys())[:5]
                            print(f"   ✅ Succès: Clés {keys}")
                    
                    results[endpoint['name']] = {
                        'status': 'success',
                        'code': response.status_code,
                        'data_type': type(data).__name__
                    }
                
                except json.JSONDecodeError:
                    print(f"   ⚠️ Réponse non-JSON")
                    print(f"   📄 Contenu: {response.text[:100]}...")
                    results[endpoint['name']] = {
                        'status': 'non_json',
                        'code': response.status_code
                    }
            
            elif response.status_code == 401:
                print(f"   🔐 Authentification requise")
                results[endpoint['name']] = {
                    'status': 'auth_required',
                    'code': response.status_code
                }
            
            elif response.status_code == 403:
                print(f"   🚫 Accès interdit")
                results[endpoint['name']] = {
                    'status': 'forbidden',
                    'code': response.status_code
                }
            
            elif response.status_code == 404:
                print(f"   ❌ Endpoint non trouvé")
                results[endpoint['name']] = {
                    'status': 'not_found',
                    'code': response.status_code
                }
            
            else:
                print(f"   ❌ Erreur: {response.status_code}")
                print(f"   📄 Message: {response.text[:200]}")
                results[endpoint['name']] = {
                    'status': 'error',
                    'code': response.status_code,
                    'message': response.text[:200]
                }
        
        except requests.exceptions.Timeout:
            print(f"   ⏰ Timeout (>15s)")
            results[endpoint['name']] = {'status': 'timeout'}
        
        except requests.exceptions.ConnectionError:
            print(f"   🔌 Erreur de connexion")
            results[endpoint['name']] = {'status': 'connection_error'}
        
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            results[endpoint['name']] = {'status': 'exception', 'error': str(e)}
        
        print()  # Ligne vide entre les tests
    
    return results

def test_specific_audio_sessions():
    """Tester des sessions audio spécifiques"""
    print("🎵 TEST DES SESSIONS AUDIO SPÉCIFIQUES")
    print("=" * 60)
    
    # D'abord récupérer la liste des sessions
    try:
        response = requests.get(f"{BASE_URL}/sessions/", timeout=10)
        
        if response.status_code == 200:
            sessions = response.json()
            
            if isinstance(sessions, list) and sessions:
                print(f"📊 {len(sessions)} sessions trouvées")
                
                # Tester les premières sessions
                for i, session in enumerate(sessions[:5]):
                    session_id = session.get('id')
                    if not session_id:
                        continue
                    
                    print(f"\n🎵 Test session {session_id}:")
                    print(f"   📚 Cours: {session.get('course', 'N/A')}")
                    print(f"   👨‍🏫 Professeur: {session.get('professeur', 'N/A')}")
                    
                    # Test endpoint audio-file
                    audio_url = f"{BASE_URL}/sessions/{session_id}/audio-file/"
                    try:
                        audio_response = requests.get(audio_url, timeout=10)
                        print(f"   📁 audio-file: {audio_response.status_code}")
                        
                        if audio_response.status_code == 200:
                            try:
                                audio_data = audio_response.json()
                                if audio_data.get('success'):
                                    file_info = audio_data.get('file_info', {})
                                    print(f"   ✅ Fichier trouvé: {file_info.get('name', 'N/A')}")
                                    print(f"   📏 Taille: {file_info.get('size_mb', 0)}MB")
                                    print(f"   🔗 URL: {audio_data.get('audio_url', 'N/A')}")
                                    
                                    # Tester l'accès direct au fichier
                                    direct_url = audio_data.get('audio_url')
                                    if direct_url:
                                        try:
                                            direct_response = requests.head(direct_url, timeout=5)
                                            print(f"   🌐 Accès direct: {direct_response.status_code}")
                                            
                                            if direct_response.status_code == 200:
                                                content_type = direct_response.headers.get('content-type', 'N/A')
                                                content_length = direct_response.headers.get('content-length', 'N/A')
                                                print(f"   🎵 Type: {content_type}")
                                                print(f"   📏 Taille header: {content_length} bytes")
                                        except Exception as e:
                                            print(f"   ❌ Erreur accès direct: {e}")
                                else:
                                    print(f"   ❌ Erreur API: {audio_data.get('error', 'Inconnue')}")
                            except json.JSONDecodeError:
                                print(f"   ⚠️ Réponse non-JSON")
                        
                        elif audio_response.status_code == 401:
                            print(f"   🔐 Authentification requise")
                        elif audio_response.status_code == 404:
                            print(f"   ❌ Session ou fichier non trouvé")
                        else:
                            print(f"   ❌ Erreur: {audio_response.status_code}")
                    
                    except Exception as e:
                        print(f"   ❌ Erreur test audio: {e}")
                    
                    # Test endpoint serve-audio
                    serve_url = f"{BASE_URL}/sessions/{session_id}/serve-audio/"
                    try:
                        serve_response = requests.head(serve_url, timeout=5)
                        print(f"   🎵 serve-audio: {serve_response.status_code}")
                        
                        if serve_response.status_code == 200:
                            content_type = serve_response.headers.get('content-type', 'N/A')
                            content_length = serve_response.headers.get('content-length', 'N/A')
                            accept_ranges = serve_response.headers.get('accept-ranges', 'N/A')
                            print(f"   ✅ Streaming OK - Type: {content_type}")
                            print(f"   📏 Taille: {content_length} bytes")
                            print(f"   🔄 Ranges: {accept_ranges}")
                    
                    except Exception as e:
                        print(f"   ❌ Erreur serve-audio: {e}")
            
            else:
                print("❌ Aucune session trouvée ou format incorrect")
        
        else:
            print(f"❌ Erreur récupération sessions: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Erreur test sessions: {e}")

def test_media_directory_access():
    """Tester l'accès direct au répertoire media"""
    print("\n📁 TEST D'ACCÈS AU RÉPERTOIRE MEDIA")
    print("=" * 60)
    
    media_urls = [
        f"{MEDIA_BASE_URL}/",
        f"{MEDIA_BASE_URL}/audio_sessions/",
    ]
    
    for url in media_urls:
        print(f"🔗 Test: {url}")
        
        try:
            response = requests.get(url, timeout=10)
            print(f"   📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', 'N/A')
                print(f"   ✅ Accessible - Type: {content_type}")
                
                # Si c'est du HTML, chercher des fichiers audio
                if 'text/html' in content_type:
                    content = response.text
                    audio_files = []
                    for ext in ['.wav', '.mp3', '.m4a', '.ogg']:
                        if ext in content:
                            # Extraire les noms de fichiers (simple)
                            import re
                            pattern = rf'[\w\-_]+{re.escape(ext)}'
                            matches = re.findall(pattern, content)
                            audio_files.extend(matches)
                    
                    if audio_files:
                        print(f"   🎵 Fichiers audio trouvés: {len(set(audio_files))}")
                        for file in list(set(audio_files))[:3]:
                            print(f"      - {file}")
                    else:
                        print(f"   ⚠️ Aucun fichier audio visible")
            
            elif response.status_code == 403:
                print(f"   🚫 Accès interdit (normal pour la sécurité)")
            elif response.status_code == 404:
                print(f"   ❌ Répertoire non trouvé")
            else:
                print(f"   ❌ Erreur: {response.status_code}")
        
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
        
        print()

def generate_production_test_report():
    """Générer un rapport de test complet pour la production"""
    print("\n📋 GÉNÉRATION DU RAPPORT DE TEST PRODUCTION")
    print("=" * 60)
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'server': BASE_URL,
        'tests': {}
    }
    
    # Exécuter tous les tests
    print("🔄 Exécution des tests...")
    
    try:
        # Test des endpoints
        endpoint_results = test_production_endpoints()
        report['tests']['endpoints'] = endpoint_results
        
        # Test des sessions audio
        print("\n" + "="*40)
        test_specific_audio_sessions()
        
        # Test du répertoire media
        print("\n" + "="*40)
        test_media_directory_access()
        
        # Résumé final
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ DU TEST PRODUCTION")
        print("=" * 60)
        
        successful_endpoints = sum(1 for result in endpoint_results.values() 
                                 if result.get('status') == 'success')
        total_endpoints = len(endpoint_results)
        
        print(f"🌐 Serveur testé: {BASE_URL}")
        print(f"📊 Endpoints testés: {total_endpoints}")
        print(f"✅ Endpoints fonctionnels: {successful_endpoints}")
        print(f"📈 Taux de succès: {(successful_endpoints/total_endpoints*100):.1f}%")
        
        print(f"\n📋 Détail par endpoint:")
        for name, result in endpoint_results.items():
            status_icon = {
                'success': '✅',
                'auth_required': '🔐',
                'not_found': '❌',
                'error': '❌',
                'timeout': '⏰',
                'connection_error': '🔌'
            }.get(result.get('status'), '❓')
            
            print(f"   {status_icon} {name}: {result.get('status')} ({result.get('code', 'N/A')})")
        
        # Recommandations
        print(f"\n💡 RECOMMANDATIONS:")
        
        if successful_endpoints < total_endpoints:
            print("   1. Vérifiez que le serveur Django fonctionne")
            print("   2. Contrôlez les logs Apache/Gunicorn")
            print("   3. Testez la connectivité réseau")
        
        auth_required_count = sum(1 for result in endpoint_results.values() 
                                if result.get('status') == 'auth_required')
        if auth_required_count > 0:
            print(f"   4. {auth_required_count} endpoints nécessitent une authentification")
            print("   5. Créez un token d'API pour les tests complets")
        
        if successful_endpoints == total_endpoints:
            print("   ✅ Tous les endpoints publics fonctionnent correctement!")
            print("   🎯 Prochaine étape: Tester avec authentification")
        
        # Sauvegarder le rapport
        report_file = f"/tmp/production_audio_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Rapport sauvegardé: {report_file}")
        
    except Exception as e:
        print(f"❌ Erreur génération rapport: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Fonction principale"""
    print("🚀 TEST COMPLET AUDIO EN PRODUCTION")
    print("=" * 80)
    print(f"🌐 Serveur: {BASE_URL}")
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    try:
        # Générer le rapport complet
        generate_production_test_report()
        
        print(f"\n🎯 PROCHAINES ÉTAPES:")
        print(f"1. Si des endpoints échouent, vérifiez les logs serveur")
        print(f"2. Pour les tests avec authentification, créez un token API")
        print(f"3. Testez l'upload d'un fichier audio via l'interface web")
        print(f"4. Vérifiez la lecture audio dans l'application Flutter")
        
    except KeyboardInterrupt:
        print(f"\n⏹️ Test interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur générale: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()