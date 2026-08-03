import 'package:dio/dio.dart';

/// Service API de debug avec URLs absolues pour contourner le problème de cache
class ApiServiceDebug {
  final Dio _dio = Dio();
  static const String token = '9743c81fdd50b11c38a55fb9de24c56d8d4857dd';
  
  /// Récupérer les sessions audio avec URL absolue
  Future<List<Map<String, dynamic>>> getAudioSessionsDebug() async {
    const url = 'https://resumecours.gestionhospitaliare.site/api/courses/sessions/';
    
    final headers = {
      'Authorization': 'Token $token',
      'Content-Type': 'application/json',
    };
    
    print('🔍 DEBUG: URL absolue utilisée: $url');
    
    try {
      final response = await _dio.get(
        url,
        options: Options(headers: headers),
      );
      
      print('✅ DEBUG: Réponse reçue: ${response.statusCode}');
      
      if (response.statusCode == 200) {
        dynamic data = response.data;
        List<dynamic> sessionsList;
        
        if (data is List) {
          sessionsList = data;
        } else if (data is Map && data.containsKey('results')) {
          sessionsList = data['results'] as List;
        } else {
          sessionsList = [];
        }
        
        print('📊 DEBUG: ${sessionsList.length} sessions récupérées');
        
        // Filtrer les sessions avec audio
        final audioSessions = sessionsList
            .where((session) => session['audio_file'] != null && session['audio_file'].toString().isNotEmpty)
            .cast<Map<String, dynamic>>()
            .toList();
            
        print('🎵 DEBUG: ${audioSessions.length} sessions avec audio');
        
        return audioSessions;
      } else {
        throw Exception('Erreur HTTP: ${response.statusCode}');
      }
    } catch (e) {
      print('❌ DEBUG: Erreur lors de l\'appel API: $e');
      rethrow;
    }
  }
  
  /// Tester la connectivité API
  Future<bool> testApiConnectivity() async {
    const url = 'https://resumecours.gestionhospitaliare.site/api/';
    
    final headers = {
      'Authorization': 'Token $token',
      'Content-Type': 'application/json',
    };
    
    try {
      final response = await _dio.get(
        url,
        options: Options(headers: headers),
      );
      
      return response.statusCode == 200;
    } catch (e) {
      print('❌ Test de connectivité échoué: $e');
      return false;
    }
  }
}