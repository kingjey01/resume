from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from .models import SecurityLog, AppVersion, ResumePricingConfig
from .serializers import (
    SecurityLogSerializer,
    CreateSecurityLogSerializer,
    AppVersionSerializer,
    ResumePricingSerializer,
)
from django.conf import settings


class SecurityLogListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['action_type']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']

    def get_queryset(self):
        user = self.request.user
        if user.profile.role == 'admin':
            return SecurityLog.objects.all()
        return SecurityLog.objects.filter(user=user)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateSecurityLogSerializer
        return SecurityLogSerializer


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def log_security_event(request):
    serializer = CreateSecurityLogSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def app_version_view(request):
    try:
        config = AppVersion.objects.filter(is_active=True).latest('created_at')
        serializer = AppVersionSerializer(config)
        data = serializer.data
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        if 'android' in user_agent or 'okhttp' in user_agent:
            data['platform'] = 'android'
            if data.get('android_latest_version'):
                data['latest_version'] = data['android_latest_version']
        elif 'iphone' in user_agent or 'ios' in user_agent:
            data['platform'] = 'ios'
            if data.get('ios_latest_version'):
                data['latest_version'] = data['ios_latest_version']
        else:
            data['platform'] = 'unknown'
        data.pop('android_latest_version', None)
        data.pop('ios_latest_version', None)
        return Response(data, status=status.HTTP_200_OK)
    except AppVersion.DoesNotExist:
        if settings.DEBUG:
            return Response({
                'latest_version': '1.0.0',
                'minimum_version': '1.0.0',
                'force_update': False,
                'maintenance_mode': False,
                'maintenance_message': '',
                'play_store_url': 'https://play.google.com/store/apps/details?id=com.resumeplus.app',
                'app_store_url': 'https://apps.apple.com/app/idXXXXXXXX',
                'mandatory_update_message': '',
                'platform': 'unknown',
            }, status=status.HTTP_200_OK)
        return Response({
            'latest_version': '1.0.0',
            'minimum_version': '1.0.0',
            'force_update': False,
            'maintenance_mode': False,
            'maintenance_message': '',
            'play_store_url': '',
            'app_store_url': '',
            'mandatory_update_message': '',
            'platform': 'unknown',
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def resume_pricing_config_view(request):
    """
    Endpoint public : retourne le prix minimum configuré.

    GET /api/resume-pricing-config/
    → {"minimum_resume_price": "3000.00"}

    Utilisé par Flutter pour la validation côté client.
    La validation finale est toujours faite côté backend.
    """
    try:
        config = ResumePricingConfig.objects.get(is_active=True)
        serializer = ResumePricingSerializer(config)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except ResumePricingConfig.DoesNotExist:
        # Aucune config → retourner la valeur par défaut (ne pas bloquer)
        return Response({
            'minimum_resume_price': '3000.00',
        }, status=status.HTTP_200_OK)
