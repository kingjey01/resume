import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter/services.dart';
import 'notification_service.dart';
import 'api_service.dart';

/// Service de gestion du badge sur l'icône de l'application.
///
/// Utilise MethodChannel pour communiquer avec le code natif
/// Android (ShortcutBadger) et iOS (UIApplication).
///
/// Synchronise le badge avec le compteur de notifications non lues.
class BadgeService with WidgetsBindingObserver {
  static final BadgeService _instance = BadgeService._internal();
  factory BadgeService() => _instance;
  BadgeService._internal();

  static const _channel = MethodChannel('resume_plus/badge');
  bool _initialized = false;

  /// Initialise le service (canal natif + écoute du compteur + lifecycle).
  ///
  /// Peut être appelé avant l'authentification : la synchronisation API
  /// échouera silencieusement (pas de JWT) mais sera retentée après le
  /// login via [refresh()] et à chaque retour au premier plan.
  Future<void> initialize() async {
    if (_initialized) return;

    try {
      final supported = await _channel.invokeMethod<bool>('isSupported') ?? false;
      if (!supported) {
        print('⚠️ BadgeService: non supporté');
        return;
      }

      // Re-synchroniser le badge à chaque retour au premier plan
      WidgetsBinding.instance.addObserver(this);

      // Brancher le badge sur le compteur (lecture, polling, FCM)
      NotificationService().addCountListener(_onCountChanged);

      _initialized = true;
      print('✅ BadgeService: initialisé');

      // Première synchronisation (échoue silencieusement si non authentifié)
      await refresh();
    } catch (e) {
      print('⚠️ BadgeService: erreur init: $e');
    }
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      // L'app revient au premier plan → re-synchroniser le badge
      refresh();
    }
  }

  /// Re-synchronise le badge depuis l'API (à appeler après login et
  /// à chaque retour au premier plan).
  Future<void> refresh() async {
    try {
      final count = await ApiService().getUnreadNotificationCount();
      await _setBadge(count);
    } catch (e) {
      print('⚠️ BadgeService: erreur synchro: $e');
    }
  }

  Future<void> _setBadge(int count) async {
    try {
      await _channel.invokeMethod('setBadge', {'count': count});
    } catch (e) {
      print('⚠️ BadgeService: erreur setBadge: $e');
    }
  }

  void _onCountChanged(int newCount) => _setBadge(newCount);

  /// Efface le badge de l'icône (à appeler au logout).
  Future<void> clearBadge() async {
    try {
      await _channel.invokeMethod('removeBadge');
    } catch (e) {
      print('⚠️ BadgeService: erreur clear: $e');
    }
  }
}
