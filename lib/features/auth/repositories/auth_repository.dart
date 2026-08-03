import 'dart:async';
import 'package:resume_plus_clean/models/user.dart';
import 'package:resume_plus_clean/services/api_service.dart';
import 'package:resume_plus_clean/services/storage_service.dart';
import 'package:dio/dio.dart';

class AuthRepository {
  final ApiService _apiService;
  final StorageService _storageService;

  AuthRepository({
    ApiService? apiService,
    StorageService? storageService,
  }) : _apiService = apiService ?? ApiService(),
       _storageService = storageService ?? StorageService();

  /// Connecte l'utilisateur avec un nom d'utilisateur et un mot de passe
  /// 
  /// Lance une exception si la connexion échoue
  Future<User> login(String username, String password) async {
    try {
      final response = await _apiService.login(username, password);
      
      // Les tokens sont déjà enregistrés dans l'ApiService
      // Récupérer les informations de l'utilisateur
      final userData = response['user'] as Map<String, dynamic>?;
      
      if (userData == null) {
        // Si le backend ne renvoie pas les infos utilisateur dans la réponse de connexion,
        // on les récupère via une requête séparée
        final userProfile = await _apiService.getUserProfile();
        return User.fromJson(userProfile);
      }
      
      return User.fromJson(userData);
    } on DioException catch (e) {
      // L'erreur est déjà gérée par l'ApiService, on la propage simplement
      rethrow;
    } catch (e) {
      throw Exception('Échec de la connexion: $e');
    }
  }

  /// Récupère l'utilisateur actuellement connecté
  /// 
  /// Retourne null si aucun utilisateur n'est connecté
  Future<User?> getCurrentUser() async {
    try {
      final tokens = await _storageService.readTokens();
      if (tokens['access'] == null) return null;
      
      final userProfile = await _apiService.getUserProfile();
      return User.fromJson(userProfile);
    } on DioException catch (e) {
      // Si le token est invalide ou expiré, on déconnecte l'utilisateur
      if (e.response?.statusCode == 401) {
        await _apiService.logout();
      }
      return null;
    } catch (e) {
      // En cas d'autre erreur, on déconnecte aussi pour être sûr
      await _apiService.logout();
      return null;
    }
  }

  Future<User> register(String username, String email, String password, {
    String? firstName,
    String? lastName,
    int? universiteId,
    int? promotionId,
    int? filiereId,
    String groupe = 'ETUDIANT',
  }) async {
    try {
      final registrationData = {
        'username': username,
        'email': email,
        'password': password,
        'first_name': firstName,
        'last_name': lastName,
        'universite_id': universiteId,
        'promotion_id': promotionId,
        'filiere_id': filiereId,
        'groupe': groupe,
      };

      await _apiService.register(registrationData);
      
      // Auto-login after registration
      return await login(email, password);
    } catch (e) {
      throw Exception('Registration failed: $e');
    }
  }

  /// Déconnecte l'utilisateur et supprime les tokens
  /// 
  /// Ne lance jamais d'exception
  Future<void> logout() async {
    try {
      await _apiService.logout();
    } catch (e) {
      // En cas d'erreur, on continue quand même la déconnexion locale
    } finally {
      // On s'assure que les tokens sont bien supprimés localement
      await _storageService.deleteTokens();
    }
  }

  Future<bool> isLoggedIn() async {
    final token = await _storageService.readToken();
    return token != null;
  }

  Future<User> updateProfile(Map<String, dynamic> profileData) async {
    try {
      final response = await _apiService.put('/auth/profile/', data: profileData);
      return User.fromJson(response.data);
    } catch (e) {
      throw Exception('Profile update failed: $e');
    }
  }

  Future<void> changePassword(String currentPassword, String newPassword) async {
    try {
      await _apiService.post('/auth/change-password/', data: {
        'current_password': currentPassword,
        'new_password': newPassword,
      });
    } catch (e) {
      throw Exception('Password change failed: $e');
    }
  }
}
