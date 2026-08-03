
// 1. Ajoutez cette classe dans votre projet Flutter
class AuthTokens {
  static const String baseUrl = 'https://resumecours.gestionhospitaliare.site/api';
  
  // Tokens générés en production
  static const String adminToken = '***REMOVED***';
  static const String cpToken = '***REMOVED***';
  static const String etudiantToken = '***REMOVED***';
  
  static Map<String, String> getHeaders(String token) {
    return {
      'Authorization': 'Token $token',
      'Content-Type': 'application/json',
    };
  }
}

// 2. Exemple d'utilisation
Future<void> testAuthentication() async {
  try {
    final response = await http.get(
      Uri.parse('${AuthTokens.baseUrl}/auth/user/'),
      headers: AuthTokens.getHeaders(AuthTokens.cpToken),
    );
    
    if (response.statusCode == 200) {
      final userData = json.decode(response.body);
      print('Connecté: ${userData['email']}');
    } else {
      print('Erreur auth: ${response.statusCode}');
    }
  } catch (e) {
    print('Erreur: $e');
  }
}
