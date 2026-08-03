class AppNotificationData {
  final int id;
  final String title;
  final String body;
  final String notificationType;
  final int? summaryId;
  final int? courseId;
  final String? imageUrl;
  final DateTime createdAt;

  const AppNotificationData({
    required this.id,
    required this.title,
    required this.body,
    required this.notificationType,
    this.summaryId,
    this.courseId,
    this.imageUrl,
    required this.createdAt,
  });

  factory AppNotificationData.fromJson(Map<String, dynamic> json) {
    return AppNotificationData(
      id: json['id'] as int,
      title: json['title'] as String? ?? '',
      body: json['body'] as String? ?? '',
      notificationType: json['notification_type'] as String? ?? 'general',
      summaryId: json['summary_id'] as int?,
      courseId: json['course_id'] as int?,
      imageUrl: json['image_url'] as String?,
      createdAt: DateTime.tryParse(json['created_at'] as String? ?? '') ?? DateTime.now(),
    );
  }
}

class UserNotification {
  final int id;
  final AppNotificationData notification;
  final bool isRead;
  final DateTime? readAt;
  final DateTime createdAt;

  const UserNotification({
    required this.id,
    required this.notification,
    required this.isRead,
    this.readAt,
    required this.createdAt,
  });

  factory UserNotification.fromJson(Map<String, dynamic> json) {
    return UserNotification(
      id: json['id'] as int,
      notification: AppNotificationData.fromJson(json['notification'] as Map<String, dynamic>),
      isRead: json['is_read'] as bool? ?? false,
      readAt: json['read_at'] != null
          ? DateTime.tryParse(json['read_at'] as String)
          : null,
      createdAt: DateTime.tryParse(json['created_at'] as String? ?? '') ?? DateTime.now(),
    );
  }

  UserNotification copyWith({bool? isRead, DateTime? readAt}) {
    return UserNotification(
      id: id,
      notification: notification,
      isRead: isRead ?? this.isRead,
      readAt: readAt ?? this.readAt,
      createdAt: createdAt,
    );
  }
}

class NotificationsPage {
  final List<UserNotification> results;
  final int total;
  final int page;
  final int pageSize;
  final int totalPages;
  final int unreadCount;

  const NotificationsPage({
    required this.results,
    required this.total,
    required this.page,
    required this.pageSize,
    required this.totalPages,
    required this.unreadCount,
  });

  factory NotificationsPage.fromJson(Map<String, dynamic> json) {
    final list = (json['results'] as List<dynamic>? ?? [])
        .map((e) => UserNotification.fromJson(e as Map<String, dynamic>))
        .toList();
    return NotificationsPage(
      results: list,
      total: json['total'] as int? ?? 0,
      page: json['page'] as int? ?? 1,
      pageSize: json['page_size'] as int? ?? 20,
      totalPages: json['total_pages'] as int? ?? 1,
      unreadCount: json['unread_count'] as int? ?? 0,
    );
  }
}
