#!/usr/bin/env python3
"""
Test des tokens d'authentification depuis l'environnement local
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://resumecours.gestionhospitaliare.site/api"

# Tokens générés en production
TOKENS = {
    'admin': 'BpwHsEvK2pHR6gLvBrT0jES9cbUeeghNMKmhNEk5',
    'cp': '65VjgtKRTHIiH39fnp5WOL7GLGohjT8L3yD5SqXb',
    'etudiant': 'pX7RHPWf4l3XvRLeeMrXHaHLpFmecutaOFYhrK8n'
}

def test_single_token(role, token):
    """Tester un token spécifique"""
    print(f"\n🔍 Test du token {role.upper()}:")
    print(f"   Token: {token[:20]}...")
    
    headers = {
        'Authorization': f'Token {token}',
        'Content-Type': 'application/json',
        'User-Agent': 'Resume+ Local Test Client'
    }
    
    results = {}
    
    # Test 1: Endpoint /auth/user/
    try:
        print(f"   📡 Test /auth/user/...")
        response = requests.get(f"{BASE_URL}/auth/user/", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Auth réussie: {data.get('email', 'N/A')}")
            print(f"   👤 ID: {data.get('id', 'N/A')}")
            print(f"   🏷️ Username: {data.get('username', 'N/A')}")
            results['auth'] = True
        elif response.status_code == 401:
            print(f"   ❌ Token invalide (401)")
            print(f"   📄 Réponse: {response.text[:100]}")
            results['auth'] = False
        else:
            print(f"   ❓ Status inattendu: {response.status_code}")
            results['auth'] = False
            
    except Exception as e:
        print(f"   ❌ Erreur auth: {e}")
        results['auth'] = False
    
    # Test 2: Endpoint /courses/
    try:
        print(f"   📚 Test /courses/...")
        response = requests.get(f"{BASE_URL}/courses/", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else data.get('count', 0)
            print(f"   ✅ Cours accessibles: {count}")
            results['courses'] = True
        else:
            print(f"   ❌ Erreur courses: {response.status_code}")
            results['courses'] = False
            
    except Exception as e:
        print(f"   ❌ Erreur courses: {e}")
        results['courses'] = False
    
    # Test 3: Endpoint /courses/sessions/audio/
    try:
        print(f"   🎵 Test /courses/sessions/audio/...")
        response = requests.get(f"{BASE_URL}/courses/sessions/audio/", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            sessions_count = len(data.get('sessions', []))
            print(f"   ✅ Sessions audio: {sessions_count}")
            results['audio_sessions'] = True
        elif response.status_code == 401:
            print(f"   ❌ Non autorisé pour les sessions audio")
            results['audio_sessions'] = False
        else:
            print(f"   ❓ Status sessions: {response.status_code}")
            results['audio_sessions'] = False
            
    except Exception as e:
        print(f"   ❌ Erreur sessions: {e}")
        results['audio_sessions'] = False
    
    # Test 4: Endpoint /summaries/
    try:
        print(f"   📝 Test /summaries/...")
        response = requests.get(f"{BASE_URL}/summaries/", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            summaries_count = len(data) if isinstance(data, list) else data.get('count', 0)
            print(f"   ✅ Résumés accessibles: {summaries_count}")
            results['summaries'] = True
        else:
            print(f"   ❌ Erreur summaries: {response.status_code}")
            results['summaries'] = False
            
    except Exception as e:
        print(f"   ❌ Erreur summaries: {e}")
        results['summaries'] = False
    
    return results

def test_all_tokens():
    """Tester tous les tokens"""
    print("🧪 TEST DE TOUS LES TOKENS D'AUTHENTIFICATION")
    print("=" * 60)
    print(f"🌐 Serveur: {BASE_URL}")
    print(f"📅 Date: {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}")
    
    all_results = {}
    
    for role, token in TOKENS.items():
        results = test_single_token(role, token)
        all_results[role] = results
        time.sleep(1)  # Pause entre les tests
    
    return all_results

def generate_test_report(results):
    """Générer un rapport de test"""
    print(f"\n📊 RAPPORT DE TEST")
    print("=" * 60)
    
    total_tests = 0
    passed_tests = 0
    
    for role, role_results in results.items():
        print(f"\n🔑 {role.upper()}:")
        
        for test_name, success in role_results.items():
            total_tests += 1
            if success:
                passed_tests += 1
                print(f"   ✅ {test_name}: OK")
            else:
                print(f"   ❌ {test_name}: ÉCHEC")
    
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n📈 RÉSUMÉ GLOBAL:")
    print(f"   Tests réussis: {passed_tests}/{total_tests}")
    print(f"   Taux de succès: {success_rate:.1f}%")
    
    if success_rate >= 75:
        print(f"   🎉 Excellent ! Les tokens fonctionnent bien")
    elif success_rate >= 50:
        print(f"   ⚠️ Partiellement fonctionnel - Vérifiez les permissions")
    else:
        print(f"   ❌ Problèmes détectés - Vérifiez la configuration")
    
    return success_rate

def test_flutter_integration():
    """Tester l'intégration Flutter simulée"""
    print(f"\n📱 TEST D'INTÉGRATION FLUTTER SIMULÉ")
    print("=" * 60)
    
    # Simuler une requête Flutter typique
    flutter_headers = {
        'Authorization': f'Token {TOKENS["cp"]}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'Flutter App/1.0'
    }
    
    try:
        print("🔍 Simulation d'une requête Flutter...")
        
        # Test de connexion utilisateur
        response = requests.get(f"{BASE_URL}/auth/user/", headers=flutter_headers, timeout=10)
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ Connexion Flutter simulée réussie")
            print(f"   👤 Utilisateur: {user_data.get('email')}")
            
            # Test de récupération des sessions audio
            audio_response = requests.get(f"{BASE_URL}/courses/sessions/audio/", headers=flutter_headers, timeout=10)
            
            if audio_response.status_code == 200:
                audio_data = audio_response.json()
                sessions_count = len(audio_data.get('sessions', []))
                print(f"✅ Sessions audio récupérées: {sessions_count}")
                
                if sessions_count > 0:
                    print(f"📱 L'app Flutter devrait maintenant fonctionner sans erreur 401!")
                else:
                    print(f"⚠️ Aucune session audio disponible")
            else:
                print(f"❌ Erreur sessions audio: {audio_response.status_code}")
        else:
            print(f"❌ Échec connexion Flutter: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur test Flutter: {e}")

def generate_flutter_usage_example():
    """Générer un exemple d'utilisation Flutter"""
    print(f"\n📝 EXEMPLE D'UTILISATION FLUTTER")
    print("=" * 60)
    
    flutter_code = f'''
// 1. Ajoutez cette classe dans votre projet Flutter
class AuthTokens {{
  static const String baseUrl = '{BASE_URL}';
  
  // Tokens générés en production
  static const String adminToken = '{TOKENS["admin"]}';
  static const String cpToken = '{TOKENS["cp"]}';
  static const String etudiantToken = '{TOKENS["etudiant"]}';
  
  static Map<String, String> getHeaders(String token) {{
    return {{
      'Authorization': 'Token $token',
      'Content-Type': 'application/json',
    }};
  }}
}}

// 2. Exemple d'utilisation
Future<void> testAuthentication() async {{
  try {{
    final response = await http.get(
      Uri.parse('${{AuthTokens.baseUrl}}/auth/user/'),
      headers: AuthTokens.getHeaders(AuthTokens.cpToken),
    );
    
    if (response.statusCode == 200) {{
      final userData = json.decode(response.body);
      print('Connecté: ${{userData['email']}}');
    }} else {{
      print('Erreur auth: ${{response.statusCode}}');
    }}
  }} catch (e) {{
    print('Erreur: $e');
  }}
}}
'''
    
    print(flutter_code)
    
    # Sauvegarder l'exemple
    try:
        with open('flutter_usage_example.dart', 'w') as f:
            f.write(flutter_code)
        print("✅ Exemple sauvegardé dans: flutter_usage_example.dart")
    except Exception as e:
        print(f"⚠️ Erreur sauvegarde: {e}")

def main():
    """Fonction principale de test"""
    print("🚀 TEST COMPLET DES TOKENS D'AUTHENTIFICATION")
    print("=" * 80)
    
    try:
        # 1. Tester tous les tokens
        results = test_all_tokens()
        
        # 2. Générer le rapport
        success_rate = generate_test_report(results)
        
        # 3. Tester l'intégration Flutter
        test_flutter_integration()
        
        # 4. Générer l'exemple Flutter
        generate_flutter_usage_example()
        
        # Conclusion
        print(f"\n" + "=" * 80)
        print("🎯 CONCLUSION")
        print("=" * 80)
        
        if success_rate >= 75:
            print("✅ Les tokens fonctionnent parfaitement !")
            print("📱 Votre app Flutter ne devrait plus avoir d'erreurs 401")
            print("🔑 Utilisez les tokens dans votre code Flutter")
        else:
            print("⚠️ Certains tests ont échoué")
            print("🔧 Vérifiez la configuration du serveur")
            print("📞 Contactez l'administrateur si nécessaire")
        
        print(f"\n💡 PROCHAINES ÉTAPES:")
        print(f"1. Copiez le code de flutter_usage_example.dart dans votre app")
        print(f"2. Remplacez vos anciens tokens par les nouveaux")
        print(f"3. Testez votre app Flutter")
        print(f"4. Les erreurs 401 devraient disparaître !")
        
    except KeyboardInterrupt:
        print(f"\n⏹️ Test interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur générale: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()