import logging
from django.utils import timezone
from django.db.models import Q
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import UserDevice, AppNotification, UserNotification
from .serializers import UserDeviceSerializer, UserNotificationSerializer

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
#  FCM Device Management
# ─────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def register_device(request):
    """
    Register or refresh an FCM token for the current user's device.
    Body: { "fcm_token": "...", "device_type": "android|ios|web" }
    
    Important: Si le token existe déjà mais associé à un autre user,
    il est RÉASSIGNÉ au user actuel (changement de compte sur le même device).
    """
    fcm_token = request.data.get('fcm_token', '').strip()
    device_type = request.data.get('device_type', 'android')
    user = request.user
    
    # Token suffix for logs (last 10 chars)
    token_suffix = fcm_token[-10:] if len(fcm_token) >= 10 else fcm_token
    
    logger.info(f"📲 [FCM Register] user={user.id}({user.username}) token=...{token_suffix} type={device_type}")

    if not fcm_token:
        logger.warning(f"⚠️ [FCM Register] fcm_token vide — user={user.id}")
        return Response({'error': 'fcm_token requis'}, status=status.HTTP_400_BAD_REQUEST)

    # Vérifier s'il existe déjà pour un autre user
    existing = UserDevice.objects.filter(fcm_token=fcm_token).first()
    if existing and existing.user_id != user.id:
        logger.warning(
            f"🔄 [FCM Register] Token réassigné: ancien_user={existing.user_id}({existing.user.username}) → "
            f"nouveau_user={user.id}({user.username})"
        )
    
    # update_or_create avec fcm_token comme clé unique
    # → si le token existe (même user ou autre), il est mis à jour avec le user actuel
    device, created = UserDevice.objects.update_or_create(
        fcm_token=fcm_token,
        defaults={
            'user': user,
            'device_type': device_type,
            'is_active': True,
        }
    )

    action = '📱 Créé' if created else '🔄 Mis à jour'
    logger.info(
        f"✅ [FCM Register] {action} — device_id={device.id} user={user.id}({user.username}) "
        f"token=...{token_suffix}"
    )
    
    # Stats : combien de devices actifs pour ce user
    active_count = UserDevice.objects.filter(user=user, is_active=True).count()
    logger.info(f"📊 [FCM Register] {user.username} a maintenant {active_count} device(s) actif(s)")
    
    return Response(
        UserDeviceSerializer(device).data,
        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
    )


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def unregister_device(request):
    """
    Mark an FCM token as inactive (e.g. on logout).
    Body: { "fcm_token": "..." }
    """
    fcm_token = request.data.get('fcm_token', '').strip()
    user = request.user
    token_suffix = fcm_token[-10:] if len(fcm_token) >= 10 else fcm_token
    
    logger.info(f"📲 [FCM Unregister] user={user.id}({user.username}) token=...{token_suffix}")
    
    if not fcm_token:
        return Response({'error': 'fcm_token requis'}, status=status.HTTP_400_BAD_REQUEST)

    updated = UserDevice.objects.filter(user=user, fcm_token=fcm_token).update(is_active=False)
    
    if updated > 0:
        logger.info(f"✅ [FCM Unregister] {updated} device(s) désactivé(s) pour {user.username}")
    else:
        logger.warning(f"⚠️ [FCM Unregister] Aucun device trouvé pour {user.username} avec ce token")
    
    return Response({'deactivated': updated > 0})


# ─────────────────────────────────────────────
#  Notification Listing & Unread Count
# ─────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def list_notifications(request):
    """
    Returns paginated notifications for the authenticated user.
    Query params:
      - page (int, default 1)
      - page_size (int, default 20, max 50)
      - search (str)
      - type (str, notification_type filter)
      - unread_only (bool)
    """
    page = max(1, int(request.query_params.get('page', 1)))
    page_size = min(50, max(1, int(request.query_params.get('page_size', 20))))
    search = request.query_params.get('search', '').strip()
    notif_type = request.query_params.get('type', '').strip()
    unread_only = request.query_params.get('unread_only', '').lower() in ('true', '1')

    qs = UserNotification.objects.filter(user=request.user).select_related(
        'notification',
        'notification__target_universite',
        'notification__target_filiere',
        'notification__target_promotion',
    ).order_by('-created_at')

    if unread_only:
        qs = qs.filter(is_read=False)

    if search:
        qs = qs.filter(
            Q(notification__title__icontains=search) |
            Q(notification__body__icontains=search)
        )

    if notif_type:
        qs = qs.filter(notification__notification_type=notif_type)

    total = qs.count()
    start = (page - 1) * page_size
    notifications_page = qs[start: start + page_size]

    serializer = UserNotificationSerializer(notifications_page, many=True)
    return Response({
        'results': serializer.data,
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': (total + page_size - 1) // page_size,
        'unread_count': UserNotification.objects.filter(user=request.user, is_read=False).count(),
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def unread_count(request):
    """Returns the current unread notification count for the user."""
    count = UserNotification.objects.filter(user=request.user, is_read=False).count()
    return Response({'unread_count': count})


# ─────────────────────────────────────────────
#  Mark Read
# ─────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_read(request, user_notification_id):
    """Mark a single UserNotification as read."""
    try:
        un = UserNotification.objects.get(id=user_notification_id, user=request.user)
        if not un.is_read:
            un.is_read = True
            un.read_at = timezone.now()
            un.save(update_fields=['is_read', 'read_at'])
        return Response({'id': un.id, 'is_read': True})
    except UserNotification.DoesNotExist:
        return Response({'error': 'Notification introuvable'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_all_read(request):
    """Mark all unread notifications for the user as read."""
    updated = UserNotification.objects.filter(
        user=request.user, is_read=False
    ).update(is_read=True, read_at=timezone.now())
    return Response({'marked_read': updated})


# ─────────────────────────────────────────────
#  Admin: Create & Send Manual Notifications
# ─────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_manual_notification(request):
    """
    Admin endpoint to create and send a notification manually.
    
    Body:
    {
        "title": "...",
        "body": "...",
        "notification_type": "general|promo|system|...",
        "universite_id": null (optional, null = all),
        "filiere_id": null (optional, requires universite_id),
        "promotion_id": null (optional, requires universite_id + filiere_id),
        "image_url": "..." (optional)
    }
    
    Targeting logic:
    - No filters → all users
    - universite_id only → all users in that universite
    - universite_id + filiere_id → all users in that universite + filiere
    - universite_id + filiere_id + promotion_id → exact group
    """
    # Check admin/superuser permission
    if not (request.user.is_staff or request.user.is_superuser):
        return Response(
            {'error': 'Permission refusée. Seuls les administrateurs peuvent créer des notifications.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        from .tasks import create_and_send_notification
        
        title = request.data.get('title', '').strip()
        body = request.data.get('body', '').strip()
        notification_type = request.data.get('notification_type', 'general')
        universite_id = request.data.get('universite_id')
        filiere_id = request.data.get('filiere_id')
        promotion_id = request.data.get('promotion_id')
        image_url = request.data.get('image_url', '').strip() or None
        
        if not title or not body:
            return Response(
                {'error': 'title et body sont requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate targeting hierarchy
        if filiere_id and not universite_id:
            return Response(
                {'error': 'filiere_id requiert universite_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if promotion_id and not (universite_id and filiere_id):
            return Response(
                {'error': 'promotion_id requiert universite_id et filiere_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Schedule the notification task
        task = create_and_send_notification.apply_async(
            kwargs={
                'title': title,
                'body': body,
                'notification_type': notification_type,
                'universite_id': universite_id,
                'filiere_id': filiere_id,
                'promotion_id': promotion_id,
                'sender_id': request.user.id,
                'image_url': image_url,
            },
            countdown=2
        )
        
        logger.info(f"📢 [Admin] Notification manuelle créée par {request.user.username} — task_id={task.id}")
        
        return Response({
            'message': 'Notification créée et envoi planifié',
            'task_id': task.id,
            'targeting': {
                'universite_id': universite_id,
                'filiere_id': filiere_id,
                'promotion_id': promotion_id,
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f'❌ [Admin] Erreur création notification: {e}')
        return Response(
            {'error': 'Erreur lors de la création de la notification'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def notification_detail(request, user_notification_id):
    """Get a single notification and auto-mark it as read."""
    try:
        un = UserNotification.objects.select_related(
            'notification',
            'notification__target_universite',
            'notification__target_filiere',
            'notification__target_promotion',
        ).get(id=user_notification_id, user=request.user)

        if not un.is_read:
            un.is_read = True
            un.read_at = timezone.now()
            un.save(update_fields=['is_read', 'read_at'])

        return Response(UserNotificationSerializer(un).data)
    except UserNotification.DoesNotExist:
        return Response({'error': 'Notification introuvable'}, status=status.HTTP_404_NOT_FOUND)
