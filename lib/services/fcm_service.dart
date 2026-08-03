import 'dart:io';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart' show Color;
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:resume_plus_clean/services/api_service.dart';
import 'package:resume_plus_clean/services/notification_service.dart';

// ─── Background handler (top-level, hors classe) ─────────────────────────────
// Appelé dans un isolate séparé quand app est en background ou terminée.
// Firebase affiche automatiquement la notification (champ `notification` présent).
// Ce handler traite uniquement les données supplémentaires.
@pragma('vm:entry-point')
Future<void> _firebaseBackgroundHandler(RemoteMessage message) async {
  // Firebase SDK affiche automatiquement la notification en background/killed.
  // Pas besoin de montrer une notification locale ici.
  debugPrint('📨 [FCM BG] Message reçu en background: ${message.messageId}');
}

// ─── FcmService ───────────────────────────────────────────────────────────────

class FcmService {
  static final FcmService _instance = FcmService._internal();
  factory FcmService() => _instance;
  FcmService._internal();

  final FirebaseMessaging _messaging = FirebaseMessaging.instance;
  final ApiService _api = ApiService();

  String? _currentToken;

  // Canal de notifications locales pour foreground
  static const AndroidNotificationChannel _channel = AndroidNotificationChannel(
    'resume_plus_notifications',
    'Résumé+ Notifications',
    description: 'Notifications pour les nouveaux résumés et exercices',
    importance: Importance.high,
    enableVibration: true,
    playSound: true,
  );

  final FlutterLocalNotificationsPlugin _localNotifications =
      FlutterLocalNotificationsPlugin();

  // ─── Init ─────────────────────────────────────────────────────────────────

  /// Initialisation PRE-AUTH : permissions, channels, handlers
  /// NE récupère PAS le token et NE l'envoie PAS au backend
  /// (l'utilisateur n'est pas encore authentifié)
  Future<void> initialize() async {
    // 1. Enregistrer le handler background
    FirebaseMessaging.onBackgroundMessage(_firebaseBackgroundHandler);

    // 2. Demander les permissions
    await _requestPermissions();

    // 3. Configurer les notifications locales (foreground Android)
    await _setupLocalNotifications();

    // 4. Configurer iOS foreground display
    await _messaging.setForegroundNotificationPresentationOptions(
      alert: true,
      badge: true,
      sound: true,
    );

    // 5. Écouter les refreshes de token (pour mise à jour automatique)
    //    Note: l'envoi au backend ne se fera que si l'utilisateur est connecté
    _messaging.onTokenRefresh.listen((newToken) async {
      debugPrint('🔄 [FCM] Token rafraîchi automatiquement');
      _currentToken = newToken;
      // Tenter d'enregistrer (échouera silencieusement si non authentifié)
      await _api.registerFcmToken(newToken, deviceType: _deviceType());
    });

    // 6. Handlers de messages
    _setupMessageHandlers();

    debugPrint('✅ [FCM] Service initialisé (pré-auth)');
  }

  /// À APPELER APRÈS LE LOGIN
  /// Récupère le token actuel et l'envoie au backend avec le user authentifié
  Future<bool> registerCurrentUserToken() async {
    try {
      final token = await _messaging.getToken();
      if (token == null) {
        debugPrint('⚠️ [FCM] Aucun token disponible (permissions refusées?)');
        return false;
      }

      _currentToken = token;
      debugPrint('📱 [FCM] Token récupéré: ...${token.substring(token.length - 10)}');

      // Toujours envoyer au backend après login (FORCE)
      // — pas de check token != _currentToken pour gérer le changement d'user
      final success = await _api.registerFcmToken(token, deviceType: _deviceType());
      if (success) {
        debugPrint('✅ [FCM] Token enregistré pour le user actuel');
      } else {
        debugPrint('❌ [FCM] Échec enregistrement token');
      }
      return success;
    } catch (e) {
      debugPrint('❌ [FCM] Erreur registerCurrentUserToken: $e');
      return false;
    }
  }

  // ─── Permissions ─────────────────────────────────────────────────────────

  Future<bool> _requestPermissions() async {
    final settings = await _messaging.requestPermission(
      alert: true,
      badge: true,
      sound: true,
      provisional: false,
      announcement: false,
      carPlay: false,
      criticalAlert: false,
    );

    final granted = settings.authorizationStatus == AuthorizationStatus.authorized ||
        settings.authorizationStatus == AuthorizationStatus.provisional;

    debugPrint(granted
        ? '✅ [FCM] Permissions accordées'
        : '⚠️ [FCM] Permissions refusées: ${settings.authorizationStatus}');

    return granted;
  }

  // ─── Token ───────────────────────────────────────────────────────────────

  /// @deprecated Utiliser `registerCurrentUserToken()` à la place
  /// Conservé pour compatibilité — force toujours l'envoi au backend
  Future<String?> refreshToken() async {
    try {
      final token = await _messaging.getToken();
      if (token != null) {
        _currentToken = token;
        // FORCE l'envoi (pas de check d'égalité avec _currentToken)
        await _api.registerFcmToken(token, deviceType: _deviceType());
        debugPrint('📱 [FCM] Token enregistré (force): ...${token.substring(token.length - 10)}');
      }
      return token;
    } catch (e) {
      debugPrint('❌ [FCM] Erreur refreshToken: $e');
      return null;
    }
  }

  /// À APPELER AVANT LE LOGOUT (pendant que le JWT est encore valide)
  Future<void> deleteToken() async {
    try {
      // 1. D'abord récupérer le token actuel s'il n'est pas en cache
      final token = _currentToken ?? await _messaging.getToken();
      
      // 2. Désactiver côté backend (pendant que le JWT est encore valide)
      if (token != null) {
        debugPrint('🗑️ [FCM] Désactivation token côté backend: ...${token.substring(token.length - 10)}');
        await _api.unregisterFcmToken(token);
      }
      
      // 3. Supprimer côté Firebase (force la régénération au prochain getToken)
      await _messaging.deleteToken();
      _currentToken = null;
      debugPrint('🗑️ [FCM] Token supprimé localement');
    } catch (e) {
      debugPrint('❌ [FCM] Erreur deleteToken: $e');
    }
  }

  String? get currentToken => _currentToken;

  // ─── Local notifications (foreground Android) ────────────────────────────

  Future<void> _setupLocalNotifications() async {
    const androidInit = AndroidInitializationSettings('@mipmap/ic_launcher');
    const iosInit = DarwinInitializationSettings(
      requestAlertPermission: false,
      requestBadgePermission: false,
      requestSoundPermission: false,
    );

    await _localNotifications.initialize(
      const InitializationSettings(android: androidInit, iOS: iosInit),
      onDidReceiveNotificationResponse: _onLocalNotificationTap,
    );

    // Créer le canal Android
    final androidPlugin = _localNotifications
        .resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>();
    await androidPlugin?.createNotificationChannel(_channel);
  }

  void _onLocalNotificationTap(NotificationResponse response) {
    debugPrint('🔔 [FCM] Notification locale tapée: ${response.payload}');
    _handleNotificationPayload(response.payload);
  }

  Future<void> _showLocalNotification(RemoteMessage message) async {
    final notification = message.notification;
    if (notification == null) return;

    await _localNotifications.show(
      message.hashCode,
      notification.title,
      notification.body,
      NotificationDetails(
        android: AndroidNotificationDetails(
          _channel.id,
          _channel.name,
          channelDescription: _channel.description,
          importance: Importance.high,
          priority: Priority.high,
          icon: '@mipmap/ic_launcher',
          color: const Color(0xFF1E3A5F), // Brand color
          largeIcon: const DrawableResourceAndroidBitmap('@mipmap/ic_launcher'),
          playSound: true,
          enableVibration: true,
          styleInformation: BigTextStyleInformation(
            notification.body ?? '',
            htmlFormatBigText: false,
            contentTitle: notification.title,
          ),
        ),
        iOS: const DarwinNotificationDetails(
          presentAlert: true,
          presentBadge: true,
          presentSound: true,
        ),
      ),
      payload: _buildPayload(message.data),
    );
  }

  // ─── Message Handlers ─────────────────────────────────────────────────────

  void _setupMessageHandlers() {
    // Foreground : afficher notification locale + mettre à jour badge
    FirebaseMessaging.onMessage.listen((message) async {
      debugPrint('📩 [FCM FG] Message reçu: ${message.notification?.title}');
      await _showLocalNotification(message);
      // Mettre à jour le badge immédiatement avec le compteur envoyé par le backend
      final badgeCount = int.tryParse(message.data['badge_count'] ?? '');
      if (badgeCount != null) {
        NotificationService().setUnreadCount(badgeCount);
      } else {
        // Fallback : rafraîchir le compteur non lues via polling
        NotificationService().refresh();
      }
    });

    // App en arrière-plan → tap sur notification
    FirebaseMessaging.onMessageOpenedApp.listen((message) {
      debugPrint('🖱️ [FCM BG→FG] Tap sur notification: ${message.data}');
      NotificationService().refresh();
      _handleNotificationPayload(_buildPayload(message.data));
    });

    // App terminée → tap sur notification
    _messaging.getInitialMessage().then((message) {
      if (message != null) {
        debugPrint('🚀 [FCM TERMINATED] App ouverte via notification: ${message.data}');
        NotificationService().refresh();
        _handleNotificationPayload(_buildPayload(message.data));
      }
    });
  }

  // ─── Navigation depuis notification ──────────────────────────────────────

  void _handleNotificationPayload(String? payload) {
    if (payload == null || payload.isEmpty) return;
    // Le payload est formaté : "summary_id:123" ou "course_id:456"
    // La navigation est gérée par le NavigationService ou les routes
    debugPrint('🔀 [FCM] Navigation payload: $payload');
    // TODO: intégrer avec le router de l'app si go_router est utilisé
  }

  String _buildPayload(Map<String, dynamic> data) {
    if (data['summary_id'] != null && data['summary_id'] != '') {
      return 'summary_id:${data['summary_id']}';
    }
    if (data['course_id'] != null && data['course_id'] != '') {
      return 'course_id:${data['course_id']}';
    }
    if (data['user_notification_id'] != null) {
      return 'notification_id:${data['user_notification_id']}';
    }
    return '';
  }

  // ─── Utils ────────────────────────────────────────────────────────────────

  String _deviceType() {
    if (kIsWeb) return 'web';
    if (Platform.isIOS) return 'ios';
    return 'android';
  }
}
