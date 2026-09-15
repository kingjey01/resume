import 'dart:async';
import 'package:resume_plus_clean/exceptions/api_exception.dart';
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
  /// Retourne null si aucun utilisateur n'est connecté, ou si le serveur a
  /// explicitement rejeté la session (401 → les jetons sont supprimés).
  ///
  /// LÈVE en revanche sur tout autre échec (réseau, timeout, 5xx, parsing) :
  /// ces erreurs ne disent RIEN de la validité de la session. Auparavant on
  /// appelait `logout()` dans ce cas, ce qui effaçait les jetons et
  /// blacklistait le refresh côté serveur — une simple perte de connexion
  /// déconnectait donc définitivement l'utilisateur.
  Future<User?> getCurrentUser() async {
    try {
      final tokens = await _storageService.readTokens();
      if (tokens['access'] == null) return null;

      final userProfile = await _apiService.getUserProfile();

      // Mémoriser le profil : il permet de rouvrir l'espace personnel hors-ligne
      // (cf. AuthNotifier._resolveCurrentUser).
      await _storageService.cacheUserProfile(userProfile);

      return User.fromJson(userProfile);
    } on DioException catch (e) {
      // Seul un 401 prouve que la session est morte.
      if (e.response?.statusCode == 401) {
        await _apiService.logout();
        return null;
      }
      rethrow;
    } on ApiException catch (e) {
      // Le token a été rejeté puis le refresh a échoué → session réellement
      // perdue (les jetons ont déjà été nettoyés par ApiService).
      if (e.type == ApiExceptionType.unauthorized) return null;
      rethrow;
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
      // Vider les caches persistants de l'utilisateur (profil, achats,
      // recherches) pour que l'utilisateur suivant ne voie PAS ses données.
      await _storageService.clearAllCache();
      // Réinitialiser le flag d'onboarding général : sinon, un nouveau compte
      // étudiant créé après ce logout sauterait l'onboarding général (le flag
      // « déjà vu » du compte précédent reste vrai) et irait droit à l'accueil.
      await _storageService.resetGeneralOnboarding();
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
