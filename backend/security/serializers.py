from rest_framework import serializers
from .models import SecurityLog, AppVersion, ResumePricingConfig


class SecurityLogSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = SecurityLog
        fields = ['id', 'user', 'user_username', 'action_type', 'description',
                  'ip_address', 'user_agent', 'timestamp']
        read_only_fields = ['user', 'timestamp']


class CreateSecurityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SecurityLog
        fields = ['action_type', 'description']

    def create(self, validated_data):
        request = self.context['request']
        validated_data['user'] = request.user
        validated_data['ip_address'] = self.get_client_ip(request)
        validated_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')
        return super().create(validated_data)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class AppVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppVersion
        fields = [
            'latest_version',
            'minimum_version',
            'force_update',
            'maintenance_mode',
            'maintenance_message',
            'play_store_url',
            'app_store_url',
            'android_latest_version',
            'ios_latest_version',
            'mandatory_update_message',
        ]


class ResumePricingSerializer(serializers.ModelSerializer):
    """Configuration du prix minimum des résumés — accessible sans auth."""

    class Meta:
        model = ResumePricingConfig
        fields = ['minimum_resume_price']
