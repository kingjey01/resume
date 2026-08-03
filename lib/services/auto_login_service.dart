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
      // 1. Vérifier si l'appareil est enregistré (phone + deviceId sauvegardés)
      final isRegistered = await storageService.isDeviceRegistered();

      // 2. Vérifier si on a un access token
      final accessToken = await storageService.accessToken;
      if (accessToken != null) {
        await apiService.initializeTokens();
        // Valider le token en appelant le serveur
        try {
          await apiService.getUserProfile();
          print('✅ Token d\'accès valide → espace personnel');
          return AppStartState.loggedIn;
        } catch (_) {
          print('⚠️ Access token expiré, tentative de refresh...');
        }
      }

      // 3. Si pas enregistré → nouvel appareil
      if (!isRegistered) {
        print('📱 Nouvel appareil → onboarding');
        return AppStartState.newDevice;
      }

      // 4. L'appareil est enregistré, essayer de restaurer la session avec le refresh token
      final refreshTokenStr = await storageService.refreshToken;
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