import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:resume_plus_clean/models/app_notification.dart';
import 'package:resume_plus_clean/services/api_service.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';

class NotificationDetailScreen extends StatefulWidget {
  final int userNotificationId;

  const NotificationDetailScreen({super.key, required this.userNotificationId});

  @override
  State<NotificationDetailScreen> createState() => _NotificationDetailScreenState();
}

class _NotificationDetailScreenState extends State<NotificationDetailScreen> {
  final ApiService _api = ApiService();
  UserNotification? _notif;
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final data = await _api.getNotificationDetail(widget.userNotificationId);
      setState(() {
        _notif = UserNotification.fromJson(data);
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Impossible de charger la notification.';
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      backgroundColor: theme.scaffoldBackgroundColor,
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: AppTheme.primaryBlue))
          : _error != null
              ? _buildError(context)
              : _buildContent(context),
    );
  }

  Widget _buildError(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.error_outline_rounded, size: 48, color: AppTheme.error),
          const SizedBox(height: 16),
          Text(_error!, style: Theme.of(context).textTheme.bodyMedium),
          const SizedBox(height: 12),
          ElevatedButton.icon(
            onPressed: _load,
            icon: const Icon(Icons.refresh_rounded),
            label: const Text('Réessayer'),
          ),
        ],
      ),
    );
  }

  Widget _buildContent(BuildContext context) {
    final theme = Theme.of(context);
    final n = _notif!.notification;

    return CustomScrollView(
      slivers: [
        // Gradient app bar
        SliverAppBar(
          expandedHeight: 210,
          pinned: true,
          backgroundColor: AppTheme.primaryBlue,
          leading: GestureDetector(
            onTap: () => Navigator.pop(context),
            child: Container(
              margin: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.2),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.arrow_back_ios_new_rounded, color: Colors.white, size: 18),
            ),
          ),
          shape: const RoundedRectangleBorder(
            borderRadius: BorderRadius.only(
              bottomLeft: Radius.circular(24),
              bottomRight: Radius.circular(24),
            ),
          ),
          flexibleSpace: FlexibleSpaceBar(
            background: Container(
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
              child: SafeArea(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(20, 40, 20, 22),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.end,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.center,
                        children: [
                          Container(
                            width: 52,
                            height: 52,
                            decoration: BoxDecoration(
                              color: Colors.white.withOpacity(0.2),
                              shape: BoxShape.circle,
                            ),
                            child: Icon(
                              _typeIcon(n.notificationType),
                              color: Colors.white,
                              size: 26,
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                              decoration: BoxDecoration(
                                color: Colors.white.withOpacity(0.2),
                                borderRadius: BorderRadius.circular(20),
                              ),
                              child: Text(
                                _typeLabel(n.notificationType),
                                textAlign: TextAlign.center,
                                style: const TextStyle(
                                  color: Colors.white,
                                  fontSize: 11,
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 14),
                      Text(
                        n.title,
                        style: theme.textTheme.headlineSmall?.copyWith(
                          color: Colors.white,
                          fontWeight: FontWeight.w700,
                        ),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),

        SliverPadding(
          padding: const EdgeInsets.all(20),
          sliver: SliverList(
            delegate: SliverChildListDelegate([
              // Date chip
              Row(
                children: [
                  const Icon(Icons.access_time_rounded, size: 16, color: AppTheme.primaryBlue),
                  const SizedBox(width: 6),
                  Text(
                    DateFormat('dd MMMM yyyy à HH:mm', 'fr_FR').format(n.createdAt.toLocal()),
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.onSurface.withOpacity(0.6),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 20),

              // Body card
              Container(
                padding: const EdgeInsets.all(18),
                decoration: BoxDecoration(
                  color: theme.colorScheme.surface,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: theme.colorScheme.outline.withOpacity(0.15),
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(theme.brightness == Brightness.dark ? 0.2 : 0.05),
                      blurRadius: 10,
                      offset: const Offset(0, 4),
                    ),
                  ],
                ),
                child: Text(
                  n.body,
                  style: theme.textTheme.bodyLarge?.copyWith(
                    color: theme.colorScheme.onSurface,
                    height: 1.6,
                  ),
                ),
              ),

              // Action buttons
              if (n.summaryId != null || n.courseId != null) ...[
                const SizedBox(height: 24),
                _buildActionButtons(context, n),
              ],

              const SizedBox(height: 40),
            ]),
          ),
        ),
      ],
    );
  }

  Widget _buildActionButtons(BuildContext context, AppNotificationData n) {
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          'Actions',
          style: theme.textTheme.titleSmall?.copyWith(
            fontWeight: FontWeight.w700,
            color: theme.colorScheme.onSurface.withOpacity(0.6),
          ),
        ),
        const SizedBox(height: 12),
        if (n.summaryId != null)
          _ActionButton(
            icon: Icons.menu_book_rounded,
            label: 'Voir le résumé',
            color: AppTheme.primaryBlue,
            onTap: () => _navigateToSummary(context, n.summaryId!),
          ),
        if (n.courseId != null) ...[
          const SizedBox(height: 10),
          _ActionButton(
            icon: Icons.school_rounded,
            label: 'Voir le cours',
            color: const Color(0xFF8B5CF6),
            onTap: () => _navigateToCourse(context, n.courseId!),
          ),
        ],
      ],
    );
  }

  void _navigateToSummary(BuildContext context, int summaryId) {
    // Navigate to summary detail — go to Résumés tab and let user find it
    // If MainNavigationScreen is in the stack, switch tab; otherwise just pop
    Navigator.popUntil(context, (route) => route.isFirst);
    // Then navigate to main and switch to summaries tab
    Navigator.pushReplacementNamed(context, '/main');
  }

  void _navigateToCourse(BuildContext context, int courseId) {
    Navigator.popUntil(context, (route) => route.isFirst);
    Navigator.pushReplacementNamed(context, '/main');
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

  String _typeLabel(String type) {
    switch (type) {
      case 'summary_validated':
        return 'Résumé validé';
      case 'new_summary':
        return 'Nouveau résumé';
      case 'new_exercise':
        return 'Exercice';
      case 'payment':
        return 'Paiement';
      case 'system':
        return 'Système';
      case 'promo':
        return 'Promotion';
      default:
        return 'Notification';
    }
  }
}

class _ActionButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback onTap;

  const _ActionButton({
    required this.icon,
    required this.label,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: color.withOpacity(0.1),
      borderRadius: BorderRadius.circular(14),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(14),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
          child: Row(
            children: [
              Icon(icon, color: color, size: 22),
              const SizedBox(width: 12),
              Text(
                label,
                style: TextStyle(
                  color: color,
                  fontWeight: FontWeight.w600,
                  fontSize: 15,
                ),
              ),
              const Spacer(),
              Icon(Icons.arrow_forward_ios_rounded, color: color, size: 16),
            ],
          ),
        ),
      ),
    );
  }
}
