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
}
