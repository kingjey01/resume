import 'package:dio/dio.dart';
import 'package:resume_plus_clean/services/storage_service.dart';
import 'package:resume_plus_clean/services/api_service.dart'; // Added import statement

class SimpleLoginService {
  static String get baseUrl => ApiService.baseUrl;
  final Dio _dio = Dio(BaseOptions(baseUrl: baseUrl));
  final StorageService _storage = StorageService();
  
  // Variable pour stocker le token temporairement
  String? _currentToken;

  Future<Map<String, dynamic>> login(String username, String password) async {
    try {
      print('🔑 Tentative de connexion: $username');
      
      final response = await _dio.post('/auth/login/', data: {
        'username': username,
        'password': password,
      });

      if (response.statusCode == 200) {
        final data = response.data;
        final accessToken = data['access'];
        final refreshToken = data['refresh'];
        
        // Sauvegarder le token en mémoire pour éviter les problèmes de storage web
        _currentToken = accessToken;
        
        // Essayer de sauvegarder dans le storage (peut échouer sur web)
        try {
          await _storage.writeTokens(
            accessToken: accessToken,
            refreshToken: refreshToken,
          );
          print('✅ Connexion réussie, tokens sauvegardés');
        } catch (e) {
          print('⚠️ Erreur storage, token gardé en mémoire: $e');
        }
        
        return {
          'success': true,
          'message': 'Connexion réussie',
          'user': data['user'],
          'tokens': {
            'access': accessToken,
            'refresh': refreshToken,
          }
        };
      } else {
        print('❌ Erreur de connexion: ${response.statusCode}');
        return {
          'success': false,
          'message': 'Erreur de connexion: ${response.statusCode}',
        };
      }
    } catch (e) {
      print('❌ Exception lors de la connexion: $e');
      
      if (e is DioException) {
        final errorMessage = e.response?.data?['non_field_errors']?.first ?? 
                           e.response?.data?.toString() ?? 
                           'Erreur de connexion';
        return {
          'success': false,
          'message': errorMessage,
        };
      }
      
      return {
        'success': false,
        'message': 'Erreur inattendue: $e',
      };
    }
  }

  Future<bool> isLoggedIn() async {
    final token = await _storage.accessToken;
    return token != null;
  }

  Future<void> logout() async {
    _currentToken = null; // Effacer le token en mémoire
    await _storage.deleteTokens();
    print('🚪 Déconnexion effectuée');
  }

  Future<Map<String, dynamic>> getSummaries() async {
    try {
      print('🔍 DEBUG: Début getSummaries');
      
      // Essayer d'abord le token en mémoire, puis le storage
      String? token = _currentToken;
      if (token == null) {
        try {
          token = await _storage.accessToken;
        } catch (e) {
          print('⚠️ Erreur storage, utilisation token en mémoire');
        }
      }
      
      if (token == null) {
        return {
          'success': false,
          'message': 'Token non trouvé, veuillez vous reconnecter',
        };
      }

      print('🔍 DEBUG: Appel API /summaries/ avec token');
      
      final response = await _dio.get(
        '/summaries/',
        options: Options(
          headers: {
            'Authorization': 'Bearer $token',
            'Content-Type': 'application/json',
          },
        ),
      );

      if (response.statusCode == 200) {
        final data = response.data;
        print('✅ Summaries récupérés: ${data.length} éléments');
        
        return {
          'success': true,
          'message': 'Données récupérées avec succès',
          'data': data,
        };
      } else {
        print('❌ Erreur API: ${response.statusCode}');
        return {
          'success': false,
          'message': 'Erreur serveur: ${response.statusCode}',
        };
      }
    } catch (e) {
      print('❌ Exception getSummaries: $e');
      
      if (e is DioException) {
        if (e.response?.statusCode == 401) {
          return {
            'success': false,
            'message': 'Token expiré, veuillez vous reconnecter',
          };
        }
        
        final errorMessage = e.response?.data?['detail'] ?? 
                           e.response?.data?.toString() ?? 
                           'Erreur de récupération des données';
        return {
          'success': false,
          'message': errorMessage,
        };
      }
      
      return {
        'success': false,
        'message': 'Erreur inattendue: $e',
      };
    }
  }
}