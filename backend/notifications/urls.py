from django.urls import path
from . import views

urlpatterns = [
    # Device registration
    path('devices/register/', views.register_device, name='register-device'),
    path('devices/unregister/', views.unregister_device, name='unregister-device'),

    # Admin: Create manual notifications
    path('admin/create/', views.create_manual_notification, name='create-manual-notification'),

    # Notification list & counts
    path('', views.list_notifications, name='list-notifications'),
    path('unread-count/', views.unread_count, name='unread-count'),

    # Mark read
    path('<int:user_notification_id>/read/', views.mark_read, name='mark-read'),
    path('mark-all-read/', views.mark_all_read, name='mark-all-read'),

    # Detail (also marks as read)
    path('<int:user_notification_id>/', views.notification_detail, name='notification-detail'),
]
