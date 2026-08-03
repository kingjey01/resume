import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:resume_plus_clean/models/app_notification.dart';
import 'package:resume_plus_clean/services/api_service.dart';
import 'package:resume_plus_clean/services/notification_service.dart';

// ─── Unread count (live, updated by NotificationService) ────────────────────

class UnreadCountNotifier extends StateNotifier<int> {
  UnreadCountNotifier() : super(0) {
    _init();
  }

  final NotificationService _service = NotificationService();
  late final void Function(int) _listener;

  void _init() {
    _listener = (count) {
      if (mounted) state = count;
    };
    _service.addCountListener(_listener);
    // fetch immediately
    _service.fetchUnreadCount();
  }

  void refresh() => _service.refresh();

  @override
  void dispose() {
    _service.removeCountListener(_listener);
    super.dispose();
  }
}

final unreadCountProvider = StateNotifierProvider<UnreadCountNotifier, int>(
  (_) => UnreadCountNotifier(),
);

// ─── Notification list state ─────────────────────────────────────────────────

class NotificationsState {
  final List<UserNotification> items;
  final bool isLoading;
  final bool isLoadingMore;
  final String? error;
  final int currentPage;
  final int totalPages;
  final int unreadCount;
  final String search;
  final String typeFilter;
  final bool unreadOnly;

  const NotificationsState({
    this.items = const [],
    this.isLoading = false,
    this.isLoadingMore = false,
    this.error,
    this.currentPage = 1,
    this.totalPages = 1,
    this.unreadCount = 0,
    this.search = '',
    this.typeFilter = '',
    this.unreadOnly = false,
  });

  bool get hasMore => currentPage < totalPages;

  NotificationsState copyWith({
    List<UserNotification>? items,
    bool? isLoading,
    bool? isLoadingMore,
    String? error,
    int? currentPage,
    int? totalPages,
    int? unreadCount,
    String? search,
    String? typeFilter,
    bool? unreadOnly,
    bool clearError = false,
  }) {
    return NotificationsState(
      items: items ?? this.items,
      isLoading: isLoading ?? this.isLoading,
      isLoadingMore: isLoadingMore ?? this.isLoadingMore,
      error: clearError ? null : (error ?? this.error),
      currentPage: currentPage ?? this.currentPage,
      totalPages: totalPages ?? this.totalPages,
      unreadCount: unreadCount ?? this.unreadCount,
      search: search ?? this.search,
      typeFilter: typeFilter ?? this.typeFilter,
      unreadOnly: unreadOnly ?? this.unreadOnly,
    );
  }
}

class NotificationsNotifier extends StateNotifier<NotificationsState> {
  NotificationsNotifier() : super(const NotificationsState());

  final ApiService _api = ApiService();

  Future<void> load({bool refresh = false}) async {
    if (state.isLoading) return;

    final page = refresh ? 1 : state.currentPage;

    state = state.copyWith(
      isLoading: refresh || page == 1,
      isLoadingMore: !refresh && page > 1,
      clearError: true,
    );

    try {
      final data = await _api.getNotifications(
        page: page,
        search: state.search,
        type: state.typeFilter,
        unreadOnly: state.unreadOnly,
      );
      final parsed = NotificationsPage.fromJson(data);

      state = state.copyWith(
        items: refresh || page == 1 ? parsed.results : [...state.items, ...parsed.results],
        currentPage: parsed.page,
        totalPages: parsed.totalPages,
        unreadCount: parsed.unreadCount,
        isLoading: false,
        isLoadingMore: false,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        isLoadingMore: false,
        error: 'Erreur de chargement des notifications',
      );
    }
  }

  Future<void> loadMore() async {
    if (state.isLoadingMore || !state.hasMore) return;
    state = state.copyWith(currentPage: state.currentPage + 1);
    await load();
  }

  Future<void> refresh() => load(refresh: true);

  void setSearch(String q) {
    state = state.copyWith(search: q, currentPage: 1);
    load(refresh: true);
  }

  void setTypeFilter(String type) {
    state = state.copyWith(typeFilter: type, currentPage: 1);
    load(refresh: true);
  }

  void toggleUnreadOnly() {
    state = state.copyWith(unreadOnly: !state.unreadOnly, currentPage: 1);
    load(refresh: true);
  }

  Future<void> markRead(int userNotificationId) async {
    await _api.markNotificationRead(userNotificationId);
    state = state.copyWith(
      items: state.items.map((n) {
        if (n.id == userNotificationId) return n.copyWith(isRead: true);
        return n;
      }).toList(),
      unreadCount: (state.unreadCount - 1).clamp(0, state.unreadCount),
    );
    NotificationService().decrementUnread();
  }

  Future<void> markAllRead() async {
    await _api.markAllNotificationsRead();
    state = state.copyWith(
      items: state.items.map((n) => n.copyWith(isRead: true)).toList(),
      unreadCount: 0,
    );
    NotificationService().resetUnread();
  }
}

final notificationsProvider =
    StateNotifierProvider<NotificationsNotifier, NotificationsState>(
  (_) => NotificationsNotifier(),
);
