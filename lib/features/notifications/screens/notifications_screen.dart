import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:resume_plus_clean/features/notifications/providers/notification_provider.dart';
import 'package:resume_plus_clean/features/notifications/screens/notification_detail_screen.dart';
import 'package:resume_plus_clean/models/app_notification.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';

class NotificationsScreen extends ConsumerStatefulWidget {
  const NotificationsScreen({super.key});

  @override
  ConsumerState<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends ConsumerState<NotificationsScreen> {
  final TextEditingController _searchController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  Timer? _debounce;

  static const _typeLabels = {
    '': 'Tout',
    'summary_validated': 'Résumés',
    'new_exercise': 'Exercices',
    'payment': 'Paiements',
    'system': 'Système',
    'general': 'Général',
  };

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(notificationsProvider.notifier).load(refresh: true);
    });
    _scrollController.addListener(_onScroll);
  }

  @override
  void dispose() {
    _searchController.dispose();
    _scrollController.dispose();
    _debounce?.cancel();
    super.dispose();
  }

  void _onScroll() {
    if (_scrollController.position.pixels >= _scrollController.position.maxScrollExtent - 200) {
      ref.read(notificationsProvider.notifier).loadMore();
    }
  }

  void _onSearchChanged(String q) {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 500), () {
      ref.read(notificationsProvider.notifier).setSearch(q);
    });
    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final state = ref.watch(notificationsProvider);
    final topPadding = MediaQuery.of(context).padding.top;

    return Scaffold(
      backgroundColor: theme.scaffoldBackgroundColor,
      body: Column(
        children: [
          _buildHeader(context, topPadding, state),
          _buildFilterChips(context, state),
          Expanded(child: _buildBody(context, theme, state)),
        ],
      ),
    );
  }

  Widget _buildHeader(BuildContext context, double topPadding, NotificationsState state) {
    final theme = Theme.of(context);
    return Container(
      height: 260 + topPadding,
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [AppTheme.primaryBlueDark, AppTheme.primaryBlue, AppTheme.primaryBlueLight],
        ),
        borderRadius: BorderRadius.only(
          bottomLeft: Radius.circular(24),
          bottomRight: Radius.circular(24),
        ),
      ),
      child: Stack(
        children: [
          Positioned(
            left: 0,
            right: 0,
            bottom: 0,
            child: Container(
              height: 82,
              decoration: BoxDecoration(
                color: Theme.of(context).scaffoldBackgroundColor,
                borderRadius: const BorderRadius.only(
                  topLeft: Radius.circular(60),
                  topRight: Radius.circular(60),
                ),
              ),
            ),
          ),
          Padding(
            padding: EdgeInsets.only(top: topPadding + 16, left: 20, right: 20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    GestureDetector(
                      onTap: () => Navigator.pop(context),
                      child: Container(
                        width: 42,
                        height: 42,
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.2),
                          shape: BoxShape.circle,
                        ),
                        child: const Icon(Icons.arrow_back_ios_new_rounded, color: Colors.white, size: 18),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        'Notifications',
                        style: theme.textTheme.headlineMedium?.copyWith(
                          color: Colors.white,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                    if (state.unreadCount > 0)
                      TextButton.icon(
                        onPressed: () => ref.read(notificationsProvider.notifier).markAllRead(),
                        icon: const Icon(Icons.done_all_rounded, color: Colors.white70, size: 18),
                        label: Text(
                          'Tout lire',
                          style: theme.textTheme.bodySmall?.copyWith(color: Colors.white70),
                        ),
                      ),
                  ],
                ),
                const SizedBox(height: 14),
                Container(
                  height: 46,
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(23),
                  ),
                  child: TextField(
                    controller: _searchController,
                    onChanged: _onSearchChanged,
                    style: const TextStyle(color: Colors.white, fontSize: 14),
                    decoration: InputDecoration(
                      hintText: 'Rechercher une notification...',
                      hintStyle: TextStyle(color: Colors.white.withOpacity(0.7), fontSize: 14),
                      prefixIcon: Icon(Icons.search_rounded, color: Colors.white.withOpacity(0.8), size: 20),
                      suffixIcon: _searchController.text.isNotEmpty
                          ? IconButton(
                              icon: Icon(Icons.close_rounded, color: Colors.white.withOpacity(0.8), size: 18),
                              onPressed: () {
                                _searchController.clear();
                                ref.read(notificationsProvider.notifier).setSearch('');
                                setState(() {});
                              },
                            )
                          : null,
                      border: InputBorder.none,
                      enabledBorder: InputBorder.none,
                      focusedBorder: InputBorder.none,
                      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                      filled: false,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFilterChips(BuildContext context, NotificationsState state) {
    final theme = Theme.of(context);
    return Container(
      height: 56,
      color: theme.colorScheme.surface,
      child: ListView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        children: [
          // Unread-only toggle
          Padding(
            padding: const EdgeInsets.only(right: 8),
            child: FilterChip(
              label: const Text('Non lues'),
              selected: state.unreadOnly,
              onSelected: (_) => ref.read(notificationsProvider.notifier).toggleUnreadOnly(),
              selectedColor: AppTheme.primaryBlue.withOpacity(0.15),
              checkmarkColor: AppTheme.primaryBlue,
              labelStyle: TextStyle(
                color: state.unreadOnly ? AppTheme.primaryBlue : theme.colorScheme.onSurface,
                fontSize: 12,
                fontWeight: state.unreadOnly ? FontWeight.w600 : FontWeight.normal,
              ),
            ),
          ),
          // Type filters
          ..._typeLabels.entries.map((entry) {
            final selected = state.typeFilter == entry.key;
            return Padding(
              padding: const EdgeInsets.only(right: 8),
              child: FilterChip(
                label: Text(entry.value),
                selected: selected,
                onSelected: (_) =>
                    ref.read(notificationsProvider.notifier).setTypeFilter(entry.key),
                selectedColor: AppTheme.primaryBlue.withOpacity(0.15),
                checkmarkColor: AppTheme.primaryBlue,
                labelStyle: TextStyle(
                  color: selected ? AppTheme.primaryBlue : theme.colorScheme.onSurface,
                  fontSize: 12,
                  fontWeight: selected ? FontWeight.w600 : FontWeight.normal,
                ),
              ),
            );
          }),
        ],
      ),
    );
  }

  Widget _buildBody(BuildContext context, ThemeData theme, NotificationsState state) {
    if (state.isLoading) {
      return const Center(child: CircularProgressIndicator(color: AppTheme.primaryBlue));
    }

    if (state.error != null && state.items.isEmpty) {
      return _buildError(context, state.error!);
    }

    if (state.items.isEmpty) {
      return _buildEmpty(context);
    }

    return RefreshIndicator(
      color: AppTheme.primaryBlue,
      onRefresh: () => ref.read(notificationsProvider.notifier).refresh(),
      child: ListView.builder(
        controller: _scrollController,
        padding: const EdgeInsets.fromLTRB(0, 8, 0, 8),
        itemCount: state.items.length + (state.isLoadingMore ? 1 : 0),
        itemBuilder: (context, index) {
          if (index == state.items.length) {
            return const Padding(
              padding: EdgeInsets.all(16),
              child: Center(child: CircularProgressIndicator(color: AppTheme.primaryBlue)),
            );
          }
          return _NotificationTile(
            notif: state.items[index],
            onTap: () => _openDetail(state.items[index]),
          );
        },
      ),
    );
  }

  void _openDetail(UserNotification notif) {
    if (!notif.isRead) {
      ref.read(notificationsProvider.notifier).markRead(notif.id);
    }
    Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => NotificationDetailScreen(userNotificationId: notif.id)),
    );
  }

  Widget _buildEmpty(BuildContext context) {
    final theme = Theme.of(context);
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(40),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 90,
              height: 90,
              decoration: BoxDecoration(
                color: AppTheme.primaryBlue.withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.notifications_none_rounded, size: 44, color: AppTheme.primaryBlue),
            ),
            const SizedBox(height: 20),
            Text(
              'Aucune notification',
              style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 8),
            Text(
              'Vous serez notifié dès qu\'un nouveau résumé est disponible.',
              textAlign: TextAlign.center,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.onSurface.withOpacity(0.6),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildError(BuildContext context, String error) {
    final theme = Theme.of(context);
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(40),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline_rounded, size: 48, color: AppTheme.error),
            const SizedBox(height: 16),
            Text(error, textAlign: TextAlign.center, style: theme.textTheme.bodyMedium),
            const SizedBox(height: 12),
            ElevatedButton.icon(
              onPressed: () => ref.read(notificationsProvider.notifier).refresh(),
              icon: const Icon(Icons.refresh_rounded),
              label: const Text('Réessayer'),
            ),
          ],
        ),
      ),
    );
  }
}

// ─── Notification tile ────────────────────────────────────────────────────────

class _NotificationTile extends StatelessWidget {
  final UserNotification notif;
  final VoidCallback onTap;

  const _NotificationTile({required this.notif, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isUnread = !notif.isRead;
    final n = notif.notification;

    return InkWell(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        color: isUnread
            ? AppTheme.primaryBlue.withOpacity(theme.brightness == Brightness.dark ? 0.08 : 0.04)
            : Colors.transparent,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Icon container
            Container(
              width: 46,
              height: 46,
              decoration: BoxDecoration(
                color: _typeColor(n.notificationType).withOpacity(0.12),
                shape: BoxShape.circle,
              ),
              child: Icon(
                _typeIcon(n.notificationType),
                color: _typeColor(n.notificationType),
                size: 22,
              ),
            ),
            const SizedBox(width: 12),
            // Content
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          n.title,
                          style: theme.textTheme.bodyMedium?.copyWith(
                            fontWeight: isUnread ? FontWeight.w700 : FontWeight.w500,
                            color: theme.colorScheme.onSurface,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        _formatDate(notif.createdAt),
                        style: theme.textTheme.bodySmall?.copyWith(
                          color: theme.colorScheme.onSurface.withOpacity(0.5),
                          fontSize: 11,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    n.body,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.onSurface.withOpacity(isUnread ? 0.75 : 0.55),
                    ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ),
            if (isUnread)
              Padding(
                padding: const EdgeInsets.only(left: 8, top: 4),
                child: Container(
                  width: 8,
                  height: 8,
                  decoration: const BoxDecoration(
                    color: AppTheme.primaryBlue,
                    shape: BoxShape.circle,
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  String _formatDate(DateTime dt) {
    final now = DateTime.now();
    final diff = now.difference(dt);
    if (diff.inMinutes < 1) return 'À l\'instant';
    if (diff.inHours < 1) return '${diff.inMinutes}min';
    if (diff.inHours < 24) return '${diff.inHours}h';
    if (diff.inDays < 7) return '${diff.inDays}j';
    return DateFormat('dd/MM').format(dt);
  }

  IconData _typeIcon(String type) {
    switch (type) {
      case 'summary_validated':
      case 'new_summary':
        return Icons.menu_book_rounded;
      case 'new_exercise':
        return Icons.quiz_rounded;
      case 'payment':
        return Icons.payment_rounded;
      case 'system':
        return Icons.info_outline_rounded;
      case 'promo':
        return Icons.local_offer_rounded;
      default:
        return Icons.notifications_rounded;
    }
  }

  Color _typeColor(String type) {
    switch (type) {
      case 'summary_validated':
      case 'new_summary':
        return AppTheme.primaryBlue;
      case 'new_exercise':
        return const Color(0xFF8B5CF6);
      case 'payment':
        return const Color(0xFF10B981);
      case 'system':
        return const Color(0xFFF59E0B);
      case 'promo':
        return const Color(0xFFEF4444);
      default:
        return AppTheme.primaryBlue;
    }
  }
}
