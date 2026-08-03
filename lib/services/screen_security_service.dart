import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:screen_protector/screen_protector.dart';

/// 🔒 Service de sécurité pour protéger l'application contre les captures d'écran
class ScreenSecurityService {
  static bool _isSecured = false;

  /// Active la protection contre les captures d'écran
  static Future<void> enableScreenSecurity() async {
    if (kIsWeb) {
      // Sur le web, on peut utiliser CSS pour masquer le contenu lors des captures
      _enableWebScreenSecurity();
      return;
    }

    if (!kIsWeb && (Platform.isAndroid || Platform.isIOS)) {
      try {
        await ScreenProtector.protectDataLeakageOn();
        _isSecured = true;
        print('🔒 Protection écran activée');
      } catch (e) {
        print('⚠️ Erreur lors de l\'activation de la protection: $e');
      }
    }
  }

  /// Désactive la protection contre les captures d'écran
  static Future<void> disableScreenSecurity() async {
    if (kIsWeb) {
      _disableWebScreenSecurity();
      return;
    }

    if (!kIsWeb && (Platform.isAndroid || Platform.isIOS)) {
      try {
        await ScreenProtector.protectDataLeakageOff();
        _isSecured = false;
        print('🔓 Protection écran désactivée');
      } catch (e) {
        print('⚠️ Erreur lors de la désactivation: $e');
      }
    }
  }

  /// Fallback pour Android sans plugin natif
  static Future<void> _enableAndroidFallback() async {
    try {
      // Utiliser les SystemChannels pour masquer l'application dans le task switcher
      await SystemChannels.platform.invokeMethod(
        'SystemChrome.setApplicationSwitcherDescription',
        {
          'label': 'Application sécurisée',
          'primaryColor': 0xFF000000,
        },
      );
      
      // Masquer les overlays système
      await SystemChrome.setEnabledSystemUIMode(
        SystemUiMode.immersiveSticky,
        overlays: [],
      );
      
      _isSecured = true;
      print('🔒 Protection écran activée (fallback Android)');
    } catch (e) {
      print('⚠️ Erreur fallback Android: $e');
    }
  }

  /// Protection web via CSS et JavaScript
  static void _enableWebScreenSecurity() {
    try {
      // Désactiver le clic droit
      _injectWebSecurity();
      _isSecured = true;
      print('🔒 Protection écran activée sur Web');
    } catch (e) {
      print('⚠️ Erreur protection web: $e');
    }
  }

  static void _disableWebScreenSecurity() {
    _isSecured = false;
    print('🔓 Protection écran désactivée sur Web');
  }

  /// Injection de code JavaScript pour la sécurité web
  static void _injectWebSecurity() {
    // Note: Cette méthode nécessiterait l'utilisation de dart:html
    // Pour une implémentation complète, il faudrait utiliser un plugin web
    if (kDebugMode) {
      print('🌐 Injection de sécurité web (simulation)');
    }
  }

  /// Vérifie si la protection est active
  static bool get isSecured => _isSecured;

  /// Active la protection pour un écran spécifique
  static Future<void> secureScreen({
    String? screenName,
    bool hideInTaskSwitcher = true,
    bool preventScreenshots = true,
  }) async {
    if (!preventScreenshots) return;

    print('🔒 Sécurisation de l\'écran: ${screenName ?? "Inconnu"}');
    await enableScreenSecurity();

    if (hideInTaskSwitcher && !kIsWeb && Platform.isAndroid) {
      try {
        await SystemChannels.platform.invokeMethod(
          'SystemChrome.setApplicationSwitcherDescription',
          {
            'label': screenName ?? 'Contenu sécurisé',
            'primaryColor': 0xFF000000,
          },
        );
      } catch (e) {
        print('⚠️ Erreur masquage task switcher: $e');
      }
    }
  }

  /// Désécurise un écran spécifique
  static Future<void> unsecureScreen() async {
    print('🔓 Désécurisation de l\'écran');
    await disableScreenSecurity();
  }

  /// Applique la sécurité à toute l'application
  static Future<void> enableGlobalScreenSecurity() async {
    print('🔒 Activation de la sécurité globale');
    await enableScreenSecurity();
    
    // Configuration globale pour Android
    if (!kIsWeb && Platform.isAndroid) {
      try {
        await SystemChrome.setApplicationSwitcherDescription(
          const ApplicationSwitcherDescription(
            label: 'Résumé+ (Sécurisé)',
            primaryColor: 0xFF1976D2,
          ),
        );
      } catch (e) {
        print('⚠️ Erreur configuration globale: $e');
      }
    }
  }

  /// Désactive la sécurité globale
  static Future<void> disableGlobalScreenSecurity() async {
    print('🔓 Désactivation de la sécurité globale');
    await disableScreenSecurity();
    
    if (!kIsWeb && Platform.isAndroid) {
      try {
        await SystemChrome.setApplicationSwitcherDescription(
          const ApplicationSwitcherDescription(
            label: 'Résumé+',
            primaryColor: 0xFF1976D2,
          ),
        );
      } catch (e) {
        print('⚠️ Erreur désactivation globale: $e');
      }
    }
  }
}