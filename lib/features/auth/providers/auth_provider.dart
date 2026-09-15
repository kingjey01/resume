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
//
// `valueOrNull` : en chargement ou en erreur, l'utilisateur n'est « pas
// (encore) authentifié » — on ne fait pas planter le build de ses
// consommateurs (contrairement à `value`, qui relance l'erreur).
final isAuthenticatedProvider = Provider<bool>((ref) {
  final authState = ref.watch(authProvider);
  return authState.valueOrNull != null;
});

// Fournisseur utilitaire pour accéder à l'utilisateur actuel
// (null tant que le profil n'est pas connu, plutôt qu'une exception).
final currentUserProvider = Provider<User?>((ref) {
  final authState = ref.watch(authProvider);
  return authState.valueOrNull;
});

// Fournisseur RÉACTIF du rôle (groupe) de l'utilisateur connecté.
//
// ⚠️ Il lit authProvider DIRECTEMENT (pas currentUserProvider) : à chaque
// rafraîchissement, le notifier remplace l'état par un NOUVEL objet → les
// consommateurs sont prévenus même si seul `groupe` a changé. Le `==` du
// modèle User ne comparant que l'`id`, un Provider dérivé qui renverrait un
// User « égal » (même id) ne notifierait pas ses dépendants.
//
// ⚠️ Renvoie `null` tant que le rôle n'est PAS CONNU : chargement initial du
// profil (AsyncValue.loading), erreur réseau, ou utilisateur déconnecté.
// Ne JAMAIS traduire ce `null` par « ETUDIANT » : un consommateur ne doit pas
// confondre « pas encore chargé » avec « étudiant ». C'est ce qui faisait
// réapparaître la bannière « devenir CP » et disparaître le bouton « + » chez
// un CP déjà validé jusqu'au prochain rafraîchissement manuel.
final currentUserRoleProvider = Provider<String?>((ref) {
  // `valueOrNull` (et non `value`) : un état en ERREUR ne doit pas faire
  // planter le build des consommateurs, il vaut « rôle inconnu » → null.
  return ref.watch(authProvider).valueOrNull?.groupe;
});

/// Compteur incrémenté à chaque login pour forcer le rafraîchissement des données
final userSessionVersionProvider = StateProvider<int>((ref) => 0);

class AuthNotifier extends StateNotifier<AsyncValue<User?>> {
  final AuthRepository _authRepository;
  final StorageService _storageService;
  final ApiService _apiService;
  
  // Pour gérer les accès concurrents lors du rafraîchissement du token
  bool _isRefreshingToken = false;

  // Garde anti-concurrence du chargement du profil. Volontairement SÉPARÉ de
  // `state.isLoading` : l'état initial est `loading`, donc s'appuyer dessus
  // empêchait le tout premier chargement (cf. _loadCurrentUser).
  bool _isLoadingUser = false;

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

  /// Résout l'utilisateur courant SANS jamais déconnecter sur un échec non
  /// authentifiant.
  ///
  /// Renvoie `null` uniquement quand la session est réellement absente ou
  /// rejetée par le serveur (401 → le repository a déjà nettoyé les jetons).
  /// Sur une panne réseau, une 5xx ou un timeout, la session reste valide : on
  /// se replie sur le dernier profil mis en cache. C'est ce qui évite qu'une
  /// simple perte de connexion renvoie l'utilisateur vers téléphone + OTP.
  Future<User?> _resolveCurrentUser() async {
    try {
      final user = await _authRepository.getCurrentUser();

      if (user == null) {
        // Plus aucun token, ou session rejetée : on s'assure qu'il ne reste
        // rien de stocké (le repository l'a normalement déjà fait).
        await _authRepository.logout();
      }

      return user;
    } catch (e) {
      debugPrint('⚠️ [Auth] Profil injoignable ($e) — repli sur le profil en cache');

      final cached = await _storageService.getCachedUserProfile();
      if (cached != null) {
        try {
          return User.fromJson(cached);
        } catch (parseError) {
          debugPrint('⚠️ [Auth] Profil en cache illisible : $parseError');
        }
      }

      return null;
    }
  }

  Future<void> _loadCurrentUser() async {
    // Garde anti-concurrence sur un booléen DÉDIÉ, et non sur `state.isLoading`.
    // L'état initial de ce notifier EST `loading` : l'ancien
    // `if (state.isLoading) return;` renvoyait donc immédiatement au démarrage
    // et le profil n'était jamais restauré depuis le stockage — l'app restait
    // bloquée en `loading` jusqu'à un rafraîchissement manuel.
    if (_isLoadingUser) return;
    _isLoadingUser = true;

    state = const AsyncValue.loading();

    try {
      // Ne lève jamais : renvoie null si la session est réellement perdue.
      final user = await _resolveCurrentUser();
      state = AsyncValue.data(user);
    } finally {
      _isLoadingUser = false;
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

  Future<void> refreshUser() async {
    // Passe par _resolveCurrentUser : un échec réseau ne met plus l'état en
    // erreur (ce qui équivalait à « non authentifié » chez les consommateurs,
    // juste après l'OTP notamment) — on retombe sur le profil en cache.
    state = AsyncValue.data(await _resolveCurrentUser());
  }

  /// Rafraîchit l'utilisateur depuis le backend SANS écran de chargement et
  /// SANS déconnecter en cas d'échec réseau : l'état précédent est conservé.
  ///
  /// C'est la brique du « rafraîchissement global » : après acceptation d'une
  /// demande CP, elle recharge le profil → `groupe`/`cp_onboarding_completed`
  /// sont à jour → les écrans branchés sur [authProvider] se reconstruisent
  /// (nombre d'onglets, bouton « + », etc.) sans logout ni redémarrage.
  ///
  /// Renvoie true si le profil a bien été rechargé.
  Future<bool> refreshCurrentUser() async {
    // _resolveCurrentUser ne lève jamais et retombe sur le profil en cache :
    // hors-ligne, l'état précédent est donc conservé plutôt que vidé.
    final user = await _resolveCurrentUser();
    if (user == null) return false;
    state = AsyncValue.data(user);
    return true;
  }
}
