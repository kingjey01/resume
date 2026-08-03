// Tokens d'authentification générés automatiquement
import 'package:http/http.dart' as http;
import 'dart:convert' as json;

class AuthTokens {
  static const String baseUrl = 'https://resumecours.gestionhospitaliare.site/api';
  
  // Tokens de test
  static const String adminToken = 'BpwHsEvK2pHR6gLvBrT0jES9cbUeeghNMKmhNEk5';
  static const String cpToken = '65VjgtKRTHIiH39fnp5WOL7GLGohjT8L3yD5SqXb';
  static const String etudiantToken = 'pX7RHPWf4l3XvRLeeMrXHaHLpFmecutaOFYhrK8n';

  // Méthode pour tester l'authentification
  static Future<Map<String, dynamic>?> testAuth(String token) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/auth/user/'),
        headers: {
          'Authorization': 'Token $token',
          'Content-Type': 'application/json',
        },
      );
      
      if (response.statusCode == 200) {
        return json.jsonDecode(response.body);
      } else {
        print('Auth failed: ${response.statusCode}');
        return null;
      }
    } catch (e) {
      print('Auth error: $e');
      return null;
    }
  }
  
  // Test de tous les tokens
  static Future<void> testAllTokens() async {
    print('Testing CP token...');
    await testAuth(cpToken);
    
    print('Testing Etudiant token...');
    await testAuth(etudiantToken);
    
    print('Testing Admin token...');
    await testAuth(adminToken);
  }
  
  // Headers d'authentification
  static Map<String, String> getAuthHeaders(String token) {
    return {
      'Authorization': 'Token $token',
      'Content-Type': 'application/json',
    };
  }
}