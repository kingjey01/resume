import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:resume_plus_clean/services/api_service.dart';

/// 🔥 Provider pour l'ApiService avec gestion hybride des tokens
/// Cette instance unique sera utilisée dans toute l'application
final apiServiceProvider = Provider<ApiService>((ref) {
  return ApiService();
});

/// 🔥 Provider pour vérifier l'état de connexion
final authStateProvider = FutureProvider.autoDispose<bool>((ref) async {
  final apiService = ref.read(apiServiceProvider);
  return await apiService.isLoggedIn();
});

/// 🔥 Provider pour les données utilisateur
final userProfileProvider = FutureProvider.autoDispose<Map<String, dynamic>?>((ref) async {
  final apiService = ref.read(apiServiceProvider);
  final isLoggedIn = await apiService.isLoggedIn();
  
  if (!isLoggedIn) {
    return null;
  }
  
  try {
    return await apiService.getUserProfile();
  } catch (e) {
    print('❌ Erreur lors de la récupération du profil: $e');
    return null;
  }
});

/// 🔥 Provider pour la connexion utilisateur
final loginProvider = StateNotifierProvider<LoginNotifier, AsyncValue<bool>>((ref) {
  final apiService = ref.read(apiServiceProvider);
  return LoginNotifier(apiService);
});

class LoginNotifier extends StateNotifier<AsyncValue<bool>> {
  final ApiService _apiService;

  LoginNotifier(this._apiService) : super(const AsyncValue.data(false));

  /// Connecter l'utilisateur
  Future<void> login(String username, String password) async {
    state = const AsyncValue.loading();
    
    try {
      await _apiService.login(username, password);
      state = const AsyncValue.data(true);
      print('✅ Connexion réussie via provider');
    } catch (e) {
      state = AsyncValue.error(e, StackTrace.current);
      print('❌ Erreur de connexion via provider: $e');
      rethrow;
    }
  }

  /// Déconnecter l'utilisateur
  Future<void> logout() async {
    state = const AsyncValue.loading();
    
    try {
      await _apiService.logout();
      state = const AsyncValue.data(false);
      print('✅ Déconnexion réussie via provider');
    } catch (e) {
      state = AsyncValue.error(e, StackTrace.current);
      print('❌ Erreur de déconnexion via provider: $e');
    }
  }

  /// Vérifier l'état de connexion
  Future<void> checkAuthState() async {
    try {
      final isLoggedIn = await _apiService.isLoggedIn();
      state = AsyncValue.data(isLoggedIn);
    } catch (e) {
      state = AsyncValue.error(e, StackTrace.current);
    }
  }
}