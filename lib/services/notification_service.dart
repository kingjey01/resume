import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:resume_plus_clean/services/api_service.dart';
import 'package:resume_plus_clean/utils/logger.dart';

/// Polls the backend periodically to update the unread notification count
/// and triggers callbacks so the UI can react (badge update, in-app banner, etc.).
/// FCM push can be layered on top without changing this service.
class NotificationService {
  static final NotificationService _instance = NotificationService._internal();
  factory NotificationService() => _instance;
  NotificationService._internal();

  final ApiService _api = ApiService();

  Timer? _pollingTimer;
  int _unreadCount = 0;
  bool _isRunning = false;

  // Listeners notified when the unread count changes
  final List<void Function(int count)> _countListeners = [];
  // Listeners notified when new notifications arrive (delta > 0)
  final List<void Function()> _newNotifListeners = [];

  int get unreadCount => _unreadCount;

  // ─── Lifecycle ───────────────────────────────────────────

  void startPolling({Duration interval = const Duration(seconds: 30)}) {
    if (_isRunning) return;
    _isRunning = true;
    _poll(); // immediate first check
    _pollingTimer = Timer.periodic(interval, (_) => _poll());
    AppLogger.info('🔔 NotificationService: polling démarré (${interval.inSeconds}s)');
  }

  void stopPolling() {
    _pollingTimer?.cancel();
    _pollingTimer = null;
    _isRunning = false;
    AppLogger.info('🔕 NotificationService: polling arrêté');
  }

  void dispose() {
    stopPolling();
    _countListeners.clear();
    _newNotifListeners.clear();
  }

  // ─── Listeners ───────────────────────────────────────────

  void addCountListener(void Function(int) listener) {
    _countListeners.add(listener);
  }

  void removeCountListener(void Function(int) listener) {
    _countListeners.remove(listener);
  }

  void addNewNotifListener(void Function() listener) {
    _newNotifListeners.add(listener);
  }

  void removeNewNotifListener(void Function() listener) {
    _newNotifListeners.remove(listener);
  }

  // ─── Manual refresh ──────────────────────────────────────

  Future<void> refresh() => _poll();

  Future<int> fetchUnreadCount() async {
    final count = await _api.getUnreadNotificationCount();
    _updateCount(count);
    return count;
  }

  /// Applique un compteur reçu directement depuis le payload FCM
  /// (data['badge_count']), pour une mise à jour immédiate du badge
  /// sans attendre le prochain polling.
  void setUnreadCount(int count) {
    _updateCount(count);
  }

  // ─── Private ─────────────────────────────────────────────

  Future<void> _poll() async {
    try {
      final count = await _api.getUnreadNotificationCount();
      _updateCount(count);
    } catch (e) {
      if (kDebugMode) print('⚠️ NotificationService poll error: $e');
    }
  }

  void _updateCount(int newCount) {
    final hadNew = newCount > _unreadCount;
    _unreadCount = newCount;
    for (final l in List.of(_countListeners)) {
      l(newCount);
    }
    if (hadNew) {
      for (final l in List.of(_newNotifListeners)) {
        l();
      }
    }
  }

  // ─── After read ──────────────────────────────────────────

  void decrementUnread({int by = 1}) {
    final updated = (_unreadCount - by).clamp(0, _unreadCount);
    _updateCount(updated);
  }

  void resetUnread() => _updateCount(0);
}
