import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:resume_plus_clean/features/auth/repositories/auth_repository.dart';
import 'package:resume_plus_clean/models/user.dart';
import 'package:resume_plus_clean/services/storage_service.dart';
import 'package:resume_plus_clean/services/api_service.dart';
import 'package:resume_plus_clean/services/fcm_service.dart';
import 'package:resume_plus_clean/services/badge_service.dart';

// Fournisseur pour le repository d'authentification
final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepository();
});

// Fournisseur pour le service de stockage
final storageServiceProvider = Provider<StorageService>((ref) {
  return StorageService();
});

// Fournisseur pour le service API
final apiServiceProvider = Provider<ApiService>((ref) {
  return ApiService();
});

// Fournisseur pour le notifier d'authentification
final authProvider = StateNotifierProvider<AuthNotifier, AsyncValue<User?>>((ref) {
  final authRepository = ref.watch(authRepositoryProvider);
  final storageService = ref.watch(storageServiceProvider);
  final apiService = ref.watch(apiServiceProvider);
  
  return AuthNotifier(authRepository, storageService, apiService);
});

// Fournisseur utilitaire pour vérifier si l'utilisateur est connecté
final isAuthenticatedProvider = Provider<bool>((ref) {
  final authState = ref.watch(authProvider);
  return authState.value != null;
});

// Fournisseur utilitaire pour accéder à l'utilisateur actuel
final currentUserProvider = Provider<User?>((ref) {
  final authState = ref.watch(authProvider);
  return authState.value;
});

/// Compteur incrémenté à chaque login pour forcer le rafraîchissement des données
final userSessionVersionProvider = StateProvider<int>((ref) => 0);

class AuthNotifier extends StateNotifier<AsyncValue<User?>> {
  final AuthRepository _authRepository;
  final StorageService _storageService;
  final ApiService _apiService;
  
  // Pour gérer les accès concurrents lors du rafraîchissement du token
  bool _isRefreshingToken = false;
  
  AuthNotifier(
    this._authRepository,
    this._storageService,
    this._apiService,
  ) : super(const AsyncValue.loading()) {
    _init();
  }
  
  Future<void> _init() async {
    // Vérifier si un token existe déjà
    final tokens = await _storageService.readTokens();
    
    if (tokens['access'] == null) {
      // Pas de token, utilisateur non connecté
      state = const AsyncValue.data(null);
      return;
    }
    
    // Charger l'utilisateur actuel
    await _loadCurrentUser();
  }

  Future<void> _loadCurrentUser() async {
    // Ne pas recharger si déjà en cours de chargement
    if (state.isLoading) return;
    
    state = const AsyncValue.loading();
    
    try {
      final user = await _authRepository.getCurrentUser();
      
      if (user == null) {
        // Si l'utilisateur n'est pas authentifié, on s'assure qu'aucun token n'est stocké
        await _authRepository.logout();
      }
      
      state = AsyncValue.data(user);
    } catch (e, stackTrace) {
      // En cas d'erreur, on déconnecte l'utilisateur pour être sûr
      await _authRepository.logout();
      state = AsyncValue.error(e, stackTrace);
    }
  }

  Future<void> login(String username, String password) async {
    try {
      state = const AsyncValue.loading();
      
      // Appel au repository pour la connexion
      final user = await _authRepository.login(username, password);
      
      // Nettoyer le cache API de l'ancien utilisateur
      _apiService.clearSession();
      // Mettre à jour l'état avec l'utilisateur connecté
      state = AsyncValue.data(user);
      // Enregistrer le token FCM maintenant que l'utilisateur est authentifié
      // AWAIT important : garantir que le token est bien associé au bon user
      if (!kIsWeb) {
        try {
          final success = await FcmService().registerCurrentUserToken();
          debugPrint('🔔 [Auth] FCM token registration: ${success ? "✅ OK" : "❌ FAILED"}');
        } catch (e) {
          debugPrint('⚠️ [Auth] FCM token registration error (non-blocking): $e');
        }
        // Synchroniser le badge d'icône maintenant que le JWT est disponible
        try {
          await BadgeService().refresh();
          debugPrint('🔴 [Auth] Badge d\'icône synchronisé après login');
        } catch (e) {
          debugPrint('⚠️ [Auth] Badge sync error (non-blocking): $e');
        }
      }
    } catch (e, stackTrace) {
      // En cas d'échec, s'assurer que l'état est bien mis à jour
      state = const AsyncValue.data(null);
      
      // Propage l'erreur pour qu'elle puisse être gérée par l'UI
      // (le message d'erreur est déjà affiché par le SnackbarService dans l'ApiService)
      rethrow;
    }
  }

  Future<void> logout() async {
    try {
      // Ne pas afficher l'état de chargement pour éviter les clignotements inutiles
      // lors de la déconnexion
      if (!state.isLoading) {
        state = const AsyncValue.loading();
      }
      
      // Supprimer le token FCM AVANT le logout (pendant que le JWT est encore valide)
      if (!kIsWeb) {
        try {
          await FcmService().deleteToken();
          debugPrint('🔔 [Auth] FCM token deleted before logout');
        } catch (e) {
          debugPrint('⚠️ [Auth] FCM token deletion error: $e');
        }
        // Effacer le badge de l'icône (plus d'utilisateur connecté)
        try {
          await BadgeService().clearBadge();
          debugPrint('🔴 [Auth] Badge d\'icône effacé au logout');
        } catch (e) {
          debugPrint('⚠️ [Auth] Badge clear error (non-blocking): $e');
        }
      }
      
      // Réinitialiser la session ApiService en mémoire (jetons et caches)
      _apiService.clearSession();
      
      // Appeler la méthode de déconnexion du repository
      await _authRepository.logout();
      
      // Mettre à jour l'état avec un utilisateur null (non connecté)
      state = const AsyncValue.data(null);
    } catch (e, stackTrace) {
      // S'assurer de réinitialiser la session même en cas d'erreur
      _apiService.clearSession();
      
      // En cas d'erreur, forcer la déconnexion locale de toute façon
      await _authRepository.logout();
      state = const AsyncValue.data(null);
      
      // Logger l'erreur mais ne pas la propager pour ne pas bloquer l'utilisateur
      debugPrint('Erreur lors de la déconnexion: $e\n$stackTrace');
    }
  }

  Future<void> register(String username, String email, String password, {
    String? firstName,
    String? lastName,
    int? universiteId,
    int? promotionId,
    int? filiereId,
  }) async {
    try {
      state = const AsyncValue.loading();
      
      // Appeler la méthode d'inscription du repository avec les paramètres supplémentaires
      final user = await _authRepository.register(
        username,
        email,
        password,
        firstName: firstName,
        lastName: lastName,
        universiteId: universiteId,
        promotionId: promotionId,
        filiereId: filiereId,
      );
      
      // Mettre à jour l'état avec l'utilisateur connecté
      state = AsyncValue.data(user);
      // Enregistrer le token FCM après inscription (auto-login) — AWAIT
      if (!kIsWeb) {
        try {
          final success = await FcmService().registerCurrentUserToken();
          debugPrint('🔔 [Auth/Register] FCM token registration: ${success ? "✅ OK" : "❌ FAILED"}');
        } catch (e) {
          debugPrint('⚠️ [Auth/Register] FCM token registration error: $e');
        }
        // Synchroniser le badge d'icône après inscription
        try {
          await BadgeService().refresh();
          debugPrint('🔴 [Auth/Register] Badge d\'icône synchronisé');
        } catch (e) {
          debugPrint('⚠️ [Auth/Register] Badge sync error (non-blocking): $e');
        }
      }
    } catch (e, stackTrace) {
      // En cas d'échec, s'assurer que l'état est bien mis à jour
      state = const AsyncValue.data(null);
      
      // Propage l'erreur pour qu'elle puisse être gérée par l'UI
      rethrow;
    }
  }

  Future<void> refreshUser() async {
    try {
      final user = await _authRepository.getCurrentUser();
      state = AsyncValue.data(user);
    } catch (e) {
      state = AsyncValue.error(e, StackTrace.current);
    }
  }
}
