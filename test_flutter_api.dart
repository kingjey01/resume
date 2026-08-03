import 'package:flutter/material.dart';
import 'lib/services/api_service.dart';

/// Test simple pour vérifier les URLs de l'API Flutter
void main() async {
  print('🚀 TEST DES URLs API FLUTTER');
  print('='*50);
  
  final apiService = ApiService();
  
  // Test 1: Vérifier la configuration de base
  print('📊 Configuration API:');
  print('   Production: ${ApiService.isProduction}');
  print('   Base URL: ${ApiService.baseUrl}');
  
  // Test 2: Simuler l'appel qui pose problème
  print('\n🔍 Test de l\'URL des sessions:');
  try {
    print('   Appel: _apiService.get(\'/courses/sessions/\')');
    print('   URL finale attendue: ${ApiService.baseUrl}/courses/sessions/');
    print('   ✅ Cette URL devrait être correcte');
    
    // Vérifier s'il y a d'autres méthodes qui pourraient causer le problème
    print('\n⚠️  Vérification des autres appels possibles:');
    print('   ❌ Ne PAS utiliser: _apiService.get(\'/api/courses/sessions/\')');
    print('   ❌ Cela donnerait: ${ApiService.baseUrl}/api/courses/sessions/');
    print('   ✅ Utiliser: _apiService.get(\'/courses/sessions/\')');
    print('   ✅ Cela donne: ${ApiService.baseUrl}/courses/sessions/');
    
  } catch (e) {
    print('   ❌ Erreur: $e');
  }
  
  print('\n💡 SOLUTION:');
  print('1. Vérifiez que tous les appels API utilisent des chemins relatifs sans /api/');
  print('2. Recompilez l\'application Flutter');
  print('3. Videz le cache du navigateur si vous testez sur le web');
  print('4. Redémarrez l\'application complètement');
}