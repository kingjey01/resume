from rest_framework import serializers
from .models import UserDevice, AppNotification, UserNotification


class UserDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDevice
        fields = ['id', 'fcm_token', 'device_type', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class AppNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppNotification
        fields = [
            'id', 'title', 'body', 'notification_type',
            'target_universite', 'target_filiere', 'target_promotion',
            'summary_id', 'course_id', 'image_url', 'created_at',
        ]


class UserNotificationSerializer(serializers.ModelSerializer):
    notification = AppNotificationSerializer(read_only=True)

    class Meta:
        model = UserNotification
        fields = ['id', 'notification', 'is_read', 'read_at', 'delivered', 'created_at']
        read_only_fields = ['id', 'created_at']
