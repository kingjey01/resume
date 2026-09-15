import 'package:resume_plus_clean/exceptions/api_exception.dart';
import 'package:resume_plus_clean/services/api_service.dart';
import 'package:resume_plus_clean/services/storage_service.dart';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:math';

/// Résultat de la vérification de l'état de l'app au démarrage
enum AppStartState {
  /// Token valide, aller directement à l'espace personnel
  loggedIn,
  /// Device enregistré, refresh token valide, session restaurée
  sessionRestored,
  /// Device enregistré mais session expirée, re-authentification nécessaire via OTP auto
  deviceKnownNeedsAuth,
  /// Nouvel appareil, afficher onboarding puis saisie numéro
  newDevice,
}

class AutoLoginService {
  static const String _deviceIdKey = 'app_device_unique_id';

  /// Génère ou récupère un identifiant unique pour cet appareil
  static Future<String> getOrCreateDeviceId() async {
    final prefs = await SharedPreferences.getInstance();
    String? deviceId = prefs.getString(_deviceIdKey);
    
    if (deviceId == null || deviceId.isEmpty) {
      // Générer un ID unique basé sur le timestamp + random
      final random = Random.secure();
      final values = List<int>.generate(16, (_) => random.nextInt(256));
      deviceId = 'DEV_${DateTime.now().millisecondsSinceEpoch}_${values.map((b) => b.toRadixString(16).padLeft(2, '0')).join()}';
      await prefs.setString(_deviceIdKey, deviceId);
      print('📱 Nouveau device ID généré: $deviceId');
    }
    
    return deviceId;
  }

  /// Détermine l'état de l'application au démarrage
  static Future<AppStartState> determineStartState() async {
    final storageService = StorageService();
    final apiService = ApiService();

    try {
      // 1. La session locale : la présence d'un refresh token prouve qu'un
      //    utilisateur s'est déjà authentifié SUR CET APPAREIL. On ne se fie
      //    pas au seul enregistrement « device » : il n'était écrit par
      //    aucune version de l'app (registerDevice n'était jamais appelé), et
      //    s'en servir comme critère renvoyait à l'onboarding des utilisateurs
      //    dont la session était pourtant parfaitement restaurable.
      final refreshTokenStr = await storageService.refreshToken;
      final isRegistered = await storageService.isDeviceRegistered();
      final deviceKnown = isRegistered || refreshTokenStr != null;

      // 2. Un access token est présent : on tente de valider la session
      final accessToken = await storageService.accessToken;
      if (accessToken != null) {
        await apiService.initializeTokens();
        try {
          await apiService.getUserProfile();
          print('✅ Token d\'accès valide → espace personnel');
          return AppStartState.loggedIn;
        } on ApiException catch (e) {
          // Seul un 401 prouve que la session est morte. Toute autre erreur
          // (réseau, timeout, 5xx) n'est PAS une déconnexion : la session
          // locale reste valide, on ouvre l'espace personnel plutôt que de
          // renvoyer l'utilisateur vers téléphone + OTP.
          if (e.type != ApiExceptionType.unauthorized) {
            print('📴 Serveur injoignable (${e.type}) → session locale conservée');
            return AppStartState.loggedIn;
          }
          print('⚠️ Session rejetée (401), tentative de refresh...');
        } catch (_) {
          print('📴 Vérification impossible → session locale conservée');
          return AppStartState.loggedIn;
        }
      }

      // 3. Aucune session locale exploitable et appareil inconnu → onboarding
      if (!deviceKnown) {
        print('📱 Nouvel appareil → onboarding');
        return AppStartState.newDevice;
      }

      // 4. Appareil connu : restaurer la session avec le refresh token
      if (refreshTokenStr != null) {
        try {
          final newAccessToken = await apiService.refreshToken();
          if (newAccessToken != null) {
            print('🔄 Session restaurée via refresh token');
            return AppStartState.sessionRestored;
          }
        } catch (e) {
          print('⚠️ Refresh token expiré: $e');
        }
      }

      // 5. Device connu mais pas de session valide → besoin re-auth OTP
      print('📱 Device connu mais session expirée → re-auth nécessaire');
      return AppStartState.deviceKnownNeedsAuth;

    } catch (e) {
      print('❌ Erreur détermination état: $e');
      // En cas d'erreur, vérifier si device enregistré
      final isRegistered = await storageService.isDeviceRegistered();
      return isRegistered ? AppStartState.deviceKnownNeedsAuth : AppStartState.newDevice;
    }
  }

  /// Enregistre l'appareil après une authentification OTP réussie
  static Future<void> registerDevice({required String phone}) async {
    final storageService = StorageService();
    final deviceId = await getOrCreateDeviceId();
    
    await storageService.saveDeviceRegistration(phone: phone, deviceId: deviceId);
    await storageService.setOnboardingComplete();
    
    print('✅ Appareil enregistré: phone=$phone, deviceId=$deviceId');
  }

  /// Récupère le numéro de téléphone enregistré sur cet appareil
  static Future<String?> getRegisteredPhone() async {
    final storageService = StorageService();
    return await storageService.getRegisteredPhone();
  }
}